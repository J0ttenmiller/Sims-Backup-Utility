from PySide6.QtWidgets import (
    QDialog, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog
)
from updater import check_for_updates_async
from config_utils import (
    get_max_backups, save_max_backups,
    save_default_backup_path, get_default_backup_path,
    save_theme_mode,
    get_update_available, set_update_available,
    get_last_installed_version
)


class SettingsWindow(QDialog):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 260)
        self.setStyleSheet(f"background-color: {theme.bg}; color: {theme.fg};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(6)

        label = QLabel("Maximum number of backups to keep:")
        label.setStyleSheet("margin-bottom: 2px;")
        self.max_combo = QComboBox()
        self.max_combo.addItems(["Unlimited"] + [str(i) for i in range(1, 100)])

        current = get_max_backups()
        if current == 0:
            self.max_combo.setCurrentText("Unlimited")
        else:
            self.max_combo.setCurrentText(str(current))

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(label)
        hlayout1.addWidget(self.max_combo)
        layout.addLayout(hlayout1)

        self.version_label = QLabel()
        self.version_label.setStyleSheet("font-size: 14px; margin-top: 4px; margin-bottom: 2px;")
        layout.addWidget(self.version_label)

        self.backup_path_label = QLabel(f"Backup folder: {get_default_backup_path() or 'Not set'}")
        self.backup_path_label.setStyleSheet("margin-bottom: 4px;")
        layout.addWidget(self.backup_path_label)

        browse_btn = QPushButton("Browse for default backup folder")
        browse_btn.setStyleSheet(self.button_style())
        browse_btn.clicked.connect(self.choose_path)
        layout.addWidget(browse_btn)

        self.theme_btn = QPushButton(f"Switch to {'Light' if self.theme.mode == 'dark' else 'Dark'} Mode")
        self.theme_btn.setStyleSheet(self.button_style())
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        hlayout2 = QHBoxLayout()
        self.update_btn = QPushButton()
        self.update_btn.clicked.connect(self.run_update_check)
        hlayout2.addWidget(self.update_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self.button_style())
        save_btn.clicked.connect(self.save_settings)
        hlayout2.addWidget(save_btn)
        layout.addLayout(hlayout2)

        self.setLayout(layout)
        self.refresh_update_status()

    def button_style(self):
        """Blue in light mode, green in dark mode."""
        if self.theme.mode == "light":
            bg = "#2196F3"
            hover = "#1976D2"
        else:
            bg = "#4CAF50"
            hover = "#388E3C"

        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                font-weight: bold;
                border-radius: 8px;
                height: 30px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """

    def choose_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Backup Folder")
        if folder:
            save_default_backup_path(folder)
            self.backup_path_label.setText(f"Backup folder: {folder}")

    def toggle_theme(self):
        self.theme.toggle()
        save_theme_mode(self.theme.mode)
        self.setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")
        self.theme_btn.setText(f"Switch to {'Light' if self.theme.mode == 'dark' else 'Dark'} Mode")
        self.refresh_update_status()

    def refresh_update_status(self):
        current_version = get_last_installed_version()
        self.version_label.setText(f"Current Version: {current_version}")

        if get_update_available():
            self.update_btn.setText("Update Available!")
            self.update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    font-size: 14px;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
        else:
            self.update_btn.setText("Check for Updates")
            self.update_btn.setStyleSheet(self.button_style())

    def run_update_check(self):
        check_for_updates_async(self, callback=self.refresh_update_status)
        set_update_available(False)
        self.refresh_update_status()

    def save_settings(self):
        val = self.max_combo.currentText()
        if val == "Unlimited":
            save_max_backups(0)
        else:
            save_max_backups(int(val))
        QMessageBox.information(self, "Settings Saved", "Settings have been saved.")
        self.accept()