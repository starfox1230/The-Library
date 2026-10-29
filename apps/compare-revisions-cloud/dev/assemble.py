"""Embed the authoring template so Cloud Run still needs only two files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'main.py'
template = (ROOT / 'dev/review-template.html').read_text(encoding='utf-8')
assert "'''" not in template
source = main.read_text(encoding='utf-8').split('# === UI TEMPLATE ===')[0]
main.write_text(source + "# === UI TEMPLATE ===\nTEMPLATE = r'''" + template + "'''\n", encoding='utf-8')
compile(main.read_text(encoding='utf-8'), str(main), 'exec')
print('main.py assembled and Python syntax checked.')
