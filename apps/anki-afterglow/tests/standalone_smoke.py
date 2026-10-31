import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen,Request
from urllib.error import HTTPError

root=Path(__file__).parents[1]
process=subprocess.Popen([sys.executable,str(root/'standalone.py'),'--no-browser'],stdout=subprocess.PIPE,text=True)
try:
    url=process.stdout.readline().strip()
    assert url.startswith('http://127.0.0.1:')
    assert b'STANDALONE' in urlopen(url).read()
    time.sleep(.5)
    state=json.load(urlopen(url+'state'))
    assert len(state['particle_phases'])==8
    for path in ('web/particles.js','web/liquid.js','web/club.js','web/waves.js','web/afterglow.js','web/afterglow.css'):
        assert urlopen(url+path).status==200
    try:urlopen(url+'../config.json')
    except HTTPError as e:assert e.code==404
    else:raise AssertionError('Server exposed non-preview files')
    urlopen(Request(url+'stop',method='POST')).read()
    assert process.wait(timeout=5)==0
    print('PASS: standalone loopback service, shared motion, assets, file isolation and clean shutdown')
finally:
    if process.poll() is None:process.terminate();process.wait(timeout=3)
