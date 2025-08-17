import os
from pathlib import Path

APPDATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SimsBackupUtility"


def get_documents_dirs():
    dirs = []
    home = Path.home()
    docs = home / "Documents"
    if docs.exists():
        dirs.append(docs)

    onedrive = os.getenv("OneDrive")
    if onedrive:
        od_docs = Path(onedrive) / "Documents"
        if od_docs.exists():
            dirs.append(od_docs)

    od_consumer = home / "OneDrive" / "Documents"
    if od_consumer.exists() and od_consumer not in dirs:
        dirs.append(od_consumer)

    out = []
    for d in dirs:
        if d not in out:
            out.append(d)
    return out


def _try_candidates(subpaths):
    for base in get_documents_dirs():
        for sub in subpaths:
            candidate = base / sub
            if candidate.exists():
                return candidate
    bases = get_documents_dirs()
    if bases:
        return bases[0] / subpaths[0]
    return Path.home() / "Documents" / subpaths[0]


def get_sims4_folder():
    return _try_candidates([
        Path("Electronic Arts") / "The Sims 4",
        Path("The Sims 4"),
    ])


def get_sims3_folder():
    return _try_candidates([
        Path("Electronic Arts") / "The Sims 3",
        Path("The Sims 3"),
    ])


def get_sims_medieval_folder():
    return _try_candidates([
        Path("Electronic Arts") / "The Sims Medieval",
        Path("The Sims Medieval"),
    ])


def get_mysims_folder():
    return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Electronic Arts" / "MySims"


def get_mysims_kingdom_folder():
    return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Electronic Arts" / "MySims Kingdom"


def get_game_folder(game_name: str) -> Path:
    g = game_name.strip().lower()
    if g == "sims 4":
        return get_sims4_folder()
    if g == "sims 3":
        return get_sims3_folder()
    if g == "sims medieval":
        return get_sims_medieval_folder()
    if g == "mysims":
        return get_mysims_folder()
    if g == "mysims kingdom":
        return get_mysims_kingdom_folder()
    return get_sims4_folder()