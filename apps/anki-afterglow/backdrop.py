"""A single non-interactive GPU surface beneath Anki's existing webviews."""
from aqt.qt import QWebEngineView,QWebEnginePage,QWebEngineProfile,Qt


class SharedBackdrop(QWebEngineView):
    def __init__(self, host, script):
        super().__init__(host)
        self.setObjectName('afterglowSharedBackdrop')
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,True)
        self.profile=QWebEngineProfile(self)
        self.setPage(QWebEnginePage(self.profile,self))
        self.setHtml('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0"><script>'+script+'</script></body></html>')
        self.setGeometry(host.rect())
        self.lower()

    def eval(self,script):
        self.page().runJavaScript(script)

    def evalWithCallback(self,script,callback):
        self.page().runJavaScript(script,callback)
