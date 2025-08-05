from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox
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
    confirm_restore_signal = Signal() 

    def __init__(self, dialog, zip_file_path):
        super().__init__()
        self.dialog = dialog
        self.zip_file_path = Path(zip_file_path)
        self.cancel_requested = False
        self.user_confirmed = False

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)
        self.done_signal.connect(self.on_done)

        self.confirm_restore_signal.connect(self.ask_confirmation)

    def run(self):
        try:
            self.log("Starting restore...")

            temp_extract_folder = APPDATA_DIR / "temp_sims4_restore"
            temp_extract_folder.mkdir(exist_ok=True)

            with zipfile.ZipFile(self.zip_file_path, 'r') as zipf:
                zip_list = zipf.infolist()
                self.progress_signal.emit(0)
                self.max_signal.emit(len(zip_list))
                step = 1

                for item in zip_list:
                    if self.cancel_requested:
                        self.log("Restore cancelled during extraction.")
                        return

                    zipf.extract(item, temp_extract_folder)
                    self.log(f"Extracted: {item.filename}")
                    self.progress_signal.emit(step)
                    step += 1

            extracted_saves = temp_extract_folder / "saves"
            extracted_tray = temp_extract_folder / "Tray"

            if not extracted_saves.exists() and not extracted_tray.exists():
                self.log("Restore zip is missing 'saves' and 'Tray'")
                QMessageBox.critical(self.dialog, "Restore Error", "No saves or Tray folder found in backup!")
                shutil.rmtree(temp_extract_folder, ignore_errors=True)
                return

            self.confirm_restore_signal.emit()
            self.exec_confirm_loop()

            if not self.user_confirmed:
                self.log("Restore cancelled by user.")
                shutil.rmtree(temp_extract_folder, ignore_errors=True)
                return

            if self.cancel_requested:
                self.log("Restore cancelled before file copy.")
                shutil.rmtree(temp_extract_folder, ignore_errors=True)
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

            shutil.rmtree(temp_extract_folder, ignore_errors=True)
            self.log("Restore complete.")
            self.done_signal.emit()

        except Exception as e:
            self.log(f"[ERROR] Restore failed: {e}")

    def exec_confirm_loop(self):
        from time import sleep
        while self.user_confirmed is False and not hasattr(self, "_confirm_answered"):
            sleep(0.05)

    def ask_confirmation(self):
        confirm = QMessageBox.question(
            self.dialog,
            "Confirm Restore",
            "⚠️ This will overwrite your current Sims 4 saves and Tray files.\n\n"
            "Are you sure you want to continue?"
        )
        self.user_confirmed = (confirm == QMessageBox.Yes)
        self._confirm_answered = True

    def log(self, message):
        self.log_signal.emit(message)
        write_log_file(message)

    def on_done(self):
        QMessageBox.information(self.dialog, "Restore Complete", "Sims 4 data has been restored.")
        self.dialog.accept()