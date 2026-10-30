"""Read-only 8 second signal check. Prints aggregate numeric features, not audio."""
import importlib
import sys
import time
import types
from pathlib import Path
pkg = types.ModuleType('afterglow_probe')
pkg.__path__ = [str(Path(__file__).parents[1])]
sys.modules[pkg.__name__] = pkg
AudioListener = importlib.import_module(pkg.__name__ + '.audio').AudioListener
listener = AudioListener()
listener.start()
samples=[]
try:
    for _ in range(80):
        time.sleep(.1)
        samples.append(listener.snapshot(35))
finally:
    listener.stop()
heard=[x for x in samples if x.get('energy',0)>.00003]
print('Output names:', sorted(set(x.get('device','unknown') for x in samples)))
print('Audible snapshots:',len(heard),'/',len(samples))
print('Energy range:',min(x['energy'] for x in samples),max(x['energy'] for x in samples))
print('Detected attacks:',max(x.get('hit_id',0) for x in samples))
print('Locked BPM snapshots:',[x['bpm'] for x in samples if x.get('bpm')][-8:])
assert heard, 'No audible stream found; leave music playing for this probe.'
assert max(x['energy'] for x in samples)>min(x['energy'] for x in samples), 'Signal is not changing'
print('PASS: automatic output selection receives changing real system audio')
