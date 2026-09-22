from __future__ import annotations

import ctypes
import sys

if sys.platform != "win32" and __name__ == "__main__":
    raise SystemExit("This application requires Windows 10 (2004+) or Windows 11.")

if sys.platform == "win32":
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

import mss
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QColorDialog, QFileDialog, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget, QTabWidget, QToolButton, QToolTip,
)

from engine import Detector, Settings, exclude_from_capture, position_overlay
from config import load_settings, save_settings
from controls import AccentCheckBox, HotkeyButton
from help_text import HELP
from overlay import Overlay


STYLE = """
QWidget { background: #11161c; color: #e4ebf1; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
QMainWindow { background: #11161c; }
QTabWidget::pane { border: none; padding-top: 12px; }
QTabBar::tab { padding: 12px 20px; background: #19212a; color: #a7b6c4; margin-right: 4px;
               border: 1px solid #243140; border-bottom: none; border-radius: 6px 6px 0 0; }
QTabBar::tab:selected { background: #234840; color: #a5f3d8; border-color: #356055; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #1f2a35; color: #c6d4e0; }
QToolButton#info { color: #b9acff; border: 1px solid #655b91; border-radius: 10px; font-weight: 700; background: #252337; }
QToolButton#info:hover { background: #2f2c4a; border-color: #8a7cc4; }
QGroupBox { background: #19212a; border: 1px solid #303c48; border-radius: 10px;
            margin-top: 14px; padding: 22px 16px 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; color: #b9acff; }
QGroupBox QLabel, QGroupBox QCheckBox, QGroupBox QWidget { background: transparent; }
QLabel#eyebrow { color: #65d5c7; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }
QLabel#heading { font-size: 30px; font-weight: 700; letter-spacing: -0.5px; }
QLabel#muted { color: #a7b6c4; }
QLabel#status { background: #19212a; border: 1px solid #303c48; border-radius: 8px; padding: 12px; }
QLineEdit, QComboBox, QSpinBox { background: #0e1319; border: 1px solid #415363;
                             border-radius: 6px; padding: 8px; min-height: 18px; selection-background-color: #234840; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: #55697c; }
QPushButton { background: #273440; border: 1px solid #415363; border-radius: 6px;
              padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #354756; border-color: #55697c; }
QPushButton:pressed { background: #2c3a47; }
QPushButton#primary { background: #65d5c7; color: #0b2424; border: none; font-weight: 700; }
QPushButton:disabled { color: #7b8b98; background: #202933; border-color: #2a3540; }
QSlider::groove:horizontal { height: 5px; background: #344450; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #65d5c7; border-radius: 2px; }
QSlider::handle:horizontal { background: #d7f9f4; width: 14px; margin: -5px 0; border-radius: 7px; }
QSlider::handle:horizontal:hover { background: #ffffff; }
QCheckBox { spacing: 9px; padding: 5px 0; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #627b8e; border-radius: 4px; background: #11161c; }
QCheckBox::indicator:checked { background: #65d5c7; border-color: #65d5c7; }
QToolTip { color: #e4ebf1; background: #273440; border: 1px solid #415363; padding: 6px; }
QCheckBox:checked { color: #a5f3d8; font-weight: 600; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus { border: 1px solid #b9acff; }
QPushButton#primary:hover { background: #91eddb; }
QPushButton#stop:enabled { background: #632b45; border-color: #df7096; color: #ffe1ec; }
QLabel#status[active="true"] { background: #153c39; border-color: #51c8af; color: #b3f5df; }
QScrollBar:vertical { background: #11161c; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #303c48; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #415363; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollArea { border: none; background: transparent; }
"""


