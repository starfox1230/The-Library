#!/usr/bin/env python3
"""Build the link directory's browser data and readable inventory from catalog.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'apps' / 'radiology-library'
data = json.loads((DIRECTORY / 'catalog.json').read_text())
items = data['items']
ids = [x['id'] for x in items]
assert len(ids) == len(set(ids)), 'Duplicate resource IDs'
assert len({x['url'] for x in items}) == len(items), 'Duplicate primary links'
for item in items:
    assert item['title'] and item['scope'] and item['subjects'] and item['types']
    assert all(t in data['types'] for t in item['types'])
    assert item['url'].startswith('https://') and item['source'].startswith('https://')
    for alias in item['related']:
        assert alias['url'].startswith('https://')
(DIRECTORY / 'catalog.js').write_text('window.RADIOLOGY_CATALOG = ' + json.dumps(data, ensure_ascii=False) + ';\n')
lines = ['# Radiology linked inventory', '', f"Snapshot: {data['updated']}. {len(items)} unique linked resources. Individual chapters and modules count as resources.", '', 'This is a directory of existing creations. Each link opens the original resource.', '', '## Particularly helpful', '']
for item in items:
    if item['recommendation']:
        lines += [f"- [{item['title']}]({item['url']}): {item['recommendation']}"]
lines += ['', '## Subject-teaching range', '']
for subject in sorted({s for i in items if i['teaches'] for s in i['subjects']}):
    lines += [f'### {subject}', '']
    for item in items:
        if item['teaches'] and subject in item['subjects']:
            lines += [f"- [{item['title']}]({item['url']}): {item['scope']}"]
            if item.get('coverage'):
                lines += ['  - Topic range: ' + '; '.join(item['coverage']) + '.']
    lines += ['']
lines += ['## Complete inventory by type', '']
for category in data['types']:
    lines += ['### ' + category, '']
    for item in sorted(items, key=lambda x: x['title'].lower()):
        if category not in item['types']:
            continue
        lines += [f"- [{item['title']}]({item['url']}) — {item['scope']} ({item['status']})"]
        for alias in item['related']:
            lines += [f"  - [{alias['label']}]({alias['url']})"]
    lines += ['']
lines += ['## Inventory limits', '', data['audit']['method'], '', data['audit']['limits'], '', data['audit']['duplicates'], '']
(DIRECTORY / 'INVENTORY.md').write_text('\n'.join(lines))
print(f"Validated and built {len(items)} links; {sum(x['teaches'] for x in items)} teaching resources; {sum(bool(x['recommendation']) for x in items)} suggested starting points.")
