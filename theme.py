from config_utils import get_config, CONFIG_PATH

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
            self.bg = "#2d2d2d"
            self.fg = "#ffffff"
            self.button_bg = "#66bb46"
            self.button_fg = "#ffffff"
            self.button_active = "#1b5e20"
            self.text_bg = "#1e1e1e"
            self.text_fg = "#ffffff"
            self.insert_bg = "#ffffff"
        else:
            self.bg = "#f0f0f0"
            self.fg = "#000000"
            self.button_bg = "#299ed9"
            self.button_fg = "#ffffff"
            self.button_active = "#315dab"
            self.text_bg = "#ffffff"
            self.text_fg = "#000000"
            self.insert_bg = "#000000"