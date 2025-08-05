import platform
import ctypes.wintypes
from pathlib import Path
import os

def get_appdata_folder():
    local_appdata = os.getenv("LOCALAPPDATA")
    app_folder = Path(local_appdata) / "Sims4BackupUtility"
    app_folder.mkdir(parents=True, exist_ok=True)
    return app_folder

APPDATA_DIR = get_appdata_folder()

def get_documents_folder():
    system = platform.system()

    if system == "Windows":
        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        return Path(buf.value)
    elif system in {"Darwin", "Linux"}:
        return Path.home() / "Documents"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

def get_sims4_folder():
    docs = get_documents_folder()
    return docs / "Electronic Arts" / "The Sims 4"