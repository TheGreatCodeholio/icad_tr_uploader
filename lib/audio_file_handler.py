import logging
from pathlib import Path
import time
import shutil
import traceback

module_logger = logging.getLogger('icad_tr_uploader.mp3')


def archive_files(files, archive_path):
    for file in files:
        file_path = Path(file)
        if file_path.is_file():
            try:
                shutil.move(file_path, archive_path)
                module_logger.debug(f"File {file} archived successfully.")
            except Exception as e:
                module_logger.error(f"Unable to archive file {file}. Reason: {str(e)}")
        else:
            module_logger.error(f"File {file} does not exist.")


def clean_files(archive_path, archive_days):
    current_time = time.time()
    count = 0
    archive_dir = Path(archive_path)
    for f in archive_dir.iterdir():
        creation_time = f.stat().st_ctime
        if (current_time - creation_time) // (24 * 3600) >= archive_days:
            try:
                f.unlink()
                count += 1
                module_logger.debug(f"Successfully cleaned file: {f}")
            except Exception as e:
                module_logger.error(f"Failed to clean file: {f}, Error: {str(e)}")
                traceback.print_exc()
    module_logger.debug(f"Cleaned {count} files.")
