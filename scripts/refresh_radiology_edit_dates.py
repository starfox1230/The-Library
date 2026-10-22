#!/usr/bin/env python3
"""Refresh per-resource GitHub edit dates; optionally merge verified Sites metrics.

Uses the authenticated gh CLI. No credentials are read or written by this script.
Sites metrics must come from the commit referenced by the latest saved Site version.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'apps/radiology-library/catalog.json'


def github(endpoint, **fields):
    command = ['gh', 'api', '--method', 'GET', endpoint]
    for key, value in fields.items():
        command += ['-f', f'{key}={value}']
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def target(item):
    url = urlparse(item['source'])
    if url.hostname != 'github.com':
        return None
    parts = unquote(url.path).strip('/').split('/')
    if len(parts) < 2:
        return None
    repo = '/'.join(parts[:2])
    path = '/'.join(parts[4:]) if len(parts) > 4 and parts[2] == 'blob' else ''
    # A page's folder includes its scripts, styles, banks and assets. Standalone
    # HTML modules use file history so sibling module edits do not change their dates.
    if path and Path(path).name in ['index.html', 'README.md']:
        path = str(Path(path).parent)
        if path == '.':
            path = ''
    return repo, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sites-file', type=Path, help='Verified, credential-free Site metrics keyed by resource URL')
    args = parser.parse_args()
    data = json.loads(CATALOG.read_text())
    checked = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    site_metrics = json.loads(args.sites_file.read_text()) if args.sites_file else {}
    targets = {item['id']: target(item) for item in data['items']}
    repositories = sorted({value[0] for value in targets.values() if value})
    # Pin each repository once so simultaneous edits cannot produce a mixed snapshot.
    def head(repo):
        return repo, github(f'repos/{repo}/commits', per_page=1)[0]
    with ThreadPoolExecutor(max_workers=5) as pool:
        heads = dict(pool.map(head, repositories))
    unique_targets = sorted({value for value in targets.values() if value})

    def metric(value):
        repo, path = value
        head_commit = heads[repo]
        changes = github(f'repos/{repo}/commits', sha=head_commit['sha'], path=path, per_page=1) if path else [head_commit]
        if not changes:
            return value, {'at': None, 'metric': 'unknown', 'label': 'No matching commit history', 'checkedAt': checked}
        commit = changes[0]
        file_scope = bool(path and Path(path).suffix.lower() == '.html')
        return value, {
            'at': commit['commit']['committer']['date'],
            'metric': 'github-file' if file_scope else 'github-folder' if path else 'github-repository',
            'label': 'GitHub file commit' if file_scope else 'GitHub resource folder commit' if path else 'GitHub repository commit',
            'repository': repo, 'path': path, 'commitSha': commit['sha'],
            'url': commit['html_url'], 'snapshotSha': head_commit['sha'], 'checkedAt': checked,
        }

    with ThreadPoolExecutor(max_workers=5) as pool:
        metrics = dict(pool.map(metric, unique_targets))
    for item in data['items']:
        if targets[item['id']]:
            item['lastEdited'] = metrics[targets[item['id']]]
        elif item['url'] in site_metrics:
            item['lastEdited'] = site_metrics[item['url']]
        elif not item.get('lastEdited'):
            item['lastEdited'] = {'at': None, 'metric': 'unknown', 'label': 'Edit date not verified', 'checkedAt': checked}
    counts = Counter(item['lastEdited']['metric'] for item in data['items'])
    data['audit']['editDates'] = {
        'checkedAt': checked, 'known': sum(bool(x['lastEdited']['at']) for x in data['items']),
        'total': len(data['items']), 'metrics': dict(counts),
        'method': 'GitHub dates use committer timestamps from the newest commit touching each resource folder (including scripts, banks, styles and assets), an individual standalone HTML file, or the whole repository for repository-level entries. Sites dates use the source commit referenced by the latest saved version. These are recorded source edits, not local file modification times, study activity, or the catalog entry date.',
        'limits': 'Folder/repository metrics can include content imports, generated assets, progress files, moves or maintenance. Group launchers include descendant edits. Alternate links retain the primary resource date. Unsaved local changes and live database edits are outside this metric. Dates are a refreshable snapshot; unknown dates sort last.',
    }
    # Write only after all queries succeed; a failed refresh preserves the catalog.
    temp = CATALOG.with_suffix('.json.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(CATALOG)
    print(f"Edit dates verified: {data['audit']['editDates']['known']}/{len(data['items'])}; metrics: {dict(counts)}")


if __name__ == '__main__':
    main()
