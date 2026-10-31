"""Exercise actual Qt WebEngine zoom, independently of the user's Anki profile."""
import os
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu'
import json
import time
import sys
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
html='<html><head><style>body{margin:0;color:white}#qa{font:24px sans-serif;display:inline-block}</style><style>'+ (root/'web/afterglow.css').read_text()+'</style></head><body><div id="qa">Zoom this card text</div><script>'+'\n'.join((root/('web/'+name)).read_text() for name in ('liquid.js','particles.js','club.js','waves.js','afterglow.js'))+'</script></body></html>'

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
    data={'config':{'enabled':True,'visual':'waves' if '--waves' in sys.argv else 'club' if '--club' in sys.argv else 'particles','motion':0,'intensity':65,'immersive':True},
          'surface':{'x':0,'y':y,'width':1000,'height':900,'view_width':view.width(),
                     'view_height':view.height(),'dpr':view.devicePixelRatioF() if dpr is None else dpr},
          'primary':True,'scene_time':0}
    for intensity in (66,65):
        before=js('Afterglow.metrics().frames')
        data['config']['intensity']=intensity
        js('Afterglow.update('+json.dumps(data)+')')
        deadline=time.monotonic()+3
        while js('Afterglow.metrics().frames')<=before and time.monotonic()<deadline:wait(.02)
        assert js('Afterglow.metrics().frames')>before,'Expected static repaint did not finish'

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
        comparison=js('(()=>{const e=document.querySelector("canvas"),c=document.createElement("canvas");c.width=e.width;c.height=e.height;const ctx=c.getContext("2d");ctx.drawImage(e,0,0);const p=ctx.getImageData(0,0,c.width,c.height).data;if(!window.zoomPixels)window.zoomPixels=new Uint8ClampedArray(p);let d=0;for(let i=0;i<p.length;i++)d+=Math.abs(p[i]-zoomPixels[i]);return {width:c.width,height:c.height,difference:d/p.length,renderer:Afterglow.renderer};})()')
        print('Zoom pixels:',comparison,flush=True)
        sizes.append(js('document.querySelector("#qa").getBoundingClientRect().width*1000/innerWidth'))
    assert len(set(snapshots))==1,'Background changed under Qt page zoom'
    assert max(sizes)>min(sizes)*3,'Card text did not actually zoom during the test'
    paint(dpr=1)
    js('(()=>{let c=document.createElement("canvas");c.width=800;c.height=80;const ctx=c.getContext("2d",{alpha:false});ctx.drawImage(document.querySelector("canvas"),0,640,800,80,0,0,800,80);window.expectedPixels=Array.from(ctx.getImageData(0,0,800,80).data);})()')
    view.resize(1000,100)
    view.setZoomFactor(1)
    wait()
    paint(800,dpr=1)
    diff=js('(()=>{const c=document.querySelector("canvas"),copy=document.createElement("canvas");copy.width=c.width;copy.height=c.height;const ctx=copy.getContext("2d");ctx.drawImage(c,0,0);const p=ctx.getImageData(0,0,c.width,c.height).data;let d=0;for(let i=0;i<p.length;i++)d+=Math.abs(p[i]-expectedPixels[i]);return {difference:d/p.length,width:c.width,height:c.height,expected:expectedPixels.length};})()')
    print('Answer-bar pixel comparison:',diff,flush=True)
    assert diff['width']==800 and diff['height']==80 and diff['difference']<1,'Differently zoomed answer-bar slice is misaligned'
    print('PASS: Qt WebEngine 75/100/125/150/200/250% zoom leaves background pixel-identical; card text scales; independently zoomed answer-bar slice aligns')
finally:
    view.close()
    page.deleteLater()
    wait(.1)
