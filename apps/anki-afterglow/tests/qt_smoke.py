"""Run with Anki's own Python; uses a separate offscreen window, no collection."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import importlib.util
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import aqt
from aqt.qt import QApplication, QMainWindow, QMenu, QTimer

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
print('PASS: Anki libraries, menu, settings dialog, audio start/stop, reviewer bridge')
