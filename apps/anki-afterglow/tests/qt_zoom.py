"""Exercise actual Qt WebEngine zoom, independently of the user's Anki profile."""
import os
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu'
import json
import time
from pathlib import Path
from aqt.qt import QApplication, QEventLoop, QTimer, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

app=QApplication(['afterglow-zoom-test'])
view=QWebEngineView()
view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
profile=QWebEngineProfile(view)  # Off the record: no user browser or Anki storage.
page=QWebEnginePage(profile,view)
view.setPage(page)
view.resize(1000,900)
view.show()
print('Qt WebEngine initialized',flush=True)
root=Path(__file__).parents[1]
html='<html><head><style>body{margin:0;color:white}#qa{font:24px sans-serif;display:inline-block}</style><style>'+ (root/'web/afterglow.css').read_text()+'</style></head><body><div id="qa">Zoom this card text</div><script>'+(root/'web/afterglow.js').read_text()+'</script></body></html>'

def wait(seconds=.2):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        app.processEvents();time.sleep(.005)

def js(code):
    result=[]
    loop=QEventLoop()
    page.runJavaScript(code,lambda value:(result.append(value),loop.quit()))
    QTimer.singleShot(5000,loop.quit)
    loop.exec()
    assert result,'JavaScript callback timed out'
    return result[0]

def paint(y=0,dpr=None):
    data={'config':{'enabled':True,'motion':0,'intensity':65,'immersive':True},
          'surface':{'x':0,'y':y,'width':1000,'height':900,'view_width':view.width(),
                     'view_height':view.height(),'dpr':view.devicePixelRatioF() if dpr is None else dpr},
          'primary':True,'scene_time':0}
    data['config']['intensity']=66
    js('Afterglow.update('+json.dumps(data)+')')
    data['config']['intensity']=65
    js('Afterglow.update('+json.dumps(data)+')')
    wait()

try:
    view.setHtml(html)
    wait(.6)
    print('HTML loaded',flush=True)
    snapshots=[];sizes=[]
    for zoom in (.75,1,1.25,1.5,2,2.5):
        view.setZoomFactor(zoom)
        wait()
        paint()
        print('Checked zoom',zoom,flush=True)
        snapshots.append(js('document.querySelector("canvas").toDataURL()'))
        sizes.append(js('document.querySelector("#qa").getBoundingClientRect().width*1000/innerWidth'))
    assert len(set(snapshots))==1,'Background changed under Qt page zoom'
    assert max(sizes)>min(sizes)*3,'Card text did not actually zoom during the test'
    paint(dpr=1)
    js('(()=>{let c=document.createElement("canvas");c.width=1000;c.height=100;const ctx=c.getContext("2d",{alpha:false});ctx.drawImage(document.querySelector("canvas"),0,800,1000,100,0,0,1000,100);window.expectedPixels=Array.from(ctx.getImageData(0,0,1000,100).data);})()')
    view.resize(1000,100)
    view.setZoomFactor(1)
    wait()
    paint(800,dpr=1)
    diff=js('(()=>{const c=document.querySelector("canvas"),p=c.getContext("2d").getImageData(0,0,c.width,c.height).data;let d=0;for(let i=0;i<p.length;i++)d+=Math.abs(p[i]-expectedPixels[i]);return {difference:d/p.length,width:c.width,height:c.height,expected:expectedPixels.length};})()')
    print('Answer-bar pixel comparison:',diff,flush=True)
    assert diff['width']==1000 and diff['height']==100 and diff['difference']<1,'Differently zoomed answer-bar slice is misaligned'
    print('PASS: Qt WebEngine 75/100/125/150/200/250% zoom leaves background pixel-identical; card text scales; independently zoomed answer-bar slice aligns')
finally:
    view.close()
    page.deleteLater()
    wait(.1)
