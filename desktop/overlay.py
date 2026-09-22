from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config import Settings
from targeting import exclusion_rect
from vision import skeleton_segments


class Overlay(QWidget):
    def __init__(self, position_window):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.position_window = position_window
        self.settings = Settings()
        self.data = {"boxes": [], "target": None}
        self.visible_frame = False
        self.edit_zone = False
        self._placed = None

    def present(self, data, settings):
        self.data, self.settings = data, settings
        # ESP stays visible whenever the session has detections — status text
        # (e.g. "Bild zu alt") only gates input, not the overlay.
        self.visible_frame = bool(data.get("show_esp", data["state"].startswith("Running")))
        monitor = data.get("monitor")
        place = None if not monitor else (monitor.get("left"), monitor.get("top"),
                                          monitor.get("width"), monitor.get("height"))
        if place is not None and place != self._placed:
            self.position_window(int(self.winId()), monitor)
            self._placed = place
        self.update()

    def clear(self):
        self.data = {"boxes": [], "target": None}
        self.visible_frame = False
        self._placed = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if not self.visible_frame and not self.edit_zone:
            painter.end()
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = self.devicePixelRatioF()
        painter.scale(1 / scale, 1 / scale)
        width, height = self.width() * scale, self.height() * scale
        painter.setOpacity(self.settings.opacity / 100)
        if self.visible_frame:
            self.paint_detections(painter, width, height)
        if self.edit_zone:
            painter.setOpacity(1)
            left, top, right, bottom = exclusion_rect(self.settings, width, height)
            painter.setPen(QPen(QColor("#efb86e"), 2, Qt.PenStyle.DashLine))
            painter.fillRect(QRectF(left, top, right - left, bottom - top), QColor(239, 184, 110, 22))
            painter.drawRect(QRectF(left, top, right - left, bottom - top))
            label = "Eigenzone · Bearbeitung" if self.settings.exclude_self else "Eigenzone · Filter deaktiviert"
            painter.drawText(QPointF(left + 6, top + 20), label)
        painter.end()

    def paint_detections(self, painter, width, height):
        config = self.settings
        if config.circle and not config.full_screen:
            radius = config.fov
            painter.setPen(QPen(QColor(config.box_color), 1))
            painter.drawEllipse(QRectF(width / 2 - radius, height / 2 - radius, radius * 2, radius * 2))
        poses = self.data.get("poses", [])
        names = self.data.get("names", {})
        origin_y = {"top": 0, "center": height / 2, "bottom": height}.get(config.tracer_origin, height)
        for index, box in enumerate(self.data["boxes"]):
            x1, y1, x2, y2, score, class_id = box
            uncertain = score < config.uncertain_threshold
            color = QColor(config.uncertain_color if uncertain else config.box_color)
            rect = QRectF(x1, y1, x2 - x1, y2 - y1)
            if config.tracers:
                painter.setPen(QPen(QColor(config.line_color), config.line_width))
                painter.drawLine(QPointF(width / 2, origin_y), QPointF((x1 + x2) / 2, y2))
            if config.boxes:
                fill = QColor(color)
                fill.setAlphaF(config.fill_opacity / 100)
                painter.fillRect(rect, fill)
                style = Qt.PenStyle.DashLine if uncertain else Qt.PenStyle.SolidLine
                painter.setPen(QPen(color, config.line_width, style))
                if config.box_style == "corners":
                    length = min(rect.width(), rect.height()) * .25
                    for x, sx in ((x1, 1), (x2, -1)):
                        for y, sy in ((y1, 1), (y2, -1)):
                            painter.drawLine(QPointF(x, y), QPointF(x + sx * length, y))
                            painter.drawLine(QPointF(x, y), QPointF(x, y + sy * length))
                else:
                    painter.drawRect(rect)
            if config.skeleton and index < len(poses):
                painter.setPen(QPen(QColor(config.skeleton_color), config.line_width))
                segments = skeleton_segments(poses[index], config.keypoint_confidence)
                for a, b in segments:
                    painter.drawLine(QPointF(a[0], a[1]), QPointF(b[0], b[1]))
                if config.joints:
                    for x, y in {(point[0], point[1]) for segment in segments for point in segment}:
                        painter.drawEllipse(QPointF(x, y), 2.5, 2.5)
            if config.labels:
                name = names.get(int(class_id), str(int(class_id))) if isinstance(names, dict) else str(int(class_id))
                label = f"{'Möglich: ' if uncertain else ''}{name} · {score:.0%}"
                label_width = painter.fontMetrics().horizontalAdvance(label) + 12
                label_x = max(0, min(x1, width - label_width))
                label_y = max(0, y1 - 24)
                painter.fillRect(QRectF(label_x, label_y, label_width, 22), QColor("#11161c"))
                painter.setPen(color)
                painter.drawText(QPointF(label_x + 6, label_y + 16), label)
        target = self.data.get("target")
        if config.target_marker and target:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(QPointF(target[1], target[2]), 4, 4)
