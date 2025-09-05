import configparser
from pathlib import Path
from datetime import datetime
from paths import APPDATA_DIR


CONFIG_PATH = APPDATA_DIR / "config.ini"
LOGFILE_PATH = APPDATA_DIR / "sbu_log.txt"

GAMES = ["Sims 4", "Sims 3", "Sims Medieval", "MySims", "MySims Kingdom"]


def ensure_config():
    if not CONFIG_PATH.exists():
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config["Settings"] = {
            "max_backups": "5",
            "theme": "dark",
            "last_selected_game": "Sims 4",
            "minimize_to_tray": "false",
        }
        for g in GAMES:
            key = game_key(g)
            config[f"Path:{key}"] = {"default_backup_path": ""}
        config["General"] = {
            "update_available": "false",
            "last_installed_version": "1.0.0"
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

def get_config():
    ensure_config()
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH, encoding="utf-8")
    return config

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
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

def get_max_backups():
    return int(get_config_value("Settings", "max_backups", 5))

def save_max_backups(value: int):
    set_config_value("Settings", "max_backups", str(value))

def get_theme_mode():
    return get_config_value("Settings", "theme", "dark")

def save_theme_mode(mode: str):
    set_config_value("Settings", "theme", mode)

def get_minimize_to_tray() -> bool:
    return get_config_value("Settings", "minimize_to_tray", "false").lower() == "true"

def save_minimize_to_tray(flag: bool):
    set_config_value("Settings", "minimize_to_tray", str(flag).lower())

def get_update_available():
    return get_config_value("General", "update_available", "false").lower() == "true"

def set_update_available(flag: bool):
    set_config_value("General", "update_available", str(flag).lower())

def get_last_installed_version():
    return get_config_value("General", "last_installed_version", "1.0.0")

def set_last_installed_version(version: str):
    set_config_value("General", "last_installed_version", version)

def game_key(game_name: str) -> str:
    return game_name.strip().lower().replace(" ", "_")

def get_default_backup_path(game_name: str):
    key = game_key(game_name)
    return get_config_value(f"Path:{key}", "default_backup_path", None)

def save_default_backup_path(game_name: str, path: str):
    key = game_key(game_name)
    set_config_value(f"Path:{key}", "default_backup_path", path)

def get_last_selected_game():
    return get_config_value("Settings", "last_selected_game", "Sims 4")

def save_last_selected_game(game_name: str):
    set_config_value("Settings", "last_selected_game", game_name)

def write_log_file(message: str):
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    today_prefix = now.strftime("[%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"

    existing = []
    if LOGFILE_PATH.exists():
        with open(LOGFILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(today_prefix):
                    existing.append(line.rstrip("\n"))

    existing.append(log_entry)

    with open(LOGFILE_PATH, "w", encoding="utf-8") as f:
        for line in existing:
            f.write(line + "\n")

def get_schedule_config():
    config = get_config()
    if "Schedule" not in config:
        return None
    mode = config["Schedule"].get("mode", "")
    if mode == "interval":
        return {"mode": "interval", "hours": config["Schedule"].getint("hours", 6)}
    elif mode == "daily":
        time_str = config["Schedule"].get("time", "12:00")
        try:
            h, m = map(int, time_str.split(":"))
        except ValueError:
            h, m = 12, 0
        return {"mode": "daily", "time": (h, m)}
    return None

def save_schedule_config(schedule: dict):
    config = get_config()
    if "Schedule" not in config:
        config["Schedule"] = {}
    config["Schedule"]["mode"] = schedule["mode"]
    if schedule["mode"] == "interval":
        config["Schedule"]["hours"] = str(schedule["hours"])
    elif schedule["mode"] == "daily":
        h, m = schedule["time"]
        config["Schedule"]["time"] = f"{h:02d}:{m:02d}"
    save_config(config)

def clear_schedule_config():
    config = get_config()
    if "Schedule" in config:
        config.remove_section("Schedule")
        save_config(config)