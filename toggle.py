from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QFont


class ToggleSwitch(QWidget):
    stateChanged = Signal(bool)

    def __init__(self, label_text="", theme=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._checked = False
        self._circle_pos = 0
        self.label_text = label_text
        self.theme = theme

        self.track_width = 40
        self.track_height = 20
        self.knob_diameter = 16
        self.padding = 8

        self.anim = QPropertyAnimation(self, b"circle_pos", self)
        self.anim.setDuration(180)

    def setChecked(self, checked: bool):
        self._checked = checked
        self.anim.stop()

        track_x = self.width() - self.track_width - self.padding
        if checked:
            end_val = track_x + (self.track_width - self.knob_diameter - 2)
        else:
            end_val = track_x + 2

        self._circle_pos = end_val
        self.update()

        self.anim.setStartValue(self._circle_pos)
        self.anim.setEndValue(end_val)
        if self.isVisible():
            self.anim.start()

    def isChecked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            self.stateChanged.emit(self._checked)

    def resizeEvent(self, event):
        track_x = self.width() - self.track_width - self.padding
        if self._checked:
            self._circle_pos = track_x + (self.track_width - self.knob_diameter - 2)
        else:
            self._circle_pos = track_x + 2
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

        track_x = self.width() - self.track_width - self.padding
        track_y = (self.height() - self.track_height) // 2
        track_rect = QRect(track_x, track_y, self.track_width, self.track_height)

        if self.theme and self.theme.mode == "dark":
            track_off = QColor("#555")
            track_on = QColor("#2e7d32")
            knob = QColor("#ddd")
            text_color = QColor(self.theme.fg)
        else:
            track_off = QColor("#ccc")
            track_on = QColor("#1976d2")
            knob = QColor("#fff")
            text_color = QColor(self.theme.fg if self.theme else "#000")

        painter.setBrush(track_on if self._checked else track_off)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 10, 10)

        knob_y = track_y + (self.track_height - self.knob_diameter) // 2
        painter.setBrush(knob)
        painter.drawEllipse(int(self._circle_pos), knob_y, self.knob_diameter, self.knob_diameter)

        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(0, 0, self.width() - self.track_width - 2 * self.padding,
                         self.height(), Qt.AlignVCenter | Qt.AlignLeft, self.label_text)