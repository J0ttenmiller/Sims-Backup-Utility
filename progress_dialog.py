from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QPlainTextEdit, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QSize, QParallelAnimationGroup
from theme import Theme


class ProgressDialog(QDialog):
    def __init__(self, title, theme: Theme):
        super().__init__()
        self.setWindowTitle(title)
        self.theme = theme
        self.setStyleSheet(f"background-color: {theme.bg}; color: {theme.fg};")

        layout = QVBoxLayout()

        self.log_label = QLabel("")
        self.log_label.setWordWrap(True)
        layout.addWidget(self.log_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet(self.progress_bar_style())
        layout.addWidget(self.progress_bar)

        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.percent_label)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(self.theme.button_style())
        self.cancel_btn.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_btn)

        self.toggle_btn = QPushButton("Show Details ▼")
        self.toggle_btn.setStyleSheet(self.theme.button_style())
        self.toggle_btn.clicked.connect(self.toggle_details)
        layout.addWidget(self.toggle_btn)

        self.details_box = QPlainTextEdit(readOnly=True)
        self.details_box.setStyleSheet(
            f"background-color: {theme.text_bg}; color: {theme.text_fg};"
        )
        self.details_box.setMinimumHeight(200)
        self.details_box.hide()

        self.details_opacity = QGraphicsOpacityEffect(self.details_box)
        self.details_box.setGraphicsEffect(self.details_opacity)
        self.details_opacity.setOpacity(0)

        layout.addWidget(self.details_box)
        layout.setStretchFactor(self.details_box, 1)

        self.setLayout(layout)
        self.worker = None
        self.details_visible = False
        self._anim_group = None
        self._last_log_message = None

        self.setMinimumSize(400, self.sizeHint().height())
        self.resize(400, self.sizeHint().height())

    def _calc_height_with_details(self, visible: bool) -> int:
        self.details_box.setVisible(visible)
        inner = self.sizeHint().height()
        frame_overhead = self.frameGeometry().height() - self.geometry().height()
        self.details_box.setVisible(self.details_visible)
        return inner + frame_overhead

    def toggle_details(self):
        self.details_visible = not self.details_visible
        collapsed_height = self._calc_height_with_details(False)
        expanded_height = self._calc_height_with_details(True)
        target_height = expanded_height if self.details_visible else collapsed_height
        target_height = max(target_height, self.minimumHeight())

        if not self.details_visible:
            self.setMinimumHeight(0)
        else:
            self.setMinimumHeight(collapsed_height)

        if self.details_visible:
            self.details_box.show()

        if self._anim_group:
            self._anim_group.stop()

        anim_group = QParallelAnimationGroup(self)

        anim_resize = QPropertyAnimation(self, b"size")
        anim_resize.setDuration(250)
        anim_resize.setStartValue(QSize(self.width(), self.height()))
        anim_resize.setEndValue(QSize(self.width(), target_height))
        anim_group.addAnimation(anim_resize)

        anim_fade = QPropertyAnimation(self.details_opacity, b"opacity")
        anim_fade.setDuration(250)
        if self.details_visible:
            anim_fade.setStartValue(0)
            anim_fade.setEndValue(1)
            self.toggle_btn.setText("Hide Details ▲")
        else:
            anim_fade.setStartValue(1)
            anim_fade.setEndValue(0)
            self.toggle_btn.setText("Show Details ▼")
            anim_group.finished.connect(lambda: self.details_box.hide())

        anim_group.addAnimation(anim_fade)
        anim_group.start()
        self._anim_group = anim_group
        self.log_label.setVisible(not self.details_visible)

    def progress_bar_style(self):
        if self.theme.mode == "dark":
            bg_color = self.theme.text_bg
            chunk_color = self.theme.highlight
            border_color = "#555"
        else:
            bg_color = self.theme.text_bg
            chunk_color = self.theme.highlight
            border_color = "#aaa"

        return f"""
            QProgressBar {{
                border: 2px solid {border_color};
                border-radius: 5px;
                background-color: {bg_color};
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                width: 20px;
            }}
        """

    def log(self, message: str):
        if message != self._last_log_message:
            self.log_label.setText(message)
            self.details_box.appendPlainText(message)
            self._last_log_message = message

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        max_val = self.progress_bar.maximum() or 1
        percent = int((value / max_val) * 100)
        self.percent_label.setText(f"{percent}%")

    def set_max(self, value: int):
        self.progress_bar.setMaximum(value)

    def cancel(self):
        if self.worker and hasattr(self.worker, "request_cancel"):
            self.worker.request_cancel()
        elif self.worker:
            self.worker.cancel_requested = True
        self.close()