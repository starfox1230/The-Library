"""Run with Anki's own Python; uses a separate offscreen window, no collection."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import importlib.util
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import aqt
from aqt.qt import QApplication, QMainWindow, QMenu, QTimer, QWidget
import json
import tempfile

app = QApplication([])
window = QMainWindow()
config = {}
window.addonManager = SimpleNamespace(
    addonFromModule=lambda name: 'anki_afterglow', getConfig=lambda name: config,
    setConfigAction=lambda *a: None, setWebExports=lambda *a: None,
    writeConfig=lambda name, value: config.update(value))
window.form = SimpleNamespace(menuTools=QMenu(window), menubar=window.menuBar())
speed_menu = window.form.menubar.addMenu('Speed Streak')
calls = []
window.reviewer = SimpleNamespace(web=SimpleNamespace(eval=calls.append))
bottom_calls=[]
window.bottomWeb = SimpleNamespace(eval=bottom_calls.append)
aqt.mw = window
root = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('afterglow_test', root / '__init__.py', submodule_search_locations=[str(root)])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
c = module.controller
c.attach_menu()
c.attach_menu()
assert speed_menu.actions().count(c.action) == 1
c.state_changed('review', 'overview')
for _ in range(20):
    app.processEvents();time.sleep(.02)
assert c.listening and c.audio._process is not None
assert calls and 'window.Afterglow' in calls[-1]
assert bottom_calls and '"primary": false' in bottom_calls[-1]
QTimer.singleShot(150, lambda: app.activeModalWidget().reject())
c.settings()
c.config['immersive'] = False
c.tick()
assert 'enabled:false' in bottom_calls[-1]
c.config['immersive'] = True
c.state_changed('overview', 'review')
assert not c.listening and '"enabled": false' in calls[-1]
c.state_changed('review', 'overview')
c.config['enabled'] = False
c.tick()
assert not c.listening and c.audio._process is None
c.close()
c.timer.stop()
class WebStub(QWidget):
    def eval(self, script):
        self.last_script=script
    def evalWithCallback(self, script, callback):
        callback({'fps':60,'renderer':'webgl'} if 'metrics()' in script else True)
    def zoomFactor(self):
        return 1.25
real_geometry=WebStub(window)
real_geometry.setGeometry(20,30,800,600)
window.reviewer.web=real_geometry
c.active=True
c.tick()
payload=json.loads(real_geometry.last_script.split('window.Afterglow.update(',1)[1][:-2])
assert payload['surface']['view_width']==800 and payload['surface']['view_height']==600
assert payload['surface']['x']==20 and payload['surface']['y']==30
assert payload['surface']['dpr']==real_geometry.devicePixelRatioF()
with tempfile.TemporaryDirectory() as directory:
    original_root=module.ROOT;module.ROOT=Path(directory)
    c.record_performance([real_geometry])
    report=json.loads((module.ROOT/'user_files/performance.jsonl').read_text())
    assert report['panes'][0]['metrics']['fps']==60
    assert report['geometry'][0]['zoom']==1.25
    assert 'card' not in report
    (module.ROOT/'user_files/particle-cloud-v0.5.json').write_text(json.dumps({'palette':'ultraviolet','particle_count':4200,'motion':55,'impact':80}))
    c.restore_cloud()
    assert c.config['visual']=='particles' and c.config['palette']=='ultraviolet'
    assert c.config['particle_count']==4200 and c.config['impact']==80
    module.ROOT=original_root
c.close()
print('PASS: Anki libraries, menu, settings dialog, audio start/stop, reviewer bridge')
