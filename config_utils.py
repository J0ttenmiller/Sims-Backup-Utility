import configparser
from pathlib import Path
from datetime import datetime
from paths import APPDATA_DIR

CONFIG_PATH = APPDATA_DIR / "config.ini"
LOGFILE_PATH = APPDATA_DIR / "sims_backup_utility_log.txt"


def ensure_config():
    if not CONFIG_PATH.exists():
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config["Settings"] = {
            "last_backup_path": "",
            "default_backup_path": "",
            "max_backups": "5",
            "theme": "dark"
        }
        config["General"] = {
            "update_available": "false",
            "last_installed_version": "1.0.0"
        }
        with open(CONFIG_PATH, "w") as f:
            config.write(f)

def get_config():
    ensure_config()
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        config.write(f)

def get_config_value(section, key, default=""):
    config = get_config()
    return config.get(section, key, fallback=default)

def set_config_value(section, key, value):
    config = get_config()
    if section not in config:
        config[section] = {}
    config[section][key] = str(value)
    save_config(config)

def get_last_backup_path():
    return get_config_value("Settings", "last_backup_path", None)

def save_last_backup_path(path: str):
    set_config_value("Settings", "last_backup_path", path)

def get_max_backups():
    return int(get_config_value("Settings", "max_backups", 5))

def save_max_backups(value: int):
    set_config_value("Settings", "max_backups", str(value))

def get_default_backup_path():
    return get_config_value("Settings", "default_backup_path", None)

def save_default_backup_path(path: str):
    set_config_value("Settings", "default_backup_path", path)

def get_theme_mode():
    return get_config_value("Settings", "theme", "dark")

def save_theme_mode(mode: str):
    set_config_value("Settings", "theme", mode)

def write_log_file(message: str):
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)

    today_prefix = datetime.now().strftime("[%Y-%m-%d")

    if LOGFILE_PATH.exists():
        with open(LOGFILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        lines = [line for line in lines if line.startswith(today_prefix)]
        with open(LOGFILE_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)

    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOGFILE_PATH, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}] {message}\n")

# --- Version and update availability helpers ---

def get_update_available() -> bool:
    val = get_config_value("General", "update_available", "false")
    return val.lower() == "true"

def set_update_available(flag: bool):
    set_config_value("General", "update_available", str(flag).lower())

def get_last_installed_version() -> str:
    return get_config_value("General", "last_installed_version", "1.0.0")

def set_last_installed_version(version: str):
    set_config_value("General", "last_installed_version", version)
