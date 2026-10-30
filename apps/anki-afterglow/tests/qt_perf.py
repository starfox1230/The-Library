"""Three-pane Qt WebEngine frame-cadence probe; no Anki profile is opened."""
import json
import time
from pathlib import Path
from aqt.qt import QApplication,QMainWindow,QWidget,QVBoxLayout,QTimer,Qt,QEventLoop
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile

app=QApplication(['afterglow-performance-test'])
window=QMainWindow();window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen,True)
host=QWidget();layout=QVBoxLayout(host);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0);window.setCentralWidget(host)
root=Path(__file__).parents[1]
script='\n'.join((root/('web/'+name)).read_text() for name in ('liquid.js','particles.js','afterglow.js'))
html='<html><body style="margin:0"><script>'+script+'</script></body></html>'
views=[];profiles=[]
for height in (50,None,90):
    view=QWebEngineView(host);profile=QWebEngineProfile(view);view.setPage(QWebEnginePage(profile,view));profiles.append(profile)
    if height:view.setFixedHeight(height)
    layout.addWidget(view);view.setHtml(html);views.append(view)
window.resize(1920,1080);window.show()
start=time.monotonic()
def update():
    t=time.monotonic()-start
    for view in views:
        pos=view.mapTo(host,view.rect().topLeft())
        data={'config':{'enabled':True,'visual':'particles','motion':55,'quality':1,'intensity':80,'show_meter':False},
              'flow_time':t*.6,'flow_rate':.6,'particle_phases':[t*(.2+i*.06) for i in range(8)],'particle_rates':[.2+i*.06 for i in range(8)],
              'camera_phase':t*.06,'camera_rate':.06,'music_level':.6,'energy':.03,'bass':.02,
              'surface':{'x':pos.x(),'y':pos.y(),'width':host.width(),'height':host.height(),'view_width':view.width(),'view_height':view.height(),'dpr':view.devicePixelRatioF()}}
        view.page().runJavaScript('window.Afterglow&&Afterglow.update('+json.dumps(data)+')')
timer=QTimer();timer.setInterval(33);timer.timeout.connect(update);timer.start()
while time.monotonic()-start<8:app.processEvents();time.sleep(.003)
result=[]
for view in views:
    loop=QEventLoop();view.page().runJavaScript('Afterglow.metrics()',lambda value:(result.append(value),loop.quit()));QTimer.singleShot(3000,loop.quit);loop.exec()
assert len(result)==3 and all(r and r['fps']>10 for r in result),result
print(json.dumps({'window':[host.width(),host.height()],'panes':result}),flush=True)
timer.stop();window.close()
for view in views:view.page().deleteLater()
app.processEvents()
