from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QRadioButton, QButtonGroup,
    QSpinBox, QTimeEdit
)
from PySide6 import QtCore
from config_utils import get_schedule_config


class ScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule Backup")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        self.interval_radio = QRadioButton("Interval (every X hours)")
        self.daily_radio = QRadioButton("Daily at fixed time")

        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.interval_radio)
        self.radio_group.addButton(self.daily_radio)

        layout.addWidget(self.interval_radio)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 72)
        self.interval_spin.setValue(6)
        layout.addWidget(self.interval_spin)

        layout.addWidget(self.daily_radio)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QtCore.QTime.currentTime())
        layout.addWidget(self.time_edit)

        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        sched = get_schedule_config()
        if sched:
            if sched["mode"] == "interval":
                self.interval_radio.setChecked(True)
                self.interval_spin.setValue(sched["hours"])
            elif sched["mode"] == "daily":
                self.daily_radio.setChecked(True)
                h, m = sched["time"]
                self.time_edit.setTime(QtCore.QTime(h, m))

    def get_schedule(self):
        if self.interval_radio.isChecked():
            return {"mode": "interval", "hours": self.interval_spin.value()}
        else:
            t = self.time_edit.time()
            return {"mode": "daily", "time": (t.hour(), t.minute())}