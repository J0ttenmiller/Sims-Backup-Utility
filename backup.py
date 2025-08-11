from PySide6.QtCore import QThread, Signal
from datetime import datetime
from pathlib import Path
import shutil
import zipfile
from paths import get_sims4_folder, APPDATA_DIR
from config_utils import (
    write_log_file,
    get_max_backups,
    save_default_backup_path
)


class BackupWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    max_signal = Signal(int)
    done_signal = Signal()
    cleanup_done_signal = Signal(str)

    def __init__(self, dialog, backup_folder):
        super().__init__()
        self.dialog = dialog
        self.backup_folder = Path(backup_folder).resolve()
        self.cancel_requested = False

        save_default_backup_path(str(self.backup_folder))

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)

    def run(self):
        try:
            self.log("Starting backup...")
            self.backup_folder.mkdir(parents=True, exist_ok=True)

            sims4_path = get_sims4_folder()
            if not sims4_path.exists():
                self.log("[ERROR] Sims 4 folder not found.")
                return

            files_to_backup = [
                file for folder_name in ["saves", "Tray"]
                for file in (sims4_path / folder_name).rglob("*")
                if file.is_file()
            ]

            if not files_to_backup:
                self.log("[ERROR] No Sims 4 files found to back up.")
                return

            self.progress_signal.emit(0)
            self.max_signal.emit(len(files_to_backup))

            backup_path = self.backup_folder / f"sims4_backup_{datetime.now():%Y%m%d_%H%M%S}.zip"
            self.log(f"Creating backup: {backup_path}")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for step, file_path in enumerate(files_to_backup, start=1):
                    if self.cancel_requested:
                        self.log("Backup cancelled by user.")
                        return
                    zipf.write(file_path, file_path.relative_to(sims4_path))
                    self.log(f"Added: {file_path.relative_to(sims4_path)}")
                    self.progress_signal.emit(step)

            self.log("Backup complete.")
            self.cleanup_folders()
            self.done_signal.emit()

        except Exception as e:
            self.log(f"[ERROR] Backup failed: {e}")

    def log(self, message: str):
        self.log_signal.emit(message)
        write_log_file(message)

    def cleanup_folders(self):
        try:
            temp_folder = APPDATA_DIR / "temp_sims4_restore"
            if temp_folder.exists():
                try:
                    shutil.rmtree(temp_folder, ignore_errors=True)
                    self.log("Temporary restore folder cleaned.")
                except Exception as e:
                    self.log(f"[ERROR] Failed to clean temp folder: {e}")

            backup_files = sorted(
                self.backup_folder.glob("*.zip"),
                key=lambda x: x.stat().st_mtime
            )
            max_backups = get_max_backups()

            removed_count = 0
            if max_backups > 0 and len(backup_files) > max_backups:
                for old_backup in backup_files[:-max_backups]:
                    try:
                        old_backup.unlink()
                        removed_count += 1
                        self.log(f"Deleted old backup: {old_backup.name}")
                    except Exception as e:
                        self.log(f"[ERROR] Failed to delete {old_backup.name}: {e}")

            if max_backups == 0:
                summary = "Unlimited backups is set!"
            elif removed_count > 0:
                summary = f"Cleanup complete. {removed_count} old backup(s) removed."
            else:
                summary = "Cleanup complete. No old backups needed removal."

            self.log(summary)
            self.cleanup_done_signal.emit(summary)

        except Exception as e:
            error_msg = f"[ERROR] Cleanup error: {e}"
            self.log(error_msg)
            self.cleanup_done_signal.emit(error_msg)