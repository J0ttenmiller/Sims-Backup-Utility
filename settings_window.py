from PySide6.QtWidgets import ( 
    QDialog, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QGridLayout
)
from updater import check_for_updates_async
from config_utils import (
    get_max_backups, save_max_backups,
    get_default_backup_path, save_default_backup_path,
    save_theme_mode, get_theme_mode,
    get_update_available, set_update_available,
    get_last_installed_version,
    GAMES
)


class SettingsWindow(QDialog):
    def __init__(self, theme, main_window=None):
        super().__init__()
        self.theme = theme
        self.main_window = main_window
        self.setWindowTitle("Settings")
        self.setFixedSize(460, 360)
        self.setStyleSheet(f"background-color: {theme.bg}; color: {theme.fg};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(8)

        top = QVBoxLayout()
        top.setSpacing(2)

        l1 = QHBoxLayout()
        l1.setSpacing(8)
        lbl = QLabel("Maximum number of backups to keep:")
        lbl.setStyleSheet("margin: 0;")
        self.max_combo = QComboBox()
        self.max_combo.addItems(["Unlimited"] + [str(i) for i in range(1, 100)])
        current = get_max_backups()
        self.max_combo.setCurrentText("Unlimited" if current == 0 else str(current))
        l1.addWidget(lbl)
        l1.addWidget(self.max_combo, 1)
        top.addLayout(l1)

        self.version_label = QLabel(f"Current Version: {get_last_installed_version()}")
        self.version_label.setStyleSheet("font-size: 13px; margin: 0;")
        top.addWidget(self.version_label)

        top.addWidget(QLabel("Per-game default backup folders:"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        self.path_labels = {}
        row = 0
        for g in GAMES:
            lab = QLabel(g + ":")
            lab.setStyleSheet("margin: 0;")
            grid.addWidget(lab, row, 0)

            p = get_default_backup_path(g) or "Not set"
            path_label = QLabel(p)
            path_label.setStyleSheet("margin: 0;")
            grid.addWidget(path_label, row, 1)
            self.path_labels[g] = path_label

            btn = QPushButton("Browse")
            btn.setStyleSheet(self.button_style())
            btn.clicked.connect(lambda _, game=g: self.choose_path(game))
            grid.addWidget(btn, row, 2)
            row += 1

        top.addLayout(grid)
        layout.addLayout(top)

        self.theme_btn = QPushButton(f"Switch to {'Light' if self.theme.mode == 'dark' else 'Dark'} Mode")
        self.theme_btn.setStyleSheet(self.button_style())
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.update_btn = QPushButton()
        self.update_btn.clicked.connect(self.run_update_check)
        row2.addWidget(self.update_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self.button_style())
        save_btn.clicked.connect(self.save_settings)
        row2.addWidget(save_btn)

        layout.addLayout(row2)

        self.setLayout(layout)
        self.refresh_update_status()

    def button_style(self):
        if self.theme.mode == "dark":
            bg = "#2e7d32"
            hover = "#1b5e20"
        else:
            bg = "#1976d2"
            hover = "#115293"
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

    def choose_path(self, game_name: str):
        folder = QFileDialog.getExistingDirectory(self, f"Select Default Backup Folder for {game_name}")
        if folder:
            save_default_backup_path(game_name, folder)
            self.path_labels[game_name].setText(folder)

    def toggle_theme(self):
        self.theme.toggle()
        save_theme_mode(self.theme.mode)
        self.setStyleSheet(f"background-color: {self.theme.bg}; color: {self.theme.fg};")
        self.theme_btn.setStyleSheet(self.button_style())
        self.theme_btn.setText(f"Switch to {'Light' if self.theme.mode == 'dark' else 'Dark'} Mode")
        self.refresh_update_status()

    def refresh_update_status(self):
        if get_update_available():
            self.update_btn.setText("Update Available!")
            if self.theme.mode == "dark":
                self.update_btn.setStyleSheet("""
                    QPushButton { background-color: #ff9800; color: white; border-radius: 8px; height: 30px; }
                    QPushButton:hover { background-color: #f57c00; }
                """)
            else:
                self.update_btn.setStyleSheet("""
                    QPushButton { background-color: #ff9800; color: white; border-radius: 8px; height: 30px; }
                    QPushButton:hover { background-color: #ef6c00; }
                """)
        else:
            self.update_btn.setText("Check for Updates")
            self.update_btn.setStyleSheet(self.button_style())

    def run_update_check(self):
        def finished():
            self.version_label.setText(f"Current Version: {get_last_installed_version()}")
            self.refresh_update_status()
            if self.main_window:
                if get_update_available():
                    self.main_window.show_settings_red_dot()
                else:
                    self.main_window.hide_settings_red_dot()

        check_for_updates_async(self, finished_callback=finished)
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