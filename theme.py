from config_utils import get_config, CONFIG_PATH
from PySide6.QtWidgets import QComboBox

class Theme:
    def __init__(self, mode=None):
        self.mode = mode or self.load_theme()
        self.update()

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        self.save_theme()
        self.update()

    def load_theme(self):
        config = get_config()
        return config.get("Settings", "theme", fallback="dark")

    def save_theme(self):
        config = get_config()
        if "Settings" not in config:
            config["Settings"] = {}
        config["Settings"]["theme"] = self.mode
        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    def update(self):
        if self.mode == "dark":
            self.bg = "#000000"
            self.fg = "#ffffff"
            self.button_bg = "#66bb46"
            self.button_fg = "#ffffff"
            self.button_active = "#1b5e20"
            self.text_bg = "#1e1e1e"
            self.text_fg = "#ffffff"
            self.insert_bg = "#ffffff"
            self.highlight = "#66bb46"
        else:
            self.bg = "#f0f0f0"
            self.fg = "#000000"
            self.button_bg = "#299ed9"
            self.button_fg = "#ffffff"
            self.button_active = "#315dab"
            self.text_bg = "#ffffff"
            self.text_fg = "#000000"
            self.insert_bg = "#000000"
            self.highlight = "#299ed9"

    def button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.button_bg};
                color: {self.button_fg};
                font-weight: bold;
                border-radius: 8px;
                height: 30px;
            }}
            QPushButton:hover {{
                background-color: {self.button_active};
            }}
        """

    def apply_combo_scrollbar_style(self, combo: QComboBox):
        hl_color = self.highlight
        fg_color = self.fg
        bg_color = self.bg
        combo.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                border: 1px solid #d0d0d0;
                selection-background-color: {hl_color};
                selection-color: white;
                background-color: {bg_color};
                color: {fg_color};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
            }}
            QComboBox QAbstractItemView QScrollBar:vertical {{
                border: none;
                width: 10px;
                margin: 0px;
                background: none;
            }}
            QComboBox QAbstractItemView QScrollBar::groove:vertical {{
                background: {bg_color};
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView QScrollBar::handle:vertical {{
                background: {hl_color};
                min-height: 20px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def apply_scrollbar_style(self, widget):
        hl_color = self.highlight
        fg_color = self.fg
        bg_color = self.bg
        widget.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {bg_color};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {hl_color};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {bg_color};
                height: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {hl_color};
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)