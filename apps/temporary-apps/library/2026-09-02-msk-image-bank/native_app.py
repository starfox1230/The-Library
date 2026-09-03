"""Native desktop MSK image curation bank.

PySide6 is the only runtime dependency. Image files live under the user's
local app-data directory; the repository contains only the 50-item seed list.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import uuid
import webbrowser
import zipfile

from PySide6.QtCore import QEvent, QMimeData, QObject, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget, QInputDialog,
)


APP_DIR = Path(__file__).resolve().parent
LOCAL_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MSK Image Bank"
MODALITIES = [("xr", "Radiograph", "radiograph radiology"), ("ct", "CT", "CT radiology"), ("mri", "MRI", "MRI radiology")]


def parse_seed_data() -> list[dict]:
    text = (APP_DIR / "data.js").read_text(encoding="utf-8")
    pattern = re.compile(
        r'\{id:"(?P<id>[^"]+)",name:"(?P<name>[^"]+)",group:"(?P<group>[^"]+)",'
        r'q:"(?P<q>[^"]+)",findings:\{xr:"(?P<xr>[^"]*)",ct:"(?P<ct>[^"]*)",mri:"(?P<mri>[^"]*)"\}\}'
    )
    items = [match.groupdict() for match in pattern.finditer(text)]
    if len(items) != 50:
        raise RuntimeError(f"Expected 50 seed diagnoses, found {len(items)}")
    for item in items:
        item["findings"] = {key: item.pop(key) for key in ("xr", "ct", "mri")}
    return items


def now_id() -> str:
    return f"image-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def open_in_chrome(url: str) -> None:
    candidates = [
        shutil.which("chrome"),
        os.environ.get("PROGRAMFILES", "") + r"\Google\Chrome\Application\chrome.exe",
        os.environ.get("LOCALAPPDATA", "") + r"\Google\Chrome\Application\chrome.exe",
    ]
    chrome = next((path for path in candidates if path and Path(path).exists()), None)
    if chrome:
        subprocess.Popen([chrome, "--new-tab", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):  # noqa: N802 - Qt API name
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ImageViewer(QDialog):
    def __init__(self, image_path: Path | None, source_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("QDialog { background: #03070d; } QLabel { color: #b7c5d8; }")
        self.image_path, self.source_url = image_path, source_url
        self.label = ClickableLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background:#03070d;")
        self.label.setMouseTracking(True)
        self.label.clicked.connect(self.close)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.label)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._refresh()

    def _refresh(self):
        if self.image_path and self.image_path.exists():
            pixmap = QPixmap(str(self.image_path))
            target = QSize(max(1, int(self.width() * .92)), max(1, int(self.height() * .92)))
            self.label.setPixmap(pixmap.scaled(target, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif self.source_url:
            self.label.setText(f"Image URL\n{self.source_url}\n\nClick anywhere or press Esc to close")
        else:
            self.label.setText("Image unavailable\n\nClick anywhere or press Esc to close")

    def resizeEvent(self, event):  # noqa: N802 - Qt API name
        self._refresh(); super().resizeEvent(event)

    def mousePressEvent(self, event):  # noqa: N802 - Qt API name
        self.close()

    def keyPressEvent(self, event):  # noqa: N802 - Qt API name
        if event.key() == Qt.Key.Key_Escape: self.close()
        else: super().keyPressEvent(event)


class ImageCard(QFrame):
    changed = Signal()
    removed = Signal(str)
    opened = Signal(str)

    def __init__(self, image: dict, root: Path, parent=None):
        super().__init__(parent); self.image = image; self.root = root
        self.setObjectName("ImageCard"); self.setStyleSheet("QFrame#ImageCard { background:#0b141f; border:1px solid #26364a; border-radius:7px; }")
        layout = QVBoxLayout(self); layout.setContentsMargins(7, 7, 7, 7); layout.setSpacing(6)
        self.preview = ClickableLabel(); self.preview.setFixedSize(190, 145); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setStyleSheet("background:#050a11; border:0;")
        self.preview.setToolTip("Click to view full screen"); self.preview.clicked.connect(lambda: self.opened.emit(self.image["id"])); layout.addWidget(self.preview)
        self.caption = QLineEdit(image.get("caption", "")); self.caption.setPlaceholderText("Caption / source note"); self.caption.textChanged.connect(self._caption_changed); layout.addWidget(self.caption)
        row = QHBoxLayout(); self.favorite = QCheckBox("Favorite"); self.favorite.setChecked(bool(image.get("favorite"))); self.favorite.stateChanged.connect(self._favorite_changed); row.addWidget(self.favorite); row.addStretch()
        remove = QPushButton("Remove"); remove.setFixedWidth(60); remove.clicked.connect(lambda: self.removed.emit(self.image["id"])); row.addWidget(remove); layout.addLayout(row)
        self._load_pixmap()

    def _load_pixmap(self):
        path = self.root / self.image.get("path", "") if self.image.get("path") else None
        if path and path.exists(): self.preview.setPixmap(QPixmap(str(path)).scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif self.image.get("source_url"): self.preview.setText("URL saved\n(click to open)"); self.preview.setStyleSheet("color:#67e8f9; background:#050a11; border:0;")
        else: self.preview.setText("Image unavailable")

    def _caption_changed(self, value): self.image["caption"] = value; self.changed.emit()
    def _favorite_changed(self, value): self.image["favorite"] = bool(value); self.changed.emit()


class ModalityPanel(QGroupBox):
    dropped = Signal(str, object)
    focused = Signal(str)

    def __init__(self, key: str, label: str, parent=None):
        super().__init__(label, parent); self.key = key; self.setAcceptDrops(True); self.setObjectName("ModalityPanel")
        self.setStyleSheet("QGroupBox#ModalityPanel { border:1px solid #26364a; border-radius:9px; margin-top:8px; padding:10px; background:#111925; } QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 5px; color:#e7edf5; font-weight:600; }")

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API name
        if event.mimeData().hasUrls() or event.mimeData().hasImage() or event.mimeData().hasText(): event.acceptProposedAction(); self.focused.emit(self.key)

    def dropEvent(self, event):  # noqa: N802 - Qt API name
        self.focused.emit(self.key); self.dropped.emit(self.key, event.mimeData()); event.acceptProposedAction()

    def mousePressEvent(self, event):  # noqa: N802 - Qt API name
        self.focused.emit(self.key); super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("MSK Image Bank"); self.resize(1380, 900); self.active_id = None; self.active_modality = "xr"; self._building = False
        self.data_root = LOCAL_ROOT; self.images_root = self.data_root / "images"; self.data_root.mkdir(parents=True, exist_ok=True); self.images_root.mkdir(parents=True, exist_ok=True)
        self.pathologies = parse_seed_data(); self.records, self.custom = {}, []
        self.state_path = self.data_root / "state.json"; self._load_state()
        self.setStyleSheet("QMainWindow,QWidget { background:#0b1018; color:#e7edf5; } QLineEdit,QTextEdit { background:#0b131f; border:1px solid #26364a; border-radius:6px; padding:7px; color:#e7edf5; } QPushButton { background:#182536; border:1px solid #26364a; border-radius:6px; padding:7px 10px; color:#e7edf5; } QPushButton:hover { border-color:#22d3ee; background:#20354c; } QPushButton#primary { background:#0e7490; border-color:#22d3ee; } QCheckBox { color:#8ea0b6; } QListWidget { background:#0e1622; border:0; outline:0; } QListWidget::item { padding:7px; border-radius:5px; } QListWidget::item:selected { background:#172131; color:#e7edf5; } QScrollArea { border:0; }")
        self._build_ui(); self.refresh_list(); self.show_first()
        self.installEventFilter(self); QApplication.instance().installEventFilter(self)

    def _load_state(self):
        if self.state_path.exists():
            try:
                saved = json.loads(self.state_path.read_text(encoding="utf-8")); self.records = saved.get("records", {}); self.custom = saved.get("custom", [])
            except (OSError, json.JSONDecodeError): pass
        self.pathologies.extend(self.custom)

    def save_state(self):
        payload = {"format":"msk-image-bank-native", "version":1, "records":self.records, "custom":self.custom}
        self.state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def record(self, pid):
        p = next(item for item in self.pathologies if item["id"] == pid)
        record = self.records.setdefault(pid, {"favorite":False, "notes":"", "findings":dict(p.get("findings", {})), "images":{"xr":[],"ct":[],"mri":[]}})
        record.setdefault("findings", {}).update({key:value for key,value in p.get("findings", {}).items() if key not in record["findings"]})
        record.setdefault("images", {}); [record["images"].setdefault(key, []) for key,_,_ in MODALITIES]
        return record

    def _build_ui(self):
        central = QWidget(); outer = QHBoxLayout(central); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0); self.setCentralWidget(central)
        sidebar = QWidget(); sidebar.setFixedWidth(305); side = QVBoxLayout(sidebar); side.setContentsMargins(12,14,10,12)
        title = QLabel("MSK Image Bank"); title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold)); side.addWidget(title); subtitle = QLabel("Fast visual curation · saved on this computer"); subtitle.setStyleSheet("color:#8ea0b6;font-size:11px;"); side.addWidget(subtitle); side.addSpacing(8)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search pathology…"); self.search.textChanged.connect(self.refresh_list); side.addWidget(self.search); self.favorites_only = QCheckBox("Favorites only"); self.favorites_only.stateChanged.connect(self.refresh_list); side.addWidget(self.favorites_only); self.list = QListWidget(); self.list.itemClicked.connect(self.select_item); side.addWidget(self.list); outer.addWidget(sidebar)
        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(0,0,0,0); self.toolbar = QHBoxLayout(); self.status = QLabel(); self.status.setStyleSheet("color:#8ea0b6;font-size:11px;"); self.toolbar.addWidget(self.status); self.toolbar.addStretch(); self.add_button = QPushButton("＋ Diagnosis"); self.add_button.setObjectName("primary"); self.add_button.clicked.connect(self.add_diagnosis); self.toolbar.addWidget(self.add_button); self.open_all = QPushButton("Open all searches"); self.open_all.setToolTip("Open XR, CT, and MRI Google Images searches in your existing Chrome"); self.open_all.clicked.connect(self.open_all_searches); self.toolbar.addWidget(self.open_all); self.copy_button = QPushButton("Copy favorites"); self.copy_button.clicked.connect(self.copy_favorites); self.toolbar.addWidget(self.copy_button); self.export_button = QPushButton("Export"); self.export_button.clicked.connect(self.export_favorites); self.toolbar.addWidget(self.export_button); self.import_button = QPushButton("Import"); self.import_button.clicked.connect(self.import_backup); self.toolbar.addWidget(self.import_button); right_layout.addLayout(self.toolbar)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.detail = QWidget(); self.detail_layout = QVBoxLayout(self.detail); self.detail_layout.setContentsMargins(22,18,22,40); self.scroll.setWidget(self.detail); right_layout.addWidget(self.scroll); outer.addWidget(right, 1)

    def refresh_list(self):
        if not hasattr(self, "list"): return
        needle = self.search.text().strip().lower(); self.list.clear(); current = None
        for p in self.pathologies:
            r = self.record(p["id"]); is_favorite = r.get("favorite") or any(img.get("favorite") for images in r["images"].values() for img in images)
            if needle and needle not in f'{p["name"]} {p["group"]} {p.get("q","")}'.lower(): continue
            if self.favorites_only.isChecked() and not is_favorite: continue
            if p["group"] != current:
                current = p["group"]; header = QListWidgetItem(current.upper()); header.setFlags(Qt.ItemFlag.NoItemFlags); header.setForeground(QColor("#6f849d")); self.list.addItem(header)
            item = QListWidgetItem(("★ " if is_favorite else "☆ ") + p["name"]); item.setData(Qt.ItemDataRole.UserRole, p["id"]); self.list.addItem(item)
        total = sum(len(imgs) for p in self.pathologies for imgs in self.record(p["id"])["images"].values()); fav = sum(1 for p in self.pathologies if (self.record(p["id"]).get("favorite") or any(image.get("favorite") for images in self.record(p["id"])["images"].values() for image in images))); self.status.setText(f"{len(self.pathologies)} diagnoses · {total} images · {fav} favorites · saved locally")

    def show_first(self): self.active_id = self.pathologies[0]["id"] if self.pathologies else None; self.render_detail()
    def select_item(self, item):
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid: self.active_id = pid; self.render_detail()

    def clear_detail(self):
        while self.detail_layout.count():
            widget = self.detail_layout.takeAt(0).widget()
            if widget: widget.deleteLater()

    def render_detail(self):
        if not self.active_id: return
        self.clear_detail(); p = next(item for item in self.pathologies if item["id"] == self.active_id); r = self.record(self.active_id)
        head = QHBoxLayout(); info = QVBoxLayout(); eyebrow = QLabel(p["group"].upper()); eyebrow.setStyleSheet("color:#67e8f9;font-size:10px;font-weight:600;letter-spacing:1px;"); info.addWidget(eyebrow); heading = QLabel(p["name"]); heading.setFont(QFont("Segoe UI", 22, QFont.Weight.DemiBold)); info.addWidget(heading); helper = QLabel("Search, curate, and keep multiple images per modality."); helper.setStyleSheet("color:#8ea0b6;font-size:11px;"); info.addWidget(helper); head.addLayout(info); head.addStretch(); favorite = QPushButton("★ Favorited" if r.get("favorite") else "☆ Favorite pathology"); favorite.setObjectName("primary" if r.get("favorite") else ""); favorite.clicked.connect(self.toggle_pathology_favorite); head.addWidget(favorite); self.detail_layout.addLayout(head)
        columns = QHBoxLayout(); columns.setSpacing(12)
        for key, label, query in MODALITIES:
            panel = ModalityPanel(key, label); panel.focused.connect(self.set_active_modality); panel.dropped.connect(self.handle_drop); layout = QVBoxLayout(panel); links = QPushButton("Google Images ↗"); links.setToolTip("Open this modality's Google Images search in your existing Chrome"); links.clicked.connect(lambda _=False, k=key, q=query: self.open_search(p, k, q)); layout.addWidget(links)
            findings = QTextEdit(); findings.setPlainText(r["findings"].get(key, "")); findings.setMinimumHeight(92); findings.setPlaceholderText("Classic report finding"); findings.setToolTip("Editable personal reference text"); findings.textChanged.connect(lambda k=key, editor=findings: self.update_finding(k, editor)); layout.addWidget(findings)
            hint = QLabel("Drop images anywhere in this panel · click an image to view full screen"); hint.setStyleSheet("color:#6f849d;font-size:10px;"); hint.setWordWrap(True); layout.addWidget(hint)
            grid_host = QWidget(); grid = QGridLayout(grid_host); grid.setContentsMargins(0,0,0,0); grid.setSpacing(9); images = r["images"][key]
            for index, image in enumerate(images):
                card = ImageCard(image, self.data_root); card.changed.connect(self.save_state); card.removed.connect(lambda image_id, k=key: self.remove_image(k, image_id)); card.opened.connect(self.open_image_viewer); grid.addWidget(card, index // 2, index % 2)
            if not images:
                empty = QLabel("No images collected yet."); empty.setStyleSheet("color:#6f849d;padding:12px 0;"); grid.addWidget(empty, 0, 0)
            layout.addWidget(grid_host); columns.addWidget(panel, 1)
        self.detail_layout.addLayout(columns); notes_label = QLabel("Personal note"); notes_label.setStyleSheet("color:#8ea0b6;font-size:11px;"); self.detail_layout.addWidget(notes_label); notes = QTextEdit(); notes.setPlainText(r.get("notes", "")); notes.setMinimumHeight(65); notes.setPlaceholderText("Optional memory hook, differential, or Anki cue…"); notes.textChanged.connect(lambda editor=notes: self.update_notes(editor)); self.detail_layout.addWidget(notes); tip = QLabel("Paste: click a modality first, then Ctrl/Cmd+V. Export creates a ZIP containing favorites.json plus the actual favorite image files."); tip.setStyleSheet("color:#6f849d;font-size:10px;"); tip.setWordWrap(True); self.detail_layout.addWidget(tip); self.refresh_list()

    def set_active_modality(self, key): self.active_modality = key
    def update_finding(self, key, editor):
        if self.active_id and not self._building: self.record(self.active_id)["findings"][key] = editor.toPlainText(); self.save_state()
    def update_notes(self, editor):
        if self.active_id and not self._building: self.record(self.active_id)["notes"] = editor.toPlainText(); self.save_state()

    def search_url(self, p, key, query):
        search_terms = f'{p.get("q", p["name"])} {query}'
        return f"https://www.google.com/search?tbm=isch&q={quote_plus(search_terms)}"
    def open_search(self, p, key, query): open_in_chrome(self.search_url(p, key, query))
    def open_all_searches(self):
        p = next(item for item in self.pathologies if item["id"] == self.active_id)
        for key, _, query in MODALITIES: self.open_search(p, key, query)

    def toggle_pathology_favorite(self):
        r = self.record(self.active_id); next_value = not r.get("favorite", False); r["favorite"] = next_value
        for images in r["images"].values():
            for image in images: image["favorite"] = next_value
        self.save_state(); self.render_detail()

    def add_diagnosis(self):
        name, ok = QInputDialog.getText(self, "Add diagnosis", "Diagnosis name:")
        if not ok or not name.strip(): return
        group, ok = QInputDialog.getText(self, "Add diagnosis", "Group:", text="My additions")
        if not ok: return
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + "-" + uuid.uuid4().hex[:6]; item = {"id":slug,"name":name.strip(),"group":group.strip() or "My additions","q":name.strip(),"findings":{"xr":"","ct":"","mri":""}}; self.custom.append(item); self.pathologies.append(item); self.active_id = slug; self.save_state(); self.render_detail()

    def handle_drop(self, key, mime: QMimeData):
        self.active_modality = key; count = 0
        if mime.hasImage():
            image = mime.imageData(); qimage = image if isinstance(image, QImage) else QImage(image); count += self.add_qimage(key, qimage)
        for url in mime.urls():
            if url.isLocalFile(): count += self.add_file(key, Path(url.toLocalFile()))
            elif url.scheme() in ("http", "https"): count += self.add_url(key, url.toString())
        if not mime.urls() and mime.text().strip().startswith(("http://", "https://")):
            count += self.add_url(key, mime.text().strip())
        if count:
            self.render_detail(); self.status.setText(f"Added {count} image{'s' if count != 1 else ''} to {dict((key, label) for key, label, _ in MODALITIES)[key]}")

    def add_qimage(self, key, qimage: QImage):
        if qimage.isNull(): return 0
        return self._save_qimage(key, qimage, "")
    def add_file(self, key, path: Path):
        image = QImage(str(path)); return self._save_qimage(key, image, str(path)) if not image.isNull() else 0
    def add_url(self, key, url: str):
        try:
            request = Request(url, headers={"User-Agent":"Mozilla/5.0"}); data = urlopen(request, timeout=12).read(); image = QImage.fromData(data); return self._save_qimage(key, image, url) if not image.isNull() else self._save_url_only(key, url)
        except Exception: return self._save_url_only(key, url)
    def _save_url_only(self, key, url):
        image = {"id":now_id(),"path":"","source_url":url,"caption":"","favorite":self.record(self.active_id).get("favorite",False),"createdAt":datetime.now().isoformat()}; self.record(self.active_id)["images"][key].append(image); self.save_state(); return 1
    def _save_qimage(self, key, qimage: QImage, source: str):
        image_id = now_id(); folder = self.images_root / self.active_id; folder.mkdir(parents=True, exist_ok=True); path = folder / f"{image_id}.png"; qimage.save(str(path), "PNG"); relative = str(path.relative_to(self.data_root)); image = {"id":image_id,"path":relative,"source_url":source if source.startswith("http") else "","caption":"","favorite":self.record(self.active_id).get("favorite",False),"createdAt":datetime.now().isoformat()}; self.record(self.active_id)["images"][key].append(image); self.save_state(); return 1

    def remove_image(self, key, image_id):
        images = self.record(self.active_id)["images"][key]; image = next((item for item in images if item["id"] == image_id), None)
        if not image: return
        images.remove(image); path = self.data_root / image.get("path", "")
        if path.exists() and path.is_file(): path.unlink()
        self.save_state(); self.render_detail()
    def open_image_viewer(self, image_id):
        image = next((image for images in self.record(self.active_id)["images"].values() for image in images if image["id"] == image_id), None)
        if not image: return
        viewer = ImageViewer(self.data_root / image.get("path", "") if image.get("path") else None, image.get("source_url", ""), self); viewer.showFullScreen(); viewer.exec()

    def favorite_payload(self):
        diagnoses = []
        for p in self.pathologies:
            r = self.record(p["id"]); selected = r.get("favorite") or any(image.get("favorite") for images in r["images"].values() for image in images)
            if not selected: continue
            copied = {"id":p["id"],"name":p["name"],"group":p["group"],"favorite":bool(r.get("favorite")),"findings":r["findings"],"notes":r.get("notes", ""),"images":{}}
            for key,_,_ in MODALITIES: copied["images"][key] = [{k:v for k,v in image.items() if k != "path"} | {"path":image.get("path", "")} for image in r["images"][key] if r.get("favorite") or image.get("favorite")]
            diagnoses.append(copied)
        return {"format":"msk-image-bank-native","version":1,"exportedAt":datetime.now().isoformat(),"diagnoses":diagnoses}
    def copy_favorites(self): QApplication.clipboard().setText(json.dumps(self.favorite_payload(), indent=2, ensure_ascii=False)); self.status.show(); QMessageBox.information(self, "MSK Image Bank", "Favorite metadata copied to the clipboard.")
    def export_favorites(self):
        target, _ = QFileDialog.getSaveFileName(self, "Export favorites", str(Path.home() / "msk-image-bank-favorites.zip"), "ZIP archive (*.zip)")
        if not target: return
        payload = self.favorite_payload()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("favorites.json", json.dumps(payload, indent=2, ensure_ascii=False))
            for diagnosis in payload["diagnoses"]:
                for images in diagnosis["images"].values():
                    for image in images:
                        if image.get("path"):
                            path = self.data_root / image["path"]
                            if path.exists(): archive.write(path, f"images/{diagnosis['id']}/{path.name}")
        QMessageBox.information(self, "MSK Image Bank", "Exported favorites.json and the actual favorite image files.")
    def import_backup(self):
        source, _ = QFileDialog.getOpenFileName(self, "Import favorites", "", "ZIP archive (*.zip);;JSON file (*.json)")
        if not source: return
        try:
            if source.lower().endswith(".json"):
                payload = json.loads(Path(source).read_text(encoding="utf-8")); members = {}
            else:
                with zipfile.ZipFile(source) as archive:
                    payload = json.loads(archive.read("favorites.json")); members = {name:archive.read(name) for name in archive.namelist() if name.startswith("images/") and ".." not in Path(name).parts}
            for item in payload.get("diagnoses", []):
                if not any(p["id"] == item.get("id") for p in self.pathologies): continue
                r = self.record(item["id"]); r["favorite"] = bool(item.get("favorite")); r["notes"] = item.get("notes", r.get("notes", "")); r["findings"].update(item.get("findings", {}))
                for key,_,_ in MODALITIES:
                    for image in item.get("images", {}).get(key, []):
                        path = image.get("path", ""); saved = dict(image); saved["id"] = now_id(); saved["favorite"] = bool(image.get("favorite"))
                        if members and path:
                            source_name = next((name for name in members if name.endswith(Path(path).name)), None)
                            if source_name:
                                dest = self.images_root / item["id"] / f"{saved['id']}.png"; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(members[source_name]); saved["path"] = str(dest.relative_to(self.data_root))
                        r["images"][key].append(saved)
            self.save_state(); self.render_detail(); QMessageBox.information(self, "MSK Image Bank", "Import complete.")
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error: QMessageBox.warning(self, "Import failed", str(error))

    def eventFilter(self, watched: QObject, event):  # noqa: N802 - Qt API name
        if event.type() == QEvent.Type.MouseButtonPress:
            widget = watched
            while widget is not None:
                if isinstance(widget, ModalityPanel):
                    self.active_modality = widget.key
                    break
                widget = widget.parent()
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            clipboard = QApplication.clipboard(); image = clipboard.image()
            if not image.isNull(): self.add_qimage(self.active_modality, image); self.render_detail(); return True
            text = clipboard.text().strip()
            if text.startswith(("http://", "https://")): self.add_url(self.active_modality, text); self.render_detail(); return True
        return super().eventFilter(watched, event)


def main() -> int:
    if "--self-test" in sys.argv: print(f"Loaded {len(parse_seed_data())} diagnoses"); return 0
    app = QApplication(sys.argv); app.setApplicationName("MSK Image Bank"); window = MainWindow(); window.show(); return app.exec()


if __name__ == "__main__": raise SystemExit(main())
