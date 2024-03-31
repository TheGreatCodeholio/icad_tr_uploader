import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import shutil

module_logger = logging.getLogger('icad_tr_uploader.audio_file')


def archive_files(files, filtered_files, archive_path):
    """
    Archives a list of files into a directory structure based on the current date.

    :param files: List of all files associated with audio transmission.
    :param filtered_files: List of file paths to archive, filtered by extensions from system config.
    :param archive_path: Base path where the archive directories will be created.
    """
    # Get the current date
    current_date = datetime.utcnow()

    # Create folder structure using current date
    folder_path = os.path.join(archive_path, str(current_date.year), str(current_date.month), str(current_date.day))
    os.makedirs(folder_path, exist_ok=True)

    for file in filtered_files:
        try:
            file_path = Path(file)
            if file_path.is_file():
                # Move file to the archive folder
                shutil.move(str(file_path), os.path.join(folder_path, os.path.basename(file_path)))
                module_logger.debug(f"File {file} archived successfully to {folder_path}.")
            else:
                module_logger.error(f"File {file} does not exist and cannot be archived.")
        except Exception as e:
            module_logger.error(f"Unable to archive file {file}. Error: {e}")

    for file in files:
        if os.path.isfile(file):
            os.remove(file)


def clean_files(archive_path, archive_days):
    """
    Removes files older than a specified number of days within the given archive path.
    Also removes empty directories after cleaning up the files.

    :param archive_path: The base directory from which to start cleaning.
    :param archive_days: The age in days beyond which files should be removed.
    """
    current_time = time.time()
    count = 0
    archive_dir = os.path.abspath(archive_path)

    for root, dirs, files in os.walk(archive_dir, topdown=False):
        # Clean files that are older than archive_days
        for name in files:
            file_path = os.path.join(root, name)
            try:
                creation_time = os.path.getctime(file_path)
                days_difference = (current_time - creation_time) / (24 * 3600)

                if days_difference >= archive_days:
                    os.remove(file_path)
                    count += 1
                    module_logger.debug(f"Successfully cleaned file: {file_path}")
            except Exception as e:
                module_logger.error(f"Failed to clean file: {file_path}, Error: {e}")

        # Clean up empty directories
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Check if the directory is empty
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    module_logger.debug(f"Successfully removed empty directory: {dir_path}")
            except Exception as e:
                module_logger.error(f"Failed to remove directory: {dir_path}, Error: {e}")

    module_logger.info(f"Cleaned {count} files.")

