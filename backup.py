from PySide6.QtCore import QThread, Signal
from datetime import datetime
from pathlib import Path
import zipfile
import shutil

from config_utils import write_log_file, get_max_backups
from paths import get_game_folder, APPDATA_DIR


INCLUDE_MAP = {
    "sims 4": ["saves", "Tray"],
    "sims 3": ["Saves", "SavedSims"],
    "sims medieval": ["Saves", "SavedSims"],
    "mysims": ["SaveData1", "SaveData2", "SaveData3"],
    "mysims kingdom": ["SaveData1", "SaveData2", "SaveData3"],
}


class BackupWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    max_signal = Signal(int)
    done_signal = Signal()
    cleanup_done_signal = Signal(str)

    def __init__(self, dialog, backup_folder, game_name: str):
        super().__init__()
        self.dialog = dialog
        self.game_name = game_name
        self.game_key = self.game_name.strip().lower()
        self.backup_folder = Path(backup_folder).resolve()
        self.cancel_requested = False

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)

    def run(self):
        try:
            self.log(f"Starting backup for {self.game_name}...")
            self.backup_folder.mkdir(parents=True, exist_ok=True)

            game_root = get_game_folder(self.game_name)
            if not game_root.exists():
                self.log(f"[ERROR] {self.game_name} folder not found: {game_root}")
                return

            include_dirs = INCLUDE_MAP.get(self.game_key, [])
            files_to_backup = []

            for sub in include_dirs:
                p = game_root / sub
                if p.exists():
                    for f in p.rglob("*"):
                        if f.is_file():
                            files_to_backup.append((f, game_root))

            if not files_to_backup and game_root.exists():
                for f in game_root.rglob("*"):
                    if f.is_file():
                        files_to_backup.append((f, game_root))

            if not files_to_backup:
                self.log("[ERROR] No files found to back up.")
                return

            self.progress_signal.emit(0)
            self.max_signal.emit(len(files_to_backup))

            backup_name = f"{self.game_key.replace(' ', '_')}_backup_{datetime.now():%Y%m%d_%H%M%S}.zip"
            backup_path = self.backup_folder / backup_name
            self.log(f"Creating backup: {backup_path}")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for step, (file_path, root) in enumerate(files_to_backup, start=1):
                    if self.cancel_requested:
                        self.log("Backup cancelled by user.")
                        return
                    arcname = file_path.relative_to(root)
                    zipf.write(file_path, arcname)
                    self.log(f"Added: {arcname}")
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
            temp_folder = APPDATA_DIR / f"temp_restore_{self.game_key.replace(' ', '_')}"
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
                summary = "Cleanup complete. Unlimited backups retained."
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