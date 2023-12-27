import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import shutil
import traceback

module_logger = logging.getLogger('icad_tr_uploader.audio_file')


def archive_files(files, archive_path):
    # Get the current date
    current_date = datetime.now()

    # Extract year, month, and day from the current date
    year = current_date.year
    month = current_date.month
    day = current_date.day

    # Create folder structure
    folder_path = os.path.join(archive_path, str(year), str(month), str(day))
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        file_path = Path(file)
        if file_path.is_file():
            try:
                shutil.move(file_path, folder_path)
                module_logger.debug(f"File {file} archived successfully.")
            except Exception as e:
                module_logger.error(f"Unable to archive file {file}. Error: {str(e)}")
        else:
            module_logger.error(f"File {file} does not exist.")


def clean_files(archive_path, archive_days):
    current_time = time.time()
    count = 0
    archive_dir = os.path.abspath(archive_path)

    for root, dirs, files in os.walk(archive_dir, topdown=False):
        # Clean files that are older than archive_days
        for name in files:
            file_path = os.path.join(root, name)
            creation_time = os.path.getctime(file_path)
            days_difference = (current_time - creation_time) // (24 * 3600)

            if days_difference >= archive_days:
                try:
                    os.remove(file_path)
                    count += 1
                    module_logger.debug(f"Successfully cleaned file: {file_path}")
                except Exception as e:
                    module_logger.error(f"Failed to clean file: {file_path}, Error: {str(e)}")
                    traceback.print_exc()

        # Clean up empty directories
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            # Check if the directory is empty
            if not os.listdir(dir_path):
                try:
                    os.rmdir(dir_path)
                    module_logger.debug(f"Successfully removed empty directory: {dir_path}")
                except Exception as e:
                    module_logger.error(f"Failed to remove directory: {dir_path}, Error: {str(e)}")
                    traceback.print_exc()

    module_logger.info(f"Cleaned {count} files.")
