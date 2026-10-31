"""Afterglow: independent reviewer decoration. Does not import or patch Speed Streak."""
import json
import platform
import time
import subprocess
import os
from pathlib import Path
from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.toolbar import TopToolbar
from aqt.webview import AnkiWebView
from aqt.qt import (QAction, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                    QFormLayout, QLabel, QSlider, Qt, QTimer, QPoint, QProgressBar, QPushButton, QColor)
from .audio import AudioListener
from .motion import MusicMotion
from .backdrop import SharedBackdrop

ROOT = Path(__file__).parent
PACKAGE = mw.addonManager.addonFromModule(__name__)
DEFAULTS = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


class Afterglow:
    @staticmethod
    def alive(web):
        try:
            if hasattr(web, 'objectName'):
                web.objectName()
            return True
        except RuntimeError:
            return False

    def __init__(self):
        self.config = dict(DEFAULTS, **(mw.addonManager.getConfig(__name__) or {}))
        self.audio = AudioListener()
        self.motion = MusicMotion()
        self.timer = QTimer(mw)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.listening = False
        self.active = False
        self.status_label = None
        self.last_status = ""
        self.meter = None
        self.scene_start = time.monotonic()
        self.last_injection = 0
        self.last_diagnostics = 0
        self.background = None
        self.transparent_pages = {}
        self.scene_fps = 0
        self.last_scene_metrics = 0
        self.decoration_updates = {}
        self.decorated = []
        css = (ROOT / 'web/afterglow.css').read_text(encoding='utf-8')
        js = '\n'.join((ROOT / ('web/'+name)).read_text(encoding='utf-8') for name in ('liquid.js','particles.js','club.js','afterglow.js'))
        self.inject_script = '(function(){if(window.Afterglow)return;const s=document.createElement("style");s.textContent=' + json.dumps(css) + ';document.head.append(s);' + js + '})();'
        self.action = QAction("Afterglow — Music background…", mw)
        self.action.triggered.connect(self.settings)
        mw.form.menuTools.addAction(self.action)
        self.fullscreen_action = QAction('Afterglow — Toggle immersive fullscreen', mw)
        self.fullscreen_action.setShortcut('Ctrl+Alt+F11')
        mw.addAction(self.fullscreen_action)
        self.fullscreen_action.triggered.connect(self.fullscreen)
        mw.form.menuTools.addAction(self.fullscreen_action)
        self.preview_action=QAction('Afterglow — Standalone performance preview',mw)
        self.preview_action.triggered.connect(self.standalone)
        mw.form.menuTools.addAction(self.preview_action)
        mw.addonManager.setConfigAction(__name__, self.settings)
        mw.addonManager.setWebExports(__name__, r"web/.*\.(js|css)")
        gui_hooks.webview_will_set_content.append(self.web_content)
        gui_hooks.state_did_change.append(self.state_changed)
        gui_hooks.profile_will_close.append(self.close)
        gui_hooks.reviewer_did_show_question.append(self.card_shown)
        gui_hooks.reviewer_did_show_answer.append(self.card_shown)
        gui_hooks.profile_did_open.append(self.attach_menu)

    def attach_menu(self):
        # Discover the public Qt menu after all add-ons load. No Speed Streak imports.
        menubar = getattr(mw.form, "menubar", None)
        if not menubar:
            return
        for item in menubar.actions():
            menu = item.menu()
            if menu and item.text().replace("&", "").strip() == "Speed Streak":
                if self.action not in menu.actions():
                    menu.addSeparator()
                    menu.addAction(self.action)
                    menu.addAction(self.fullscreen_action)
                    menu.addAction(self.preview_action)
                return

    def web_content(self, content, context):
        if isinstance(context, (Reviewer, ReviewerBottomBar, TopToolbar)):
            base = f"/_addons/{PACKAGE}/web"
            content.css.append(base + "/afterglow.css")
            content.js.append(base + "/liquid.js")
            content.js.append(base + "/particles.js")
            content.js.append(base + "/club.js")
            content.js.append(base + "/afterglow.js")

    def fullscreen(self):
        toggle = getattr(mw, 'on_toggle_full_screen', None)
        if toggle:
            toggle()

    def standalone(self):
        if platform.system()=='Windows':
            subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'start_preview.ps1')],creationflags=0x08000000)

    def views(self):
        reviewer = getattr(mw, 'reviewer', None)
        main = getattr(reviewer, 'web', None)
        views = [main]
        if self.config.get('immersive', True):
            views.extend([getattr(mw, 'topWeb', None), getattr(mw, 'bottomWeb', None)])
            host = mw.centralWidget()
            if host:
                views.extend(host.findChildren(AnkiWebView))
        unique = []
        for web in views:
            if web is not None and web not in unique and self.alive(web):
                unique.append(web)
        return unique

    def state_changed(self, new, old):
        self.active = new == "review"
        if not self.active:
            self.hide_background()
        self.tick()

    def hide_background(self):
        views = self.views()
        for web in views + [item for item in self.decorated if item not in views]:
            if not self.alive(web):
                continue
            payload = {"config": dict(self.config, enabled=False)}
            web.eval("window.Afterglow && window.Afterglow.update(" + json.dumps(payload) + ");")
        if self.background:
            self.background.eval('window.Afterglow&&Afterglow.update({config:{enabled:false}});')
            self.background.hide()
        self.restore_pages()
        self.decoration_updates.clear()

    def restore_pages(self, keep=()):
        for web, color in list(self.transparent_pages.items()):
            if web not in keep:
                if self.alive(web):web.page().setBackgroundColor(color)
                del self.transparent_pages[web]

    def card_shown(self, card):
        self.active = True
        QTimer.singleShot(0, self.tick)

    def close(self):
        self.active = False
        self.hide_background()
        if self.background:
            self.background.page().deleteLater()
            self.background.deleteLater()
            self.background=None
        self.audio.stop()
        self.listening = False

    def tick(self):
        enabled = bool(self.config.get("enabled"))
        should_listen = self.active and enabled and self.config.get("listen") and platform.system() == "Windows"
        if bool(should_listen) != self.listening:
            self.listening = bool(should_listen)
            self.audio.start() if should_listen else self.audio.stop()
        state = self.audio.snapshot(self.config["lead_ms"])
        state.update(self.motion.feed(time.monotonic(), state, impact=self.config['impact']/100))
        if platform.system() != "Windows":
            state["status"] = "Ambient visuals only — system audio currently supports Windows"
        if self.status_label:
            bpm = state.get("bpm", 0)
            energy = state.get('energy', 0)
            self.status_label.setText(state["status"] + f" · Signal: {energy:.5f}" + (f" · Locked: {bpm:.0f} BPM" if bpm else " · Finding the rhythm" if self.listening and energy > .00005 else " · No sound detected" if self.listening else ""))
            if self.meter:
                self.meter.setValue(min(100, round(energy ** .5 * 350)))
        reviewer = getattr(mw, "reviewer", None)
        web = getattr(reviewer, "web", None)
        if self.active and web:
            inject = time.monotonic() - self.last_injection > 1
            if inject:
                self.last_injection = time.monotonic()
            host = mw.centralWidget() or mw
            views = self.views()
            shared = enabled and self.config.get('shared_background',False) and mw.centralWidget() is not None
            if shared:
                if self.background is None:
                    self.background=SharedBackdrop(host,self.inject_script)
                if self.background.geometry()!=host.rect():self.background.setGeometry(host.rect())
                if not self.background.isVisible():
                    self.background.show();self.background.lower()
                for view in views:
                    if view not in self.transparent_pages:
                        self.transparent_pages[view]=view.page().backgroundColor()
                        view.page().setBackgroundColor(QColor(0,0,0,0))
                self.restore_pages(views)
                payload=dict(state,config=self.config,primary=False,scene_time=time.monotonic()-self.scene_start,
                             surface=dict(x=0,y=0,width=host.width(),height=host.height(),view_width=host.width(),view_height=host.height(),dpr=host.devicePixelRatioF()))
                self.background.eval('window.Afterglow&&Afterglow.update('+json.dumps(payload)+');')
                if time.monotonic()-self.last_scene_metrics>1:
                    self.last_scene_metrics=time.monotonic()
                    self.background.evalWithCallback('window.Afterglow&&Afterglow.metrics()',self.scene_metrics)
            else:
                if self.background:
                    self.background.eval('window.Afterglow&&Afterglow.update({config:{enabled:false}});')
                    self.background.hide()
                self.restore_pages()
            for previous in self.decorated:
                if previous not in views and self.alive(previous):
                    previous.eval('window.Afterglow && window.Afterglow.update({config:{enabled:false}});')
            self.decorated = views
            for surface in views:
                if inject:
                    if hasattr(surface, 'evalWithCallback'):
                        surface.evalWithCallback('!!window.Afterglow', lambda ready, target=surface: self.ensure_renderer(target, ready))
                    else:
                        surface.eval(self.inject_script)
                geometry = None
                if hasattr(surface, 'mapTo'):
                    pos = surface.mapTo(host, QPoint(0, 0))
                    geometry = dict(x=pos.x(), y=pos.y(), width=host.width(), height=host.height(),
                                    view_width=surface.width(), view_height=surface.height(),
                                    dpr=surface.devicePixelRatioF())
                payload = dict(state, config=self.config, surface=geometry,
                               primary=surface is web, scene_time=time.monotonic()-self.scene_start,
                               decoration_only=shared,scene_fps=self.scene_fps)
                # Static transparent pages need no 30 Hz audio stream. Only the
                # optional primary HUD refreshes, at four updates per second.
                if shared:
                    key=json.dumps([self.config,geometry,surface is web])
                    previous_key,last_sent=self.decoration_updates.get(surface,('',0))
                    hud_due=surface is web and self.config.get('show_meter') and time.monotonic()-last_sent>.25
                    if key==previous_key and not hud_due and not inject:
                        continue
                    self.decoration_updates[surface]=(key,time.monotonic())
                else:
                    self.decoration_updates.pop(surface,None)
                surface.eval("window.Afterglow && window.Afterglow.update(" + json.dumps(payload) + ");")
            if self.config.get('diagnostics') and time.monotonic()-self.last_diagnostics>3:
                self.last_diagnostics=time.monotonic()
                self.record_performance(views+([self.background] if shared else []))

    def scene_metrics(self, value):
        if isinstance(value,dict):self.scene_fps=value.get('fps',0)

    def record_performance(self, views):
        from aqt.qt import QQuickWindow
        report={'time':time.time(),'qt_api':str(QQuickWindow.graphicsApi()),
                'qt_opengl':os.environ.get('QT_OPENGL'), 'panes':[],
                'geometry':[dict(width=v.width(),height=v.height(),dpr=v.devicePixelRatioF(),zoom=v.zoomFactor()) for v in views]}
        pending=[len(views)]
        def complete(value,index):
            report['panes'].append(dict(index=index,metrics=value))
            pending[0]-=1
            if pending[0]==0:
                folder=ROOT/'user_files';folder.mkdir(exist_ok=True)
                with (folder/'performance.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(report)+'\n')
        for index,view in enumerate(views):
            if hasattr(view,'evalWithCallback'):
                view.evalWithCallback('window.Afterglow&&Afterglow.metrics()',lambda value,i=index:complete(value,i))
            else:
                complete(None,index)

    def ensure_renderer(self, target, ready):
        if not ready and self.active and self.alive(target):
            target.eval(self.inject_script)

    def settings(self):
        dialog = QDialog(mw)
        dialog.setWindowTitle("Afterglow · Music background")
        dialog.setMinimumWidth(480)
        form = QFormLayout(dialog)
        intro = QLabel("Full-window neon light, with your cards floating in front.\nAudio automatically follows the active output, including HDMI/TV.\nAudio is analyzed locally while reviewing; nothing is saved or uploaded.")
        intro.setWordWrap(True)
        form.addRow(intro)
        def save(key, value):
            self.config[key] = value
            mw.addonManager.writeConfig(__name__, self.config)
            self.tick()
        for key, label in [("enabled", "Enable Afterglow"), ("listen", "React to computer audio"),
                           ("immersive", "Extend behind toolbars, answer buttons and side panes"),
                           ("show_meter", "Show live audio meter on the review screen"),
                           ("shared_background", "Use one shared graphics layer"),
                           ("clear_backgrounds", "Replace card container backgrounds")]:
            box = QCheckBox(label)
            box.setChecked(bool(self.config[key]))
            box.toggled.connect(lambda value, k=key: save(k, value))
            form.addRow(box)
        for key, label, lo, hi in [("intensity", "Light intensity", 0, 100), ("motion", "Motion", 0, 100),
                                   ("impact", "Music / beat impact", 0, 100),
                                   ("particle_count", "Particle count (lower is faster)", 1200, 10000),
                                   ("contrast", "Letter halo strength", 0, 100), ("lead_ms", "Timing advance (ms)", -200, 200)]:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(lo, hi)
            slider.setValue(int(self.config[key]))
            value_label = QLabel(f"{label}: {self.config[key]}")
            slider.valueChanged.connect(lambda value, k=key, l=value_label, title=label: (l.setText(f"{title}: {value}"), save(k, value)))
            form.addRow(value_label, slider)
        palette = QComboBox()
        for title, value in [("Club neon · cyan / magenta / lime", "neon"),("Aurora · cyan / violet / rose", "aurora"), ("Acid · lime / teal / amber", "acid"), ("Ultraviolet · purple / blue / pink", "ultraviolet"), ('Ember · coral / gold / violet','ember')]:
            palette.addItem(title, value)
        palette.setCurrentIndex(max(0, palette.findData(self.config["palette"])))
        palette.currentIndexChanged.connect(lambda _: save("palette", palette.currentData()))
        form.addRow("Palette", palette)
        visual=QComboBox()
        visual.addItem('Techno Club · beat-driven neon ribbons','club')
        visual.addItem('Particle cloud','particles')
        visual.addItem('Liquid wall','liquid')
        visual.setCurrentIndex(max(0,visual.findData(self.config['visual'])))
        visual.currentIndexChanged.connect(lambda _:save('visual',visual.currentData()))
        form.addRow('Visual',visual)
        restore=QPushButton('Restore saved v0.5 Particle Cloud look')
        restore.clicked.connect(lambda: (self.restore_cloud(),dialog.accept()))
        form.addRow(restore)
        quality = QComboBox()
        quality.addItems(["Economy · 30 FPS", "Smooth · display refresh rate"])
        quality.setCurrentIndex(int(self.config["quality"]))
        quality.currentIndexChanged.connect(lambda value: save("quality", value))
        form.addRow("Rendering", quality)
        status = QLabel()
        status.setWordWrap(True)
        self.status_label = status
        form.addRow(status)
        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setTextVisible(False)
        form.addRow('Live audio signal', self.meter)
        fullscreen = QPushButton('Toggle immersive fullscreen')
        fullscreen.clicked.connect(lambda: (dialog.accept(), QTimer.singleShot(0, self.fullscreen)))
        form.addRow(fullscreen)
        form.addRow(QLabel('Enter or leave fullscreen: Ctrl+Alt+F11'))
        form.addRow(QLabel("Timing: increase advance if the light feels late; decrease if early.\nBeat prediction needs several steady beats to lock.\nMotion 0 freezes animation. OS reduced motion is respected."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        self.tick()
        dialog.exec()
        self.status_label = None
        self.meter = None

    def restore_cloud(self):
        saved=ROOT/'user_files/particle-cloud-v0.5.json'
        if not saved.exists():saved=ROOT/'cloud-v0.5.json'
        values=json.loads(saved.read_text(encoding='utf-8-sig'))
        for key in ('intensity','motion','contrast','quality','palette','impact','particle_count'):
            if key in values:self.config[key]=values[key]
        self.config['visual']='particles'
        mw.addonManager.writeConfig(__name__,self.config)
        self.tick()


controller = Afterglow()
