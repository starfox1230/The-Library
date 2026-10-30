"""Afterglow: independent reviewer decoration. Does not import or patch Speed Streak."""
import json
import platform
import time
from pathlib import Path
from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.toolbar import TopToolbar
from aqt.webview import AnkiWebView
from aqt.qt import (QAction, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                    QFormLayout, QLabel, QSlider, Qt, QTimer, QPoint, QProgressBar, QPushButton)
from .audio import AudioListener

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
        self.decorated = []
        css = (ROOT / 'web/afterglow.css').read_text(encoding='utf-8')
        js = (ROOT / 'web/afterglow.js').read_text(encoding='utf-8')
        self.inject_script = '(function(){if(window.Afterglow)return;const s=document.createElement("style");s.textContent=' + json.dumps(css) + ';document.head.append(s);' + js + '})();'
        self.action = QAction("Afterglow — Music background…", mw)
        self.action.triggered.connect(self.settings)
        mw.form.menuTools.addAction(self.action)
        self.fullscreen_action = QAction('Afterglow — Toggle immersive fullscreen', mw)
        self.fullscreen_action.setShortcut('Ctrl+Alt+F11')
        mw.addAction(self.fullscreen_action)
        self.fullscreen_action.triggered.connect(self.fullscreen)
        mw.form.menuTools.addAction(self.fullscreen_action)
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
                return

    def web_content(self, content, context):
        if isinstance(context, (Reviewer, ReviewerBottomBar, TopToolbar)):
            base = f"/_addons/{PACKAGE}/web"
            content.css.append(base + "/afterglow.css")
            content.js.append(base + "/afterglow.js")

    def fullscreen(self):
        toggle = getattr(mw, 'on_toggle_full_screen', None)
        if toggle:
            toggle()

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

    def card_shown(self, card):
        self.active = True
        QTimer.singleShot(0, self.tick)

    def close(self):
        self.active = False
        self.hide_background()
        self.audio.stop()
        self.listening = False

    def tick(self):
        enabled = bool(self.config.get("enabled"))
        should_listen = self.active and enabled and self.config.get("listen") and platform.system() == "Windows"
        if bool(should_listen) != self.listening:
            self.listening = bool(should_listen)
            self.audio.start() if should_listen else self.audio.stop()
        state = self.audio.snapshot(self.config["lead_ms"])
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
            for previous in self.decorated:
                if previous not in views and self.alive(previous):
                    previous.eval('window.Afterglow && window.Afterglow.update({config:{enabled:false}});')
            self.decorated = views
            for surface in views:
                if inject:
                    surface.eval(self.inject_script)
                geometry = None
                if hasattr(surface, 'mapTo'):
                    pos = surface.mapTo(host, QPoint(0, 0))
                    geometry = dict(x=pos.x(), y=pos.y(), width=host.width(), height=host.height())
                payload = dict(state, config=self.config, surface=geometry,
                               primary=surface is web, scene_time=time.monotonic()-self.scene_start)
                surface.eval("window.Afterglow && window.Afterglow.update(" + json.dumps(payload) + ");")

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
                           ("clear_backgrounds", "Replace card container backgrounds")]:
            box = QCheckBox(label)
            box.setChecked(bool(self.config[key]))
            box.toggled.connect(lambda value, k=key: save(k, value))
            form.addRow(box)
        for key, label, lo, hi in [("intensity", "Light intensity", 0, 100), ("motion", "Motion", 0, 100),
                                   ("impact", "Music / beat impact", 0, 100),
                                   ("contrast", "Letter halo strength", 0, 100), ("lead_ms", "Timing advance (ms)", -200, 200)]:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(lo, hi)
            slider.setValue(int(self.config[key]))
            value_label = QLabel(f"{label}: {self.config[key]}")
            slider.valueChanged.connect(lambda value, k=key, l=value_label, title=label: (l.setText(f"{title}: {value}"), save(k, value)))
            form.addRow(value_label, slider)
        palette = QComboBox()
        for title, value in [("Aurora · cyan / violet / rose", "aurora"), ("Acid · lime / teal / amber", "acid"), ("Ultraviolet · purple / blue / pink", "ultraviolet")]:
            palette.addItem(title, value)
        palette.setCurrentIndex(max(0, palette.findData(self.config["palette"])))
        palette.currentIndexChanged.connect(lambda _: save("palette", palette.currentData()))
        form.addRow("Palette", palette)
        quality = QComboBox()
        quality.addItems(["Economy · 30 FPS", "Smooth · 60 FPS"])
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


controller = Afterglow()
