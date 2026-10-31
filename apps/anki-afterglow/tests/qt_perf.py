"""Three-pane Qt WebEngine frame-cadence probe; no Anki profile is opened."""
import json
import time
import sys
import importlib.util
from pathlib import Path
from aqt.qt import QApplication,QMainWindow,QWidget,QVBoxLayout,QTimer,Qt,QEventLoop
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile
from aqt.qt import QColor

app=QApplication(['afterglow-performance-test'])
window=QMainWindow();window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen,True)
host=QWidget();layout=QVBoxLayout(host);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0);window.setCentralWidget(host)
root=Path(__file__).parents[1]
script='\n'.join((root/('web/'+name)).read_text() for name in ('liquid.js','particles.js','club.js','waves.js','afterglow.js'))
html='<html><body style="margin:0"><script>'+script+'</script></body></html>'
shared='--shared' in sys.argv
views=[];profiles=[]
for height in (50,None,90):
    view=QWebEngineView(host);profile=QWebEngineProfile(view);view.setPage(QWebEnginePage(profile,view));profiles.append(profile)
    if height:view.setFixedHeight(height)
    layout.addWidget(view);view.setHtml(html);views.append(view)
if shared:
    spec=importlib.util.spec_from_file_location('afterglow_backdrop_test',root/'backdrop.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    backdrop=module.SharedBackdrop(host,script)
    for view in views:view.page().setBackgroundColor(QColor(0,0,0,0))
window.resize(1920,1080);window.show()
if shared:backdrop.setGeometry(host.rect());backdrop.show();backdrop.lower()
start=time.monotonic()
def update():
    t=time.monotonic()-start
    for view in views+([backdrop] if shared else []):
        pos=view.mapTo(host,view.rect().topLeft())
        data={'config':{'enabled':True,'visual':'waves' if '--waves' in sys.argv else 'club' if '--club' in sys.argv else 'particles','particle_count':1800 if ('--club' in sys.argv or '--waves' in sys.argv) else 4200,'motion':55,'quality':1,'intensity':80,'show_meter':False},
              'flow_time':t*.6,'flow_rate':.6,'particle_phases':[t*(.2+i*.06) for i in range(8)],'particle_rates':[.2+i*.06 for i in range(8)],
              'camera_phase':t*.06,'camera_rate':.06,'music_level':.6,'energy':.03,'bass':.02,'decoration_only':shared and view is not backdrop,
              'hit_id':int(t*2)+1 if ('--club' in sys.argv or '--waves' in sys.argv) else 0,
              'period':.5 if ('--club' in sys.argv or '--waves' in sys.argv) else 0,'confidence':1,'next_in':.5-t%.5,
              'surface':{'x':pos.x(),'y':pos.y(),'width':host.width(),'height':host.height(),'view_width':view.width(),'view_height':view.height(),'dpr':view.devicePixelRatioF()}}
        view.page().runJavaScript('window.Afterglow&&Afterglow.update('+json.dumps(data)+')')
timer=QTimer();timer.setInterval(33);timer.timeout.connect(update);timer.start()
while time.monotonic()-start<8:app.processEvents();time.sleep(.003)
result=[]
for view in views+([backdrop] if shared else []):
    loop=QEventLoop();view.page().runJavaScript('Afterglow.metrics()',lambda value:(result.append(value),loop.quit()));QTimer.singleShot(3000,loop.quit);loop.exec()
assert len(result)==(4 if shared else 3),result
if shared:
    assert all(r['renderer']=='decorator' and r['frames']==0 for r in result[:3]),result
    assert result[-1]['fps']>10 and result[-1]['renderer']=='webgl',result
else:assert all(r and r['fps']>10 for r in result),result
print(json.dumps({'window':[host.width(),host.height()],'panes':result}),flush=True)
timer.stop();window.close()
for view in views+([backdrop] if shared else []):view.page().deleteLater()
app.processEvents()
