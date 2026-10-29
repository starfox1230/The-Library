"""Embed the authoring template so Cloud Run still needs only two files."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'main.py'
template = (ROOT / 'dev/review-template.html').read_text(encoding='utf-8')
assert "'''" not in template
source = main.read_text(encoding='utf-8').split('# === UI TEMPLATE ===')[0]
main.write_text(source + "# === UI TEMPLATE ===\nTEMPLATE = r'''" + template + "'''\n", encoding='utf-8')
compile(main.read_text(encoding='utf-8'), str(main), 'exec')
# Export the exact default without importing authentication or the API client.
tree = ast.parse(source)
prompt = next(ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'DEFAULT_PROMPT'
                      for target in node.targets))
(ROOT / 'ANALYSIS_PROMPT.md').write_text(prompt, encoding='utf-8')
title_rules = {target.id: ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign) for target in node.targets
               if isinstance(target, ast.Name) and target.id in ('RESIDENT_TITLE_RULE', 'ATTENDING_TITLE_RULE')}
assert prompt.count(title_rules['RESIDENT_TITLE_RULE']) == 1
attending = prompt.replace(title_rules['RESIDENT_TITLE_RULE'], title_rules['ATTENDING_TITLE_RULE'], 1)
(ROOT / 'ATTENDING_ANALYSIS_PROMPT.md').write_text(attending, encoding='utf-8')
print('main.py assembled, syntax checked, and both exact default prompts exported.')
