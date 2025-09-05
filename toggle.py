from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QFont


class ToggleSwitch(QWidget):
    def __init__(self, label_text="", theme=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self._checked = False
        self._circle_pos = 3
        self.label_text = label_text
        self.theme = theme

        self.anim = QPropertyAnimation(self, b"circle_pos", self)
        self.anim.setDuration(150)

    def setChecked(self, checked: bool):
        self._checked = checked
        self.anim.stop()
        if checked:
            self.anim.setEndValue(self.width() - 27)
        else:
            self.anim.setEndValue(3)
        self.anim.start()

    def isChecked(self):
        return self._checked

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            self.stateChanged.emit(self._checked)

    def resizeEvent(self, event):
        if self._checked:
            self._circle_pos = self.width() - 27
        else:
            self._circle_pos = 3
        super().resizeEvent(event)

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = Property(int, get_circle_pos, set_circle_pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_rect = QRect(self.width() - 50, 5, 40, 20)

        if self.theme and self.theme.mode == "dark":
            track_off = QColor("#555")
            track_on = QColor("#2e7d32")
            circle = QColor("#ddd")
            text_color = QColor(self.theme.fg)
        else:
            track_off = QColor("#ccc")
            track_on = QColor("#1976d2")
            circle = QColor("#fff")
            text_color = QColor(self.theme.fg if self.theme else "#000")

        painter.setBrush(track_on if self._checked else track_off)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 10, 10)

        painter.setBrush(circle)
        painter.drawEllipse(int(self._circle_pos), 7, 16, 16)

        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(0, 0, self.width() - 60, self.height(),
                         Qt.AlignVCenter | Qt.AlignLeft,
                         self.label_text)

    stateChanged = Signal(bool)