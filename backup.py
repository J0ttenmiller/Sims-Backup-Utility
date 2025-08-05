from PySide6.QtCore import QThread, Signal
from datetime import datetime
from pathlib import Path
import zipfile
import shutil
from config_utils import write_log_file
from paths import get_sims4_folder


class BackupWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    max_signal = Signal(int)
    done_signal = Signal()

    def __init__(self, dialog, backup_folder):
        super().__init__()
        self.dialog = dialog
        self.backup_folder = Path(backup_folder).resolve()
        self.cancel_requested = False

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)
        self.done_signal.connect(self.on_done)

    def run(self):
        try:
            self.log("Starting backup...")

            self.backup_folder.mkdir(parents=True, exist_ok=True)

            sims4_path = get_sims4_folder()
            if not sims4_path.exists():
                self.log("[ERROR] Sims 4 folder not found.")
                return

            files_to_backup = []
            for folder_name in ["saves", "Tray"]:
                folder_path = sims4_path / folder_name
                if folder_path.exists():
                    for file in folder_path.rglob("*"):
                        if file.is_file():
                            files_to_backup.append(file)

            if not files_to_backup:
                self.log("[ERROR] No Sims 4 files found to back up.")
                return

            self.progress_signal.emit(0)
            self.max_signal.emit(len(files_to_backup))
            step = 1

            backup_name = f"sims4_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            backup_path = self.backup_folder / backup_name

            self.log(f"Creating backup: {backup_path}")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_backup:
                    if self.cancel_requested:
                        self.log("Backup cancelled by user.")
                        return

                    arcname = file_path.relative_to(sims4_path)
                    zipf.write(file_path, arcname)

                    self.log(f"Added: {arcname}")
                    self.progress_signal.emit(step)
                    step += 1

            self.log("Backup complete.")
            self.done_signal.emit()

        except Exception as e:
            self.log(f"[ERROR] Backup failed: {e}")

    def log(self, message):
        self.log_signal.emit(message)
        write_log_file(message)

    def on_done(self):
        self.dialog.accept()