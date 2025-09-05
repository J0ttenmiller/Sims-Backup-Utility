import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SimsBackupUtility"


def get_exe_path() -> str:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable)
    else:
        exe_path = Path(__file__).parent / "SimsBackupUtility.exe"
    return str(exe_path.resolve())


def enable_startup():
    exe_path_str = get_exe_path()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path_str}" --minimized')

def disable_startup():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass

def is_startup_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            _, _ = winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False