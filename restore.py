from PySide6.QtCore import QThread, Signal
from pathlib import Path
import shutil
import zipfile
from paths import get_sims4_folder, APPDATA_DIR
from config_utils import write_log_file


class RestoreWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    max_signal = Signal(int)
    done_signal = Signal()
    request_confirmation_signal = Signal()
    confirmation_result_signal = Signal(bool)

    def __init__(self, dialog, zip_file_path):
        super().__init__()
        self.dialog = dialog
        self.zip_file_path = Path(zip_file_path)
        self.cancel_requested = False
        self.user_confirmed = None

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)
        self.done_signal.connect(self.on_done)
        self.confirmation_result_signal.connect(self.set_confirmation_result)

    def run(self):
        temp_extract_folder = APPDATA_DIR / "temp_sims4_restore"
        try:
            self.log("Starting restore...")

            temp_extract_folder.mkdir(exist_ok=True)

            with zipfile.ZipFile(self.zip_file_path, 'r') as zipf:
                zip_list = zipf.infolist()
                self.progress_signal.emit(0)
                self.max_signal.emit(len(zip_list))

                for step, item in enumerate(zip_list, start=1):
                    if self.cancel_requested:
                        self.log("Restore cancelled during extraction.")
                        self._cleanup_temp(temp_extract_folder)
                        return

                    zipf.extract(item, temp_extract_folder)
                    self.log(f"Extracted: {item.filename}")
                    self.progress_signal.emit(step)

            extracted_saves = temp_extract_folder / "saves"
            extracted_tray = temp_extract_folder / "Tray"

            if not extracted_saves.exists() and not extracted_tray.exists():
                self.log("Restore zip is missing 'saves' and 'Tray'")
                self._cleanup_temp(temp_extract_folder)
                return

            self.request_confirmation_signal.emit()
            while self.user_confirmed is None:
                self.msleep(50)

            if not self.user_confirmed:
                self.log("Restore cancelled by user.")
                self._cleanup_temp(temp_extract_folder)
                return

            if self.cancel_requested:
                self.log("Restore cancelled before file copy.")
                self._cleanup_temp(temp_extract_folder)
                return

            sims4_path = get_sims4_folder()
            if extracted_saves.exists():
                dest = sims4_path / "saves"
                shutil.copytree(extracted_saves, dest, dirs_exist_ok=True)
                self.log(f"Restored saves to: {dest}")

            if extracted_tray.exists():
                dest = sims4_path / "Tray"
                shutil.copytree(extracted_tray, dest, dirs_exist_ok=True)
                self.log(f"Restored Tray to: {dest}")

            self._cleanup_temp(temp_extract_folder)
            self.log("Restore complete.")
            self.done_signal.emit()

        except Exception as e:
            self.log(f"[ERROR] Restore failed: {e}")
            self._cleanup_temp(temp_extract_folder)

    def _cleanup_temp(self, folder_path):
        try:
            if folder_path.exists():
                shutil.rmtree(folder_path, ignore_errors=True)
                self.log("Temporary restore folder cleaned.")
        except Exception as e:
            self.log(f"[ERROR] Failed to clean temp folder: {e}")

    def set_confirmation_result(self, result: bool):
        self.user_confirmed = result

    def log(self, message):
        self.log_signal.emit(message)
        write_log_file(message)

    def on_done(self):
        self.dialog.accept()