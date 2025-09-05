import sys
import threading
from pathlib import Path
import requests
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QDialog, QMessageBox, QComboBox, QLabel,
    QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QIcon, QPainter, QColor, QAction

from progress_dialog import ProgressDialog
from backup import BackupWorker
from restore import RestoreWorker
from settings_window import SettingsWindow
from schedule_dialog import ScheduleDialog
from config_utils import (
    get_default_backup_path, save_default_backup_path,
    get_update_available, set_update_available,
    get_last_installed_version,
    get_last_selected_game, save_last_selected_game,
    get_schedule_config, save_schedule_config,
    get_minimize_to_tray
)

GITHUB_USER = "J0ttenmiller"
GITHUB_REPO = "Sims-Backup-Utility"

GAMES = ["Sims 4", "Sims 3", "Sims Medieval", "MySims", "MySims Kingdom"]


def resource_path(relative_path: str) -> Path:
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent
    return base_path / relative_path


class MainWindow(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Sims Backup Utility")
        self.setFixedSize(320, 280)

        self.setWindowIcon(QIcon(str(resource_path("icon.ico"))))
        self.installed_version = get_last_installed_version()
        self.settings_btn_red_dot = False

        self.schedule = None
        self.schedule_timer = QtCore.QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedule)

        self.silent_workers = []

        self.init_ui()
        self.init_tray()

        self.schedule = get_schedule_config()
        if self.schedule:
            self.schedule_timer.start(60000)

        if not get_update_available():
            QtCore.QTimer.singleShot(2000, self.check_updates_silent)

    def init_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel("Game:"))
        self.game_combo = QComboBox()
        self.game_combo.addItems(GAMES)
        last_game = get_last_selected_game()
        if last_game in GAMES:
            self.game_combo.setCurrentText(last_game)
        self.game_combo.currentTextChanged.connect(save_last_selected_game)
        row.addWidget(self.game_combo, 1)
        outer.addLayout(row)

        self.backup_btn = QPushButton("Backup")
        self.backup_btn.setIcon(QIcon(str(resource_path("backup_icon.png"))))
        self.restore_btn = QPushButton("Restore")
        self.restore_btn.setIcon(QIcon(str(resource_path("restore_icon.png"))))
        self.schedule_btn = QPushButton("Schedule")
        self.schedule_btn.setIcon(QIcon(str(resource_path("schedule_icon.png"))))
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setIcon(QIcon(str(resource_path("settings_icon.png"))))

        for btn in (self.backup_btn, self.restore_btn, self.schedule_btn, self.settings_btn):
            btn.setIconSize(QtCore.QSize(20, 20))
            btn.setMinimumHeight(45)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        outer.addWidget(self.backup_btn)
        outer.addWidget(self.restore_btn)
        outer.addWidget(self.schedule_btn)
        outer.addWidget(self.settings_btn)

        container = QWidget()
        container.setLayout(outer)
        self.setCentralWidget(container)

        self.backup_btn.clicked.connect(lambda: self.run_backup(silent=False))
        self.restore_btn.clicked.connect(self.run_restore)
        self.schedule_btn.clicked.connect(self.open_schedule)
        self.settings_btn.clicked.connect(self.open_settings)

        self.apply_theme()

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon(str(resource_path("icon.ico"))), self)
        menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.restore_from_tray)
        menu.addAction(show_action)

        backup_action = QAction("Run Backup Now", self)
        backup_action.triggered.connect(lambda: self.run_backup(silent=True))
        menu.addAction(backup_action)

        sched_action = QAction("Schedule Backup…", self)
        sched_action.triggered.connect(self.open_schedule)
        menu.addAction(sched_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def minimize_to_tray(self):
        self.hide()
        if self.tray:
            self.tray.showMessage(
                "Sims Backup Utility",
                "Running in the background. Right-click the tray icon for options.",
                QSystemTrayIcon.Information,
                4000
            )

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        if get_minimize_to_tray():
            self.minimize_to_tray()
        else:
            QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        if get_minimize_to_tray():
            event.ignore()
            self.minimize_to_tray()
        else:
            event.accept()

    def button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.theme.button_bg};
                color: {self.theme.button_fg};
                font-size: 18px;
                border-radius: 6px;
                text-align: center;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.button_active};
            }}
        """

    def apply_theme(self):
        self.setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")
        self.centralWidget().setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")
        for btn in (self.backup_btn, self.restore_btn, self.schedule_btn, self.settings_btn):
            btn.setStyleSheet(self.button_style())

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.settings_btn_red_dot:
            painter = QPainter(self)
            painter.setBrush(QColor(255, 0, 0))
            painter.setPen(QtCore.Qt.NoPen)
            btn_geom = self.settings_btn.geometry()
            radius = 8
            painter.drawEllipse(btn_geom.right() - radius - 4, btn_geom.top() + 4, radius, radius)

    def show_settings_red_dot(self):
        self.settings_btn_red_dot = True
        self.update()

    def hide_settings_red_dot(self):
        self.settings_btn_red_dot = False
        self.update()

    def check_updates_silent(self):
        def run_check():
            try:
                api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
                r = requests.get(api_url, timeout=5)
                r.raise_for_status()
                latest_version = r.json().get("tag_name", "").lstrip("v")
                if latest_version and latest_version != self.installed_version:
                    set_update_available(True)
                    self.show_settings_red_dot()
            except Exception:
                pass
        threading.Thread(target=run_check, daemon=True).start()

    def run_backup(self, silent=False):
        game = self.game_combo.currentText()
        folder = get_default_backup_path(game)

        if not folder or not Path(folder).exists():
            if silent:
                self.show_tray_notification("Scheduled backup skipped", f"No folder set for {game}")
                print(f"[Scheduled Backup] No folder set for {game}, skipping.")
                return
            folder = QFileDialog.getExistingDirectory(self, f"Select {game} Backup Destination")
            if not folder:
                return
            save_default_backup_path(game, folder)

        if silent:
            worker = BackupWorker(dialog=None, backup_folder=folder, game_name=game, silent=True)
            self.silent_workers.append(worker)
            worker.cleanup_done_signal.connect(
                lambda summary: self.show_tray_notification(f"{game} Backup Complete", summary)
            )
            worker.finished.connect(lambda: self.silent_workers.remove(worker))
            worker.start()
        else:
            dialog = ProgressDialog(f"Backup in Progress — {game}", self.theme)
            worker = BackupWorker(dialog, folder, game, silent=False)
            dialog.worker = worker

            def backup_done():
                QMessageBox.information(self, "Backup Complete", f"Your {game} backup has been created successfully.")
                dialog.accept()

            if hasattr(worker, "cleanup_done_signal"):
                worker.cleanup_done_signal.connect(
                    lambda summary: QMessageBox.information(self, "Cleanup Complete", summary)
                )

            worker.done_signal.connect(backup_done)
            worker.start()
            dialog.exec()

    def run_restore(self):
        game = self.game_combo.currentText()
        path, _ = QFileDialog.getOpenFileName(self, f"Select {game} Backup Zip", filter="Zip Files (*.zip)")
        if not path:
            return

        dialog = ProgressDialog(f"Restore in Progress — {game}", self.theme)
        worker = RestoreWorker(dialog, path, game)
        dialog.worker = worker

        confirm_box_ref = {"box": None}

        def cancel_restore():
            worker.cancel_requested = True
            if confirm_box_ref["box"] is not None and confirm_box_ref["box"].isVisible():
                confirm_box_ref["box"].done(QMessageBox.No)
            dialog.close()

        dialog.cancel_btn.clicked.disconnect()
        dialog.cancel_btn.clicked.connect(cancel_restore)

        def on_confirm_required():
            if worker.cancel_requested:
                return
            msg = (
                "⚠️ This will overwrite your current game data.\n\n"
                "Are you sure you want to continue?"
            )
            confirm_box = QMessageBox(self)
            confirm_box.setWindowTitle("Confirm Restore")
            confirm_box.setText(msg)
            confirm_box.setIcon(QMessageBox.Warning)
            confirm_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm_box_ref["box"] = confirm_box
            reply = confirm_box.exec()
            worker.confirmation_result_signal.emit(reply == QMessageBox.Yes)

        def restore_done():
            QMessageBox.information(self, "Restore Complete", f"Your {game} data has been restored successfully.")
            dialog.accept()

        worker.request_confirmation_signal.connect(on_confirm_required)
        worker.done_signal.connect(restore_done)
        worker.start()
        dialog.exec()

    def open_settings(self):
        settings = SettingsWindow(self.theme, self)
        if settings.exec() == QDialog.Accepted:
            self.apply_theme()
        self.hide_settings_red_dot()

    def open_schedule(self):
        dlg = ScheduleDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.schedule = dlg.get_schedule()
            save_schedule_config(self.schedule)
            self.schedule_timer.start(60000)
            QMessageBox.information(self, "Scheduled", "Backup schedule set successfully.")
            self.hide()

    def check_schedule(self):
        if not self.schedule:
            return
        now = QtCore.QTime.currentTime()

        if self.schedule["mode"] == "interval":
            last = getattr(self, "_last_backup_time", None)
            interval_seconds = self.schedule.get("hours", 0) * 3600
            if not last or last.secsTo(now) >= interval_seconds:
                self._last_backup_time = now
                self.run_backup(silent=True)

        elif self.schedule["mode"] == "daily":
            scheduled_hour, scheduled_minute = self.schedule.get("time", (0, 0))
            if now.hour() == scheduled_hour and now.minute() == scheduled_minute:
                last_day = getattr(self, "_last_backup_day", None)
                today_str = QtCore.QDate.currentDate().toString("yyyyMMdd")
                if last_day != today_str:
                    self._last_backup_day = today_str
                    self.run_backup(silent=True)

    def show_tray_notification(self, title, message):
        if self.tray:
            self.tray.showMessage(title, message, QSystemTrayIcon.Information, 10000)