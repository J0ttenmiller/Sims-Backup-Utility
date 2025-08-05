from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QPlainTextEdit, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QSize, QParallelAnimationGroup


class ProgressDialog(QDialog):
    def __init__(self, title, theme):
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
        self.cancel_btn.clicked.connect(self.cancel)
        self.cancel_btn.setStyleSheet(self.button_style())
        layout.addWidget(self.cancel_btn)

        self.toggle_btn = QPushButton("Show Details ▼")
        self.toggle_btn.clicked.connect(self.toggle_details)
        self.toggle_btn.setStyleSheet(self.button_style())
        layout.addWidget(self.toggle_btn)

        self.details_box = QPlainTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setStyleSheet(
            "background-color: #111; color: white;" if theme.mode == "dark"
            else "background-color: #fff; color: black;"
        )
        self.details_box.hide()

        self.details_opacity = QGraphicsOpacityEffect()
        self.details_box.setGraphicsEffect(self.details_opacity)
        self.details_opacity.setOpacity(0)

        self.details_box.setMinimumHeight(200)
        layout.addWidget(self.details_box)
        layout.setStretchFactor(self.details_box, 1)

        self.setLayout(layout)

        self._anim_group = None
        self.worker = None
        self.details_visible = False

        self.details_box.setVisible(False)
        self.setMinimumSize(400, self.sizeHint().height())
        self.resize(400, self.sizeHint().height())

    def get_collapsed_height(self):
        self.details_box.setVisible(False)
        inner = self.sizeHint().height()
        frame_overhead = self.frameGeometry().height() - self.geometry().height()
        self.details_box.setVisible(self.details_visible)
        return inner + frame_overhead

    def get_expanded_height(self):
        self.details_box.setVisible(True)
        inner = self.sizeHint().height()
        frame_overhead = self.frameGeometry().height() - self.geometry().height()
        self.details_box.setVisible(self.details_visible)
        return inner + frame_overhead

    def toggle_details(self):
        self.details_visible = not self.details_visible

        collapsed_height = self.get_collapsed_height()
        expanded_height = self.get_expanded_height()

        target_height = expanded_height if self.details_visible else collapsed_height

        target_height = max(target_height, self.minimumHeight())

        if not self.details_visible:
            self.setMinimumHeight(0)
        else:
            self.setMinimumHeight(collapsed_height)

        if self.details_visible:
            self.details_box.show()

        anim_group = QParallelAnimationGroup()

        anim_resize = QPropertyAnimation(self, b"size")
        anim_resize.setDuration(250)
        anim_resize.setStartValue(QSize(self.width(), max(self.height(), self.minimumHeight())))
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

            def hide_and_restore():
                self.details_box.hide()
                self.setMinimumHeight(collapsed_height)
            anim_group.finished.connect(hide_and_restore)

        anim_group.addAnimation(anim_fade)

        anim_group.start()
        self._anim_group = anim_group

        self.log_label.setVisible(not self.details_visible)

    def progress_bar_style(self):
        if self.theme.mode == "dark":
            return """
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #222;
                }
                QProgressBar::chunk {
                    background-color: #4caf50;
                    width: 20px;
                }
            """
        else:
            return """
                QProgressBar {
                    border: 2px solid #aaa;
                    border-radius: 5px;
                    background-color: #eee;
                }
                QProgressBar::chunk {
                    background-color: #2196f3;
                    width: 20px;
                }
            """

    def button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.theme.button_bg};
                color: {self.theme.button_fg};
                font-weight: bold;
                border-radius: 8px;
                height: 30px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.button_active};
            }}
        """

    def log(self, message):
        self.log_label.setText(message)
        self.details_box.appendPlainText(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        max_val = self.progress_bar.maximum() or 1
        percent = int((value / max_val) * 100)
        self.percent_label.setText(f"{percent}%")

    def set_max(self, value):
        self.progress_bar.setMaximum(value)

    def cancel(self):
        if self.worker:
            self.worker.cancel_requested = True
        self.close()