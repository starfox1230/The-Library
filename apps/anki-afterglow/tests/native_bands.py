"""Exercises the same filter bank used by WASAPI with silent offline test tones."""
import json
from pathlib import Path
import subprocess
helper=Path(__file__).parents[1]/'loopback.exe'
rows=[json.loads(line) for line in subprocess.check_output([str(helper),'--test-bands'],text=True,timeout=5).splitlines()]
assert len(rows)==3 and all(len(row['bands'])==8 for row in rows)
assert rows[0]['bands'][0]>max(rows[0]['bands'][4:])*5
assert max(rows[2]['bands'][5:])>rows[2]['bands'][0]*5
assert max(rows[1]['bands'][2:5])>rows[1]['bands'][7]*3
print('PASS: native filter bank separates low, mid and high offline tones; no sound played')
