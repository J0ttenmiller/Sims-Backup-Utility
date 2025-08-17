from PySide6.QtCore import QThread, Signal
from pathlib import Path
import shutil
import zipfile

from paths import get_game_folder, APPDATA_DIR
from config_utils import write_log_file


INCLUDE_MAP = {
    "sims 4": ["saves", "Tray"],
    "sims 3": ["Saves", "SavedSims"],
    "sims medieval": ["Saves", "SavedSims"],
    "mysims": ["SaveData1", "SaveData2", "SaveData3"],
    "mysims kingdom": ["SaveData1", "SaveData2", "SaveData3"],
}


class RestoreWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    max_signal = Signal(int)
    done_signal = Signal()
    request_confirmation_signal = Signal()
    confirmation_result_signal = Signal(bool)

    def __init__(self, dialog, zip_file_path, game_name: str):
        super().__init__()
        self.dialog = dialog
        self.zip_file_path = Path(zip_file_path)
        self.game_name = game_name
        self.game_key = self.game_name.strip().lower()
        self.cancel_requested = False
        self.user_confirmed = None

        self.log_signal.connect(dialog.log)
        self.progress_signal.connect(dialog.update_progress)
        self.max_signal.connect(dialog.set_max)
        self.done_signal.connect(self.on_done)
        self.confirmation_result_signal.connect(self.set_confirmation_result)

    def run(self):
        try:
            self.log(f"Starting restore for {self.game_name}...")

            temp_extract_folder = APPDATA_DIR / f"temp_restore_{self.game_key.replace(' ', '_')}"
            temp_extract_folder.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(self.zip_file_path, 'r') as zipf:
                zip_list = zipf.infolist()
                self.progress_signal.emit(0)
                self.max_signal.emit(len(zip_list))

                for step, item in enumerate(zip_list, start=1):
                    if self.cancel_requested:
                        self.log("Restore cancelled during extraction.")
                        shutil.rmtree(temp_extract_folder, ignore_errors=True)
                        return
                    zipf.extract(item, temp_extract_folder)
                    self.log(f"Extracted: {item.filename}")
                    self.progress_signal.emit(step)

            self.request_confirmation_signal.emit()
            while self.user_confirmed is None:
                self.msleep(50)

            if not self.user_confirmed:
                self.log("Restore cancelled by user.")
                shutil.rmtree(temp_extract_folder, ignore_errors=True)
                return

            if self.cancel_requested:
                self.log("Restore cancelled before file copy.")
                shutil.rmtree(temp_extract_folder, ignore_errors=True)
                return

            game_root = get_game_folder(self.game_name)
            if not game_root.exists():
                game_root.mkdir(parents=True, exist_ok=True)

            include_dirs = INCLUDE_MAP.get(self.game_key, [])
            restored_any = False
            for sub in include_dirs:
                src = temp_extract_folder / sub
                dst = game_root / sub
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    self.log(f"Restored: {dst.relative_to(game_root)}")
                    restored_any = True

            if not restored_any:
                for item in temp_extract_folder.iterdir():
                    src = item
                    dst = game_root / item.name
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    self.log(f"Restored: {dst.relative_to(game_root)}")

            shutil.rmtree(temp_extract_folder, ignore_errors=True)
            self.log("Restore complete.")
            self.done_signal.emit()

        except Exception as e:
            self.log(f"[ERROR] Restore failed: {e}")

    def set_confirmation_result(self, result: bool):
        self.user_confirmed = result

    def log(self, message):
        self.log_signal.emit(message)
        write_log_file(message)

    def on_done(self):
        self.dialog.accept()