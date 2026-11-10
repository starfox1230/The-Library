#!/usr/bin/env python3
"""Stage the web Library below Pages' 1 GB limit; keep source downloads on GitHub."""
import argparse
import html
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BINARY_SOURCE = {'.apkg', '.ankiaddon', '.pyc', '.exe', '.pyd', '.dll', '.db', '.sqlite3', '.db-wal', '.db-shm'}
IMAGES = {'.png', '.jpg', '.jpeg', '.gif'}
WEB = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.svg', '.webp'}
TEXT = {'.html', '.css', '.js', '.json', '.md', '.svg', '.webmanifest'}

def excluded(name):
    p = PurePosixPath(name)
    if any(part.startswith('.') or part in {'__pycache__', 'node_modules', 'tmp', 'exports'} for part in p.parts):
        return True
    if p.suffix.lower() in BINARY_SOURCE:
        return True
    if 'tests' in p.parts and p.suffix.lower() not in {'.html', '.css', '.js', '.json', '.svg'}:
        return True
    if name.startswith('apps/anki-companion-game/') and p.suffix.lower() not in WEB:
        return True
    if name.startswith('apps/anki-card-creation-codex-helper/') and p.suffix.lower() in IMAGES:
        return True
    if name.startswith('apps/temporary-apps/library/2026-06-09-manual-audio-player/') and p.suffix.lower() == '.mp3':
        return True
    if str(p.parent) == 'apps/Radionuclides' and p.suffix.lower() in IMAGES:
        return True
    return False

def rewrite(text, name, omitted, revision):
    def target(value):
        decoded = html.unescape(value)
        parts = urlsplit(decoded)
        if parts.scheme or parts.netloc or not parts.path or any(x in decoded for x in ['${', '\\', '<', '\n']):
            return value
        path = unquote(parts.path)
        if path.startswith('/The-Library/'):
            path = path[len('/The-Library/'):]
        elif path.startswith('/'):
            return value
        else:
            path = posixpath.normpath(posixpath.join(posixpath.dirname(name), path))
        if path not in omitted:
            return value
        return f'https://raw.githubusercontent.com/starfox1230/The-Library/{revision}/{quote(path, safe="/")}' + (('?' + parts.query) if parts.query else '') + (('#' + parts.fragment) if parts.fragment else '')
    def quoted(m):
        try:
            return m[1] + target(m[2]) + m[1]
        except ValueError:
            return m[0]
    text = re.sub(r'''(["'`])([^"'`]*?)\1''', quoted, text)
    return re.sub(r'url\(([^\s\'"()]+)\)', lambda m: 'url(' + target(m[1]) + ')', text)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        raise SystemExit('Output must be a separate staging directory')
    if output.exists():
        raise SystemExit('Output directory already exists; choose an empty staging path')
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).decode().split('\0')
    # Gitlinks are unpopulated submodules in the normal Actions checkout.
    names = [entry.split('\t', 1)[1] for entry in entries if entry and not entry.startswith('160000 ')]
    omitted = {n for n in names if excluded(n)}
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output.mkdir(parents=True)
    size = 0
    for name in names:
        if name in omitted:
            continue
        src, dest = ROOT / name, output / name
        if not src.is_file():
            raise SystemExit(f'Missing tracked web file: {name}. Use a full checkout.')
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in TEXT:
            try:
                dest.write_text(rewrite(src.read_text(), name, omitted, revision))
            except UnicodeDecodeError:
                shutil.copyfile(src, dest)
        else:
            shutil.copyfile(src, dest)
        size += dest.stat().st_size
    # Preserve the .nojekyll marker despite excluding other hidden source files.
    (output / '.nojekyll').touch()
    if size > 950_000_000:
        raise SystemExit(f'Pages package is {size:,} bytes; exceeds the 950 MB budget.')
    required = ['index.html', 'apps/study-reward-timer/index.html', 'apps/study-reward-timer/alerts.js', 'apps/study-reward-timer/alarm.wav']
    for name in required:
        if not (output / name).is_file():
            raise SystemExit(f'Missing required page asset: {name}')
    print(json.dumps({'bytes': size, 'files': len(names) - len(omitted), 'repository_assets': len(omitted), 'revision': revision}))

if __name__ == '__main__':
    main()
