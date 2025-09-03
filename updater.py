import sys
import os
import tempfile
import requests
from packaging.version import Version, InvalidVersion
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication

from config_utils import (
    set_last_installed_version,
    set_update_available,
    get_last_installed_version
)

GITHUB_USER = "J0ttenmiller"
GITHUB_REPO = "Sims-Backup-Utility"
INSTALLER_FILENAME = "SimsBackupUtilityInstaller.exe"

_running_threads = []


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
    try:
        latest_v = Version(latest_version)
        current_v = Version(current_version)
    except InvalidVersion:
        latest_v = latest_version
        current_v = current_version

    if latest_v <= current_v:
        QMessageBox.information(parent, "No Updates", "You already have the latest version.")
        set_update_available(False)
        if hasattr(parent, "hide_update_indicator"):
            parent.hide_update_indicator()
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

    progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, parent)
    progress.setWindowTitle("Downloading Update")
    progress.setWindowModality(Qt.WindowModal)
    progress.show()

    try:
        with requests.get(asset_url, stream=True) as download:
            download.raise_for_status()
            total = int(download.headers.get("content-length", 0))
            downloaded = 0
            with open(installer_path, "wb") as f:
                for chunk in download.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = int(downloaded * 100 / total)
                        progress.setValue(percent)
                        QApplication.processEvents()
                    if progress.wasCanceled():
                        progress.close()
                        return
        progress.setValue(100)
        progress.close()
    except Exception as e:
        progress.close()
        QMessageBox.warning(parent, "Download Error", str(e))
        return

    set_update_available(False)
    if hasattr(parent, "hide_update_indicator"):
        parent.hide_update_indicator()

    os.startfile(installer_path)
    if parent:
        parent.close()
    sys.exit()


def check_for_updates_async(parent=None, finished_callback=None, silent=False):
    checker = UpdateChecker(parent)
    _running_threads.append(checker)

    def handle_result(result):
        latest_version = result["latest_version"]
        current_version = result["current_version"]

        try:
            latest_v = Version(latest_version)
            current_v = Version(current_version)
        except InvalidVersion:
            latest_v = latest_version
            current_v = current_version

        if latest_v > current_v:
            set_update_available(True)
            if hasattr(parent, "show_update_indicator"):
                parent.show_update_indicator()
            if not silent:
                install_update(parent, result["data"], latest_version)
        else:
            set_update_available(False)
            if hasattr(parent, "hide_update_indicator"):
                parent.hide_update_indicator()
            if not silent:
                QMessageBox.information(parent, "No Updates", "You already have the latest version.")

        if finished_callback:
            finished_callback()

        if checker in _running_threads:
            _running_threads.remove(checker)

    def handle_error(err):
        if not silent:
            QMessageBox.warning(parent, "Update Error", f"Could not check for updates:\n{err}")
        if finished_callback:
            finished_callback()
        if checker in _running_threads:
            _running_threads.remove(checker)

    checker.update_result.connect(handle_result)
    checker.error_signal.connect(handle_error)
    checker.finished.connect(checker.deleteLater)
    checker.start()


def silent_update_check(parent=None, finished_callback=None):
    check_for_updates_async(parent=parent, finished_callback=finished_callback, silent=True)


def sync_stored_version_on_startup(current_app_version: str):
    stored_version = get_last_installed_version()
    if stored_version != current_app_version:
        set_last_installed_version(current_app_version)
        set_update_available(False)