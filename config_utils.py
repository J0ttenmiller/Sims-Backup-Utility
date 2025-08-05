import configparser
from pathlib import Path
from datetime import datetime
from paths import APPDATA_DIR

CONFIG_PATH = APPDATA_DIR / "config.ini"
LOGFILE_PATH = APPDATA_DIR / "sims_backup_utility_log.txt"

def get_config():
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config

def get_last_backup_path():
    config = get_config()
    return config.get("Settings", "last_backup_path", fallback=None)

def save_last_backup_path(path: str):
    config = get_config()
    if "Settings" not in config:
        config["Settings"] = {}
    config["Settings"]["last_backup_path"] = path
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

def get_max_backups():
    config = get_config()
    return config.getint("Settings", "max_backups", fallback=5)

def save_max_backups(value: int):
    config = get_config()
    if "Settings" not in config:
        config["Settings"] = {}
    config["Settings"]["max_backups"] = str(value)
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

def get_default_backup_path():
    config = get_config()
    return config.get("Settings", "default_backup_path", fallback=None)

def save_default_backup_path(path: str):
    config = get_config()
    if "Settings" not in config:
        config["Settings"] = {}
    config["Settings"]["default_backup_path"] = path
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

def write_log_file(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    with open(LOGFILE_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def get_theme_mode():
    config = get_config()
    return config.get("Settings", "theme", fallback="dark")

def save_theme_mode(mode: str):
    config = get_config()
    if "Settings" not in config:
        config["Settings"] = {}
    config["Settings"]["theme"] = mode
    with open(CONFIG_PATH, "w") as f:
        config.write(f)