from PySide6.QtCore import Qt, QTimer, QVariantAnimation, QEasingCurve, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QPushButton

from engine import held


KEYS = {1: 'Left mouse', 2: 'Right mouse', 4: 'Middle mouse', 5: 'Mouse side 1',
        6: 'Mouse side 2', 9: 'Tab', 13: 'Enter', 32: 'Space',
        33: 'Page Up', 34: 'Page Down', 35: 'End', 36: 'Home',
        37: 'Left', 38: 'Up', 39: 'Right', 40: 'Down', 45: 'Insert', 46: 'Delete',
        160: 'Left Shift', 161: 'Right Shift', 162: 'Left Ctrl', 163: 'Right Ctrl',
        164: 'Left Alt', 165: 'Right Alt'}
KEYS.update({key: chr(key) for key in range(48, 58)})
KEYS.update({key: chr(key) for key in range(65, 91)})
KEYS.update({key: f'F{key - 111}' for key in range(112, 136) if key != 119})
KEYS.update({key: f'Numpad {key - 96}' for key in range(96, 106)})


class HotkeyButton(QPushButton):
    changed = Signal()

    def __init__(self, code):
        super().__init__()
        self.code = code
        self.listening = False
        self.ready = False
        self.ticks = 0
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)
        self.clicked.connect(self.record)
        self.refresh()
        self.setToolTip('Click, release all keys, then press a keyboard key or mouse button. Single-key bindings; Escape cancels. F8 is reserved.')

    def currentData(self):
        return self.code

    def setCode(self, code):
        self.code = int(code)
        self.cancel()
        self.refresh()

    def refresh(self):
        self.setText(f'{KEYS.get(self.code, str(self.code))}  ·  Click to rebind')

    def record(self):
        self.listening = True
        self.ready = False
        self.ticks = 0
        self.setText('Release keys, then press your hotkey…')
        self.timer.start()

    def cancel(self):
        self.timer.stop()
        self.listening = False
        self.refresh()

    def poll(self):
        self.ticks += 1
        if held(27) or self.ticks > 400:
            self.cancel()
            return
        down = [key for key in KEYS if held(key)]
        if not self.ready:
            self.ready = not down
            return
        if held(119):
            self.setText('F8 is reserved · choose another key')
            return
        if down:
            self.code = down[0]
            self.cancel()
            self.changed.emit()


class AccentCheckBox(QCheckBox):
    def __init__(self, text):
        super().__init__(text)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.color = QColor('#19212a')
        self.animation.valueChanged.connect(self.paint_color)
        self.toggled.connect(self.transition)

    def transition(self, checked):
        self.animation.stop()
        self.animation.setStartValue(self.color)
        self.animation.setEndValue(QColor('#164a43' if checked else '#19212a'))
        self.animation.start()

    def paint_color(self, color):
        self.color = color
        self.setStyleSheet(f'QCheckBox {{ background: {color.name()}; border-radius: 6px; padding: 8px; }}')
