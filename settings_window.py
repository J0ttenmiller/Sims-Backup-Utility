from PySide6.QtWidgets import (
    QDialog, QLabel, QSpinBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog
)
from config_utils import (
    get_max_backups, save_max_backups,
    save_default_backup_path, get_default_backup_path,
    save_theme_mode
)


class SettingsWindow(QDialog):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 220)
        self.setStyleSheet(f"background-color: {theme.bg}; color: {theme.fg};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Maximum number of backups to keep:")
        self.max_spinbox = QSpinBox()
        self.max_spinbox.setMinimum(1)
        self.max_spinbox.setMaximum(99)
        self.max_spinbox.setValue(get_max_backups())

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(label)
        hlayout1.addWidget(self.max_spinbox)
        layout.addLayout(hlayout1)

        self.backup_path_label = QLabel(f"Backup folder: {get_default_backup_path() or 'Not set'}")
        layout.addWidget(self.backup_path_label)

        browse_btn = QPushButton("Browse for default backup folder")
        browse_btn.setStyleSheet(self.button_style())
        browse_btn.clicked.connect(self.choose_path)
        layout.addWidget(browse_btn)

        self.theme_btn = QPushButton(f"Switch to {'Light' if self.theme.mode == 'dark' else 'Dark'} Mode")
        self.theme_btn.setStyleSheet(self.button_style())
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self.button_style())
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

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

    def save_settings(self):
        save_max_backups(self.max_spinbox.value())
        QMessageBox.information(self, "Settings Saved", "Settings have been saved.")
        self.accept()