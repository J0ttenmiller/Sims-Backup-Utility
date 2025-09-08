from PySide6.QtWidgets import (
    QDialog, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QGridLayout
)
from config_utils import (
    get_max_backups, save_max_backups,
    get_default_backup_path, save_default_backup_path,
    save_theme_mode, get_theme_mode,
    get_update_available, set_update_available,
    get_last_installed_version,
    GAMES,
    get_minimize_to_tray, save_minimize_to_tray
)
from updater import check_for_updates_async
from startup import enable_startup, disable_startup, is_startup_enabled
from toggle import ToggleSwitch


class SettingsWindow(QDialog):
    def __init__(self, theme, main_window=None):
        super().__init__()
        self.theme = theme
        self.main_window = main_window
        self.setWindowTitle("Settings")
        self.setFixedSize(460, 420)
        self.setStyleSheet(f"background-color: {theme.bg}; color: {theme.fg};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(8)

        self.startup_toggle = ToggleSwitch("Run at Startup", theme=self.theme)
        self.startup_toggle.setChecked(is_startup_enabled())
        self.startup_toggle.stateChanged.connect(self.toggle_startup)
        layout.addWidget(self.startup_toggle)

        self.tray_toggle = ToggleSwitch("Minimize to tray on close", theme=self.theme)
        self.tray_toggle.setChecked(get_minimize_to_tray())
        self.tray_toggle.stateChanged.connect(lambda checked: save_minimize_to_tray(checked))
        layout.addWidget(self.tray_toggle)

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
        layout.addLayout(l1)

        self.version_label = QLabel(f"Current Version: {get_last_installed_version()}")
        self.version_label.setStyleSheet("font-size: 13px; margin: 0;")
        layout.addWidget(self.version_label)

        layout.addWidget(QLabel("Per-game default backup folders:"))
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
        layout.addLayout(grid)

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
            bg = "#66bb46"
            hover = "#1b5e20"
        else:
            bg = "#299ed9"
            hover = "#315dab"
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

    def toggle_startup(self, checked: bool):
        if checked:
            enable_startup()
        else:
            disable_startup()

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
            self.update_btn.setStyleSheet("""
                QPushButton { background-color: #ff9800; color: white; border-radius: 8px; height: 30px; }
                QPushButton:hover { background-color: #f57c00; }
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
        save_max_backups(0 if val == "Unlimited" else int(val))
        save_minimize_to_tray(self.tray_toggle.isChecked())
        QMessageBox.information(self, "Settings Saved", "Settings have been saved.")
        self.accept()