class Console(QMainWindow):
    def __init__(self, settings: Settings | None = None, *, persist: bool = True):
        super().__init__()
        self.worker = None
        self.closing = False
        self.failed = False
        self.persist = persist
        self._loading = True
        self.overlay = Overlay(position_overlay)
        self.defaults = load_settings() if settings is None else settings
        self.setWindowTitle("Vision Test Console")
        self.resize(1000, 840)
        self.setMinimumSize(740, 620)
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(self.label("RETRAC / DEVELOPMENT TOOLS", "eyebrow"))
        layout.addWidget(self.label("Vision test console", "heading"))
        layout.addWidget(self.label("Screen-based detection and controlled input testing for your development build.", "muted"))
        self.status = self.label("Bereit · Sitzung starten, Spielfenster fokussieren und Ziel-Hotkey halten. F8 stoppt.", "status")
        self.status.setWordWrap(True)
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(250)
        self.status_timer.timeout.connect(self.refresh_status_color)
        self.status_timer.start()
        layout.addWidget(self.status)
        tabs = self.tabs = QTabWidget()
        capture, capture_layout = self.group("01  Capture & model")
        self.monitor = QComboBox()
        with mss.mss() as source:
            for index, monitor in enumerate(source.monitors[1:], 1):
                self.monitor.addItem(f"Display {index} · {monitor['width']} × {monitor['height']}", index)
        self.field(capture_layout, "Game display (crosshair must be centered)", self.monitor)
        self.desktop_detection = AccentCheckBox("Detect across desktop · game focus not required")
        self.desktop_detection.setChecked(True)
        self.checkbox(capture_layout, self.desktop_detection)
        self.preview_button = QPushButton("Test selected display capture")
        self.preview_button.clicked.connect(self.preview_capture)
        preview_row = QHBoxLayout()
        preview_row.addWidget(self.preview_button, 1)
        preview_row.addWidget(self.info(self.preview_button.text()))
        capture_layout.addLayout(preview_row)
        self.capture_preview = QLabel("Capture test works without loading an AI model.")
        self.capture_preview.setWordWrap(True)
        self.capture_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capture_preview.setMinimumHeight(100)
        capture_layout.addWidget(self.capture_preview)
        self.title = QLineEdit("Retrac")
        self.field(capture_layout, "Required foreground window title contains", self.title)
        self.model = QLineEdit(self.defaults.model)
        self.model.setReadOnly(True)
        self.field(capture_layout, "Detection model", self.model)
        row = QHBoxLayout()
        browse = QPushButton("Choose trusted .pt model")
        browse.clicked.connect(self.browse)
        starter = QPushButton("Use starter")
        starter.clicked.connect(lambda: self.apply_profile(0))
        self.model_buttons = [browse, starter]
        row.addWidget(browse)
        row.addWidget(self.info(browse.text()))
        row.addWidget(starter)
        row.addWidget(self.info(starter.text()))
        capture_layout.addLayout(row)
        self.class_id = QSpinBox()
        self.class_id.setRange(-1, 9999)
        self.class_id.setSpecialValueText("Automatisch · person / player / enemy")
        self.class_id.setValue(-1)
        self.field(capture_layout, "Target class ID (starter: 0 = person)", self.class_id)
        self.profile = QComboBox()
        self.profile.addItems(["Schnell · Nano / 640 px · Standard", "Ausgewogen · Small-Pose / 640 px", "Qualität / kleine Figuren · sehr langsam"])
        self.field(capture_layout, "Erkennungsprofil", self.profile)
        note = self.label("Schnellprofil: YOLO11n, 640 px, ein Durchlauf, keine zusätzliche Pose-Erkennung. 320 px ist optional noch leichter, übersieht aber eher kleine Figuren. CUDA wird genutzt, falls installiert und verfügbar. COCO erkennt Personen, nicht zuverlässig Gegner oder Teams. Nur vertrauenswürdige .pt-Dateien laden: Sie können Code ausführen.", "muted")
        note.setWordWrap(True)
        capture_layout.addWidget(note)
        model_link = QLabel('<a href="https://huggingface.co/jparedesDS/fortnite-yolo11m">Optional: Fortnite-Community-Modell ansehen</a>')
        model_link.setOpenExternalLinks(True)
        capture_layout.addWidget(model_link)
        model_note = self.label("Dieses externe Modell verlangt Anmeldung und Zustimmung beim Anbieter; es ist nicht mitgeliefert oder hier geprüft. Danach bei Vertrauen lokal auswählen. Automatik wählt player statt head. Eigene Skins sind nicht garantiert abgedeckt.", "muted")
        model_note.setWordWrap(True)
        capture_layout.addWidget(model_note)
        aim, aim_layout = self.group("02  Input simulation")
        self.arm = AccentCheckBox("Enable mouse input")
        self.arm.setChecked(self.defaults.aim_enabled)
        self.checkbox(aim_layout, self.arm)
        self.input_mode = QComboBox()
        self.input_mode.addItem("Cursor · tatsächlichen Mauszeiger zum Ziel bewegen", "cursor")
        self.input_mode.addItem("Fadenkreuz · relative Windows-Mauseingabe", "relative")
        self.field(aim_layout, "Eingabemodus", self.input_mode)
        self.automatic = AccentCheckBox("Automatisch zielen ohne gehaltenen Hotkey")
        self.checkbox(aim_layout, self.automatic)
        self.aim_key = HotkeyButton(0x02)
        self.field(aim_layout, "Hold-to-aim hotkey", self.aim_key)
        self.smoothing = self.slider(aim_layout, "Smoothness · 0 = direkt", 0, 40, 0, "")
        self.region = QComboBox()
        for title, value in [("Körper · Näherung", 35), ("Kopf · Näherung", 12), ("Becken · Näherung", 55), ("Benutzerdefiniert", None)]:
            self.region.addItem(title, value)
        self.field(aim_layout, "Zielbereich", self.region)
        self.vertical = self.slider(aim_layout, "Aim point · % from top of detected box", 5, 90, 35, "%")
        self.vertical.setEnabled(False)
        self.region.currentIndexChanged.connect(self.change_region)
        self.max_step = self.slider(aim_layout, "Bewegungslimit · 0 = unbegrenzt", 0, 500, 0, " px / 60-Hz-Schritt")
        note = self.label("Cursor-Modus bewegt den echten Zeiger ab seiner aktuellen Position. Ein Spiel mit gesperrtem Cursor benötigt gegebenenfalls Fadenkreuz-Modus; dessen Reaktion hängt von Sensitivität und Raw Input ab. Hotkey halten: 0 = direkt, höhere Smoothness = sanfter. Keine Treiber, Speicherzugriffe oder Umgehung gesperrter Eingaben.", "muted")
        note.setWordWrap(True)
        aim_layout.addWidget(note)
        detection, detection_layout = self.group("03  Detection & overlay")
        self.image_size = QComboBox()
        for size in [320, 416, 640, 960, 1280, 1536]:
            self.image_size.addItem(f"{size} px", size)
        self.image_size.setCurrentIndex(self.image_size.findData(self.defaults.image_size))
        self.field(detection_layout, "Erkennungsauflösung", self.image_size)
        self.confidence = self.slider(detection_layout, "Minimum confidence", 5, 95, 20, "%")
        self.tiled = AccentCheckBox("Teilbild-Erkennung für kleine Figuren")
        self.tiled.setChecked(self.defaults.tiled)
        self.checkbox(detection_layout, self.tiled)
        self.full_screen = AccentCheckBox("Gesamten Bildschirm zur Auswahl verwenden")
        self.full_screen.setChecked(True)
        self.checkbox(detection_layout, self.full_screen)
        self.fov = self.slider(detection_layout, "Target selection radius", 40, 4000, 1600, " px")
        self.fov.setEnabled(False)
        self.uncertain_threshold = self.slider(detection_layout, "Unsichere Kandidaten unter", 5, 95, 45, "%")
        detection_note = self.label("Niedrige Konfidenz findet mehr mögliche Personen, erzeugt aber Fehlalarme. Orange/gestrichelt = unsicher, nicht bestätigter Spieler. Reichweite hängt von sichtbaren Pixeln und Modell ab, nicht vom Auswahlradius.", "muted")
        detection_note.setWordWrap(True)
        detection_layout.addWidget(detection_note)
        esp, esp_layout = self.group("ESP · Darstellung")
        self.boxes = AccentCheckBox("Show visible-target bounding boxes")
        self.labels = AccentCheckBox("Show class and confidence")
        self.circle = AccentCheckBox("Show selection radius")
        self.tracers = AccentCheckBox("Linien-ESP")
        self.skeleton = AccentCheckBox("Skeleton-ESP")
        self.joints = AccentCheckBox("Gelenkpunkte anzeigen")
        self.target_marker = AccentCheckBox("Zielpunkt anzeigen")
        for checkbox, checked in [(self.boxes, True), (self.labels, True), (self.circle, False),
                                  (self.tracers, True), (self.skeleton, self.defaults.skeleton),
                                  (self.joints, False), (self.target_marker, False)]:
            checkbox.setChecked(checked)
            self.checkbox(esp_layout, checkbox)
        self.box_style = QComboBox()
        for title, value in [("Eckrahmen", "corners"), ("Vollständiger Rahmen", "rectangle")]:
            self.box_style.addItem(title, value)
        self.field(esp_layout, "Rahmenstil", self.box_style)
        self.tracer_origin = QComboBox()
        for title, value in [("Unten Mitte", "bottom"), ("Bildschirmmitte", "center"), ("Oben Mitte", "top")]:
            self.tracer_origin.addItem(title, value)
        self.field(esp_layout, "Linienursprung", self.tracer_origin)
        self.line_width = self.slider(esp_layout, "Linienstärke", 1, 6, 2, " px")
        self.opacity = self.slider(esp_layout, "ESP-Deckkraft", 10, 100, 90, "%")
        self.fill_opacity = self.slider(esp_layout, "Rahmenfüllung", 0, 60, 8, "%")
        self.keypoint_confidence = self.slider(esp_layout, "Gelenk-Konfidenz", 10, 95, 45, "%")
        self.colors = {}
        for title, key in [("Rahmenfarbe", "box_color"), ("Kandidatenfarbe", "uncertain_color"),
                           ("Linienfarbe", "line_color"), ("Skelettfarbe", "skeleton_color")]:
            button = QPushButton(getattr(self.defaults, key))
            self.colors[key] = button
            button.clicked.connect(lambda checked=False, key=key: self.choose_color(key))
            self.field(esp_layout, title, button)
        pose_note = self.label("Skelette verwenden ausschließlich erkannte COCO-Gelenke, keine erfundenen Knochen. Unsichere Gelenke bleiben unsichtbar. Eigene Detect-Modelle erhalten bei aktivem Skeleton-ESP eine zusätzliche Pose-Inferenz.", "muted")
        pose_note.setWordWrap(True)
        esp_layout.addWidget(pose_note)
        exclusion, exclusion_layout = self.group("Eigenfigur · räumlicher Ausschluss")
        self.exclude_self = AccentCheckBox("Eigenfigur-Ausschlusszone aktiv")
        self.exclude_self.setChecked(True)
        self.checkbox(exclusion_layout, self.exclude_self)
        self.edit_zone = AccentCheckBox("Eigenzone bearbeiten / Vorschau")
        self.checkbox(exclusion_layout, self.edit_zone)
        self.exclusion_bounds = {}
        for title, name, value in [("Links", "left", 15), ("Oben", "top", 40), ("Rechts", "right", 50), ("Unten", "bottom", 100)]:
            control = QSpinBox()
            control.setRange(0, 100)
            control.setSuffix(" %")
            control.setValue(value)
            self.field(exclusion_layout, title, control)
            self.exclusion_bounds[name] = control
            control.valueChanged.connect(self.update_settings)
        warning = self.label("Die Zone ist im Betrieb unsichtbar. Vorschau erscheint nur mit aktiviertem Bearbeiten, auf diesem Tab und bei fokussiertem Einstellungsfenster. Zone eng um den Mittelpunkt der Eigenfigur einstellen: Auch Gegner in der Zone werden ausgefiltert. Zum Vergleich Filter kurz deaktivieren.", "muted")
        warning.setWordWrap(True)
        exclusion_layout.addWidget(warning)
        safety, safety_layout = self.group("04  Session controls")
        self.toggle = HotkeyButton(0x75)
        self.field(safety_layout, "Pause / resume hotkey", self.toggle)
        safety_layout.addWidget(self.label("F8  ·  Emergency stop (fixed)", "eyebrow"))
        note = self.label("Use borderless or windowed mode, and select the display containing the game. Detections cannot distinguish enemies from teammates without a trained model. Hidden or occluded players cannot be tracked from screen pixels alone. Settings are saved to settings.json automatically.", "muted")
        note.setWordWrap(True)
        safety_layout.addWidget(note)
        for name, group in [("Aufnahme", capture), ("Erkennung", detection), ("ESP", esp), ("Eigenfigur", exclusion), ("Zielen", aim), ("Sitzung", safety)]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(group)
            tabs.addTab(scroll, name)
        layout.addWidget(tabs, 1)
        bottom = QHBoxLayout()
        bottom.addWidget(self.label("LOCAL INFERENCE  /  NO SCREEN UPLOADS", "muted"), 1)
        self.start_button = QPushButton("Start session")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start)
        self.stop_button = QPushButton("Stop · F8")
        self.stop_button.setObjectName("stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        bottom.addWidget(self.start_button)
        bottom.addWidget(self.info(self.start_button.text()))
        bottom.addWidget(self.stop_button)
        bottom.addWidget(self.info(self.stop_button.text()))
        layout.addLayout(bottom)
        self.setCentralWidget(outer)
        for checkbox in [self.arm, self.boxes, self.labels, self.circle, self.desktop_detection,
                         self.automatic, self.exclude_self, self.edit_zone, self.tiled,
                         self.full_screen, self.tracers, self.skeleton, self.joints, self.target_marker]:
            checkbox.toggled.connect(self.update_settings)
        for slider in [self.smoothing, self.vertical, self.max_step, self.confidence, self.fov,
                       self.line_width, self.opacity, self.fill_opacity, self.keypoint_confidence,
                       self.uncertain_threshold]:
            slider.valueChanged.connect(self.update_settings)
        for combo in [self.aim_key, self.toggle]:
            combo.changed.connect(self.update_settings)
        for combo in [self.image_size, self.box_style, self.tracer_origin, self.input_mode]:
            combo.currentIndexChanged.connect(self.update_settings)
        self.title.textChanged.connect(self.update_settings)
        self.profile.activated.connect(self.apply_profile)
        self.monitor.currentIndexChanged.connect(self.update_settings)
        self.tabs.currentChanged.connect(self.refresh_overlay)
        self.status_timer.timeout.connect(self.refresh_overlay)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._persist_settings)
        # Apply persisted values once every control exists and signals are wired.
        self.apply_settings(self.defaults)
        self._loading = False

    def apply_settings(self, config: Settings):
        self._loading = True
        try:
            index = self.monitor.findData(config.monitor)
            if index >= 0:
                self.monitor.setCurrentIndex(index)
            self.title.setText(config.window_title)
            self.model.setText(config.model)
            self.class_id.setValue(config.class_id)
            self.profile.setCurrentIndex(config.profile)
            self.desktop_detection.setChecked(config.desktop_detection)
            self.arm.setChecked(config.aim_enabled)
            index = self.input_mode.findData(config.input_mode)
            if index >= 0:
                self.input_mode.setCurrentIndex(index)
            self.automatic.setChecked(config.automatic)
            self.aim_key.setCode(config.aim_key)
            self.toggle.setCode(config.toggle_key)
            self.smoothing.setValue(int(config.smoothing))
            self.vertical.setValue(int(round(config.vertical * 100)))
            self._sync_region()
            self.max_step.setValue(config.max_step)
            index = self.image_size.findData(config.image_size)
            if index >= 0:
                self.image_size.setCurrentIndex(index)
            self.confidence.setValue(int(round(config.confidence * 100)))
            self.tiled.setChecked(config.tiled)
            self.full_screen.setChecked(config.full_screen)
            self.fov.setValue(config.fov)
            self.fov.setEnabled(not config.full_screen)
            self.uncertain_threshold.setValue(int(round(config.uncertain_threshold * 100)))
            for checkbox, checked in [(self.boxes, config.boxes), (self.labels, config.labels),
                                      (self.circle, config.circle), (self.tracers, config.tracers),
                                      (self.skeleton, config.skeleton), (self.joints, config.joints),
                                      (self.target_marker, config.target_marker),
                                      (self.exclude_self, config.exclude_self)]:
                checkbox.setChecked(checked)
            index = self.box_style.findData(config.box_style)
            if index >= 0:
                self.box_style.setCurrentIndex(index)
            index = self.tracer_origin.findData(config.tracer_origin)
            if index >= 0:
                self.tracer_origin.setCurrentIndex(index)
            self.line_width.setValue(config.line_width)
            self.opacity.setValue(config.opacity)
            self.fill_opacity.setValue(config.fill_opacity)
            self.keypoint_confidence.setValue(int(round(config.keypoint_confidence * 100)))
            for key, button in self.colors.items():
                button.setText(getattr(config, key))
            for name in ("left", "top", "right", "bottom"):
                self.exclusion_bounds[name].setValue(getattr(config, f"exclude_{name}"))
        finally:
            self._loading = False

    def _sync_region(self):
        value = round(self.vertical.value())
        for i in range(self.region.count()):
            if self.region.itemData(i) == value:
                self.region.setCurrentIndex(i)
                self.vertical.setEnabled(False)
                return
        self.region.setCurrentIndex(self.region.count() - 1)
        self.vertical.setEnabled(True)

    def _persist_settings(self):
        if self.persist:
            save_settings(self.settings())

    def choose_color(self, key):
        color = QColorDialog.getColor(QColor(self.colors[key].text()), self, "ESP-Farbe wählen")
        if color.isValid():
            self.colors[key].setText(color.name())
            self.update_settings()

    def apply_profile(self, index):
        if self.worker:
            return
        model, resolution, tiled, confidence = [
            ("yolo11n.pt", 640, False, 20),
            ("yolo11s-pose.pt", 640, False, 25),
            ("yolo11m-pose.pt", 1536, True, 20),
        ][index]
        self._loading = True
        self.skeleton.setChecked(index != 0)
        self.profile.setCurrentIndex(index)
        self.model.setText(model)
        self.class_id.setValue(-1)
        self.image_size.setCurrentIndex(self.image_size.findData(resolution))
        self.tiled.setChecked(tiled)
        self.confidence.setValue(confidence)
        self.full_screen.setChecked(True)
        self._loading = False
        self.update_settings()

    def refresh_overlay(self):
        editing = (self.edit_zone.isChecked() and self.tabs.tabText(self.tabs.currentIndex()) == "Eigenfigur"
                   and self.isActiveWindow() and not self.isMinimized() and self.valid_zone() and not self.closing)
        self.overlay.edit_zone = editing
        self.overlay.settings = self.settings()
        if editing and not self.overlay.isVisible():
            try:
                with mss.mss() as capture:
                    index = self.monitor.currentData()
                    if index is None or not 1 <= index < len(capture.monitors):
                        raise ValueError("Bildschirm nicht verfügbar. Anwendung nach Monitorwechsel neu starten.")
                    monitor = capture.monitors[index]
            except Exception as exc:
                self.edit_zone.setChecked(False)
                self.status.setText(f"Zonenvorschau fehlgeschlagen: {exc}")
                return
            self.overlay.show()
            position_overlay(int(self.overlay.winId()), monitor)
            if not exclude_from_capture(int(self.overlay.winId())):
                self.overlay.hide()
                self.edit_zone.setChecked(False)
                self.status.setText("Zonenvorschau nicht möglich: Windows-Aufnahmeausschluss fehlt.")
                return
        if not self.worker and not editing:
            self.overlay.hide()
        self.overlay.update()

    def change_region(self):
        value = self.region.currentData()
        self.vertical.setEnabled(value is None)
        if value is not None:
            self.vertical.setValue(value)
        self.update_settings()

    def refresh_status_color(self):
        active = self.status.text().startswith("Running")
        if self.status.property("active") != active:
            self.status.setProperty("active", active)
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)
            self.status.update()

    @staticmethod
    def label(text, name):
        label = QLabel(text)
        label.setObjectName(name)
        return label

    @staticmethod
    def group(title):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.setSpacing(10)
        return box, layout

    @staticmethod
    def info(title):
        button = QToolButton()
        button.setText("i")
        button.setObjectName("info")
        button.setFixedSize(22, 22)
        text = HELP[title]
        button.setToolTip(text)
        button.setAccessibleName(f"Information: {title}")
        button.setAccessibleDescription(text)
        button.clicked.connect(lambda: QToolTip.showText(button.mapToGlobal(button.rect().bottomLeft()), text, button))
        return button

    def checkbox(self, layout, control):
        row = QHBoxLayout()
        row.addWidget(control, 1)
        row.addWidget(self.info(control.text()))
        control.setToolTip(HELP[control.text()])
        layout.addLayout(row)

    def field(self, layout, title, control):
        label = QLabel(title)
        label.setBuddy(control)
        control.setAccessibleName(title)
        row = QHBoxLayout()
        row.addWidget(label, 1)
        row.addWidget(self.info(title))
        layout.addLayout(row)
        layout.addWidget(control)

    def slider(self, layout, title, low, high, default, suffix):
        label = QLabel(f"{title}: {default}{suffix}")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(default)
        slider.setAccessibleName(title)
        label.setBuddy(slider)
        slider.valueChanged.connect(lambda value: label.setText(f"{title}: {value}{suffix}"))
        row = QHBoxLayout()
        row.addWidget(label, 1)
        row.addWidget(self.info(title))
        layout.addLayout(row)
        layout.addWidget(slider)
        return slider

    def preview_capture(self):
        try:
            with mss.mss() as capture:
                index = self.monitor.currentData()
                if index is None or not 1 <= index < len(capture.monitors):
                    raise ValueError("Selected display is unavailable. Restart the app after connecting your monitor.")
                frame = capture.grab(capture.monitors[index])
                image = QImage(frame.rgb, frame.width, frame.height, frame.width * 3,
                               QImage.Format.Format_RGB888).copy()
            self.capture_preview.setPixmap(QPixmap.fromImage(image).scaled(
                360, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.status.setText(f"Capture successful · {frame.width} × {frame.height} · Snapshot only; AI detection is separate.")
        except Exception as exc:
            self.capture_preview.clear()
            self.capture_preview.setText(f"Capture failed: {exc}")

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a trusted detection model", "", "PyTorch models (*.pt)")
        if path:
            answer = QMessageBox.warning(self, "Trusted files only", "Model files can execute Python code. Only continue if you created this model or trust its publisher.", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if answer == QMessageBox.StandardButton.Ok:
                self.model.setText(path)

    def settings(self):
        return Settings(monitor=self.monitor.currentData(), profile=self.profile.currentIndex(),
                        model=self.model.text(),
                        class_id=self.class_id.value(), window_title=self.title.text().strip(),
                        confidence=self.confidence.value() / 100, fov=self.fov.value(),
                        smoothing=self.smoothing.value(), vertical=self.vertical.value() / 100,
                        max_step=self.max_step.value(), input_mode=self.input_mode.currentData(),
                        aim_key=self.aim_key.currentData(),
                        toggle_key=self.toggle.currentData(), aim_enabled=self.arm.isChecked(),
                        boxes=self.boxes.isChecked(), labels=self.labels.isChecked(), circle=self.circle.isChecked(),
                        desktop_detection=self.desktop_detection.isChecked(),
                        automatic=self.automatic.isChecked(), image_size=self.image_size.currentData(),
                        exclude_self=self.exclude_self.isChecked(),
                        full_screen=self.full_screen.isChecked(), tiled=self.tiled.isChecked(),
                        box_style=self.box_style.currentData(), tracer_origin=self.tracer_origin.currentData(),
                        tracers=self.tracers.isChecked(), skeleton=self.skeleton.isChecked(),
                        joints=self.joints.isChecked(), target_marker=self.target_marker.isChecked(),
                        line_width=self.line_width.value(), opacity=self.opacity.value(),
                        fill_opacity=self.fill_opacity.value(),
                        keypoint_confidence=self.keypoint_confidence.value() / 100,
                        uncertain_threshold=self.uncertain_threshold.value() / 100,
                        **{key: button.text() for key, button in self.colors.items()},
                        **{f"exclude_{name}": control.value() for name, control in self.exclusion_bounds.items()})

    def valid_zone(self):
        bounds = self.exclusion_bounds
        return (not self.exclude_self.isChecked() or
                (bounds["left"].value() < bounds["right"].value() and
                 bounds["top"].value() < bounds["bottom"].value()))

    def update_settings(self, *_):
        if self._loading:
            return
        if self.persist:
            self._save_timer.start()
        self.fov.setEnabled(not self.full_screen.isChecked())
        self.refresh_overlay()
        if not self.valid_zone():
            if self.worker:
                self.arm.setChecked(False)
                self.worker.configure(self.settings())
            self.status.setText("Ungültige Zone: Links < Rechts und Oben < Unten erforderlich. Mauseingabe deaktiviert.")
            return
        if self.worker:
            self.worker.configure(self.settings())

    def start(self):
        if not self.valid_zone():
            QMessageBox.warning(self, "Ungültige Ausschlusszone", "Links muss kleiner als Rechts sein; Oben kleiner als Unten.")
            return
        for binding in [self.aim_key, self.toggle]:
            binding.cancel()
        if self.aim_key.currentData() == self.toggle.currentData():
            QMessageBox.warning(self, "Hotkey conflict", "Choose different keys for hold-to-aim and pause / resume.")
            return
        if not self.title.text().strip():
            QMessageBox.warning(self, "Target window required", "Enter a nonempty part of your game window title.")
            return
        self.failed = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        for control in [self.class_id, self.profile, self.aim_key, self.toggle, self.preview_button, *self.model_buttons]:
            control.setEnabled(False)
        try:
            with mss.mss() as source:
                index = self.monitor.currentData()
                if index is None or not 1 <= index < len(source.monitors):
                    raise ValueError("Selected display is unavailable.")
                mon = source.monitors[index]
            self.overlay.setGeometry(mon["left"], mon["top"], mon["width"], mon["height"])
        except Exception as exc:
            self.on_failure(str(exc))
            self.finished()
            return
        self.overlay.show()
        if not exclude_from_capture(int(self.overlay.winId())):
            self.overlay.hide()
            self.on_failure("Windows could not exclude the overlay from capture. Session not started; Windows 10 version 2004 or later is required.")
            self.finished()
            return
        exclude_from_capture(int(self.winId()))
        self.worker = Detector(self.settings())
        self.worker.frame.connect(self.receive)
        self.worker.status.connect(self.status.setText)
        self.worker.failed.connect(self.on_failure)
        self.worker.finished.connect(self.finished)
        self.worker.start()

    def receive(self, data):
        if self.worker and not self.closing:
            self.overlay.present(data, self.settings())
            age = data.get("latency_ms")
            latency = f"  ·  Bildalter {age:.0f} ms" if age is not None else ""
            self.status.setText(f"{data['state']}  ·  {data['fps']:.0f} inference FPS  ·  {len(data['boxes'])} detections{latency}")

    def on_failure(self, message):
        self.failed = True
        self.status.setText(f"Session error: {message}")

    def stop(self):
        self.overlay.clear()
        self.edit_zone.setChecked(False)
        if self.worker:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.status.setText("Mauseingabe gestoppt · laufende Modelloperation wird noch beendet…")
        self.overlay.hide()

    def finished(self):
        self.overlay.clear()
        self.overlay.hide()
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        for control in [self.class_id, self.profile, self.aim_key, self.toggle, self.preview_button, *self.model_buttons]:
            control.setEnabled(True)
        if not self.failed:
            self.status.setText("Gestoppt · keine Mauseingabe. Einstellungen bleiben für die nächste Sitzung erhalten.")
        if self.closing:
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.closing = True
            self.stop()
            event.ignore()
        else:
            self._save_timer.stop()
            self._persist_settings()
            self.overlay.close()
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    console = Console()
    console.show()
    sys.exit(app.exec())
