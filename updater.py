import sys
import os
import tempfile
import requests
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox
from config_utils import (
    set_last_installed_version,
    set_update_available,
    get_last_installed_version
)


GITHUB_USER = "J0ttenmiller"
GITHUB_REPO = "Sims-Backup-Utility"
INSTALLER_FILENAME = "SimsBackupUtilityInstaller.exe"


class UpdateChecker(QThread):
    update_result = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
            r = requests.get(api_url, timeout=10)
            r.raise_for_status()
            data = r.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            current_version = get_last_installed_version() or "0.0.0"
            self.update_result.emit({
                "data": data,
                "latest_version": latest_version,
                "current_version": current_version
            })
        except Exception as e:
            self.error_signal.emit(str(e))


def install_update(parent, data, latest_version):
    current_version = get_last_installed_version() or "0.0.0"

    if latest_version == current_version:
        QMessageBox.information(parent, "No Updates", "You already have the latest version.")
        return

    reply = QMessageBox.question(
        parent,
        "Update Available",
        f"A new version ({latest_version}) is available.\n"
        f"You have {current_version}.\n\nWould you like to update now?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply != QMessageBox.Yes:
        return

    asset_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == INSTALLER_FILENAME:
            asset_url = asset.get("browser_download_url")
            break

    if not asset_url:
        QMessageBox.warning(parent, "Error", "Installer not found in latest GitHub release.")
        return

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, INSTALLER_FILENAME)

    try:
        with requests.get(asset_url, stream=True) as download:
            download.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in download.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        QMessageBox.warning(parent, "Download Error", str(e))
        return

    set_last_installed_version(latest_version)
    set_update_available(False)
    os.startfile(installer_path)

    if parent:
        parent.close()
    sys.exit()

def check_for_updates_async(parent=None, finished_callback=None):
    checker = UpdateChecker(parent)

    def handle_result(result):
        install_update(parent, result["data"], result["latest_version"])
        if finished_callback:
            finished_callback()

    def handle_error(err):
        QMessageBox.warning(parent, "Update Error", f"Could not check for updates:\n{err}")
        if finished_callback:
            finished_callback()

    checker.update_result.connect(handle_result)
    checker.error_signal.connect(handle_error)
    checker.finished.connect(checker.deleteLater)
    checker.start()