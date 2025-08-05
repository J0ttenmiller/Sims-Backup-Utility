import sys
from pathlib import Path
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QDialog, QMessageBox
)
from PySide6.QtGui import QIcon

from progress_dialog import ProgressDialog
from backup import BackupWorker
from restore import RestoreWorker
from settings_window import SettingsWindow
from config_utils import get_default_backup_path


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
        self.setFixedSize(300, 200)

        self.setWindowIcon(QIcon(str(resource_path("icon.ico"))))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)

        self.backup_btn = QPushButton("Backup")
        self.backup_btn.setIcon(QIcon(str(resource_path("backup_icon.png"))))

        self.restore_btn = QPushButton("Restore")
        self.restore_btn.setIcon(QIcon(str(resource_path("restore_icon.png"))))

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setIcon(QIcon(str(resource_path("settings_icon.png"))))

        buttons = [self.backup_btn, self.restore_btn, self.settings_btn]

        for btn in buttons:
            btn.setIconSize(QtCore.QSize(20, 20))
            btn.setMinimumHeight(45)
            btn.setStyleSheet(self.button_style())
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            layout.addWidget(btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.backup_btn.clicked.connect(self.run_backup)
        self.restore_btn.clicked.connect(self.run_restore)
        self.settings_btn.clicked.connect(self.open_settings)

        self.apply_theme()

    def button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.theme.button_bg};
                color: {self.theme.button_fg};
                font-size: 20px;
                height: 32px;
                border-radius: 6px;
                text-align: center;
                padding: 2px 8px;
            }}
            QPushButton::menu-indicator {{
                image: none;
            }}
            QPushButton:hover {{
                background-color: {self.theme.button_active};
            }}
        """

    def apply_theme(self):
        self.setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")
        self.centralWidget().setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")

        for btn in [self.backup_btn, self.restore_btn, self.settings_btn]:
            btn.setStyleSheet(self.button_style())

    def run_backup(self):
        folder = get_default_backup_path()
        if not folder or not Path(folder).exists():
            folder = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
            if not folder:
                return

        dialog = ProgressDialog("Backup in Progress", self.theme)
        worker = BackupWorker(dialog, folder)
        dialog.worker = worker

        def backup_done():
            QMessageBox.information(self, "Backup Complete", "Your Sims 4 backup has been created successfully.")
            dialog.accept()

        worker.done_signal.connect(backup_done)

        worker.start()
        dialog.exec()

    def run_restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Sims 4 Backup Zip", filter="Zip Files (*.zip)")
        if not path:
            return

        dialog = ProgressDialog("Restore in Progress", self.theme)
        worker = RestoreWorker(dialog, path)
        dialog.worker = worker

        def restore_done():
            QMessageBox.information(self, "Restore Complete", "Your Sims 4 saves have been restored successfully.")
            dialog.accept()

        worker.done_signal.connect(restore_done)

        worker.start()
        dialog.exec()

    def open_settings(self):
        settings = SettingsWindow(self.theme)
        if settings.exec() == QDialog.Accepted:
            self.apply_theme()