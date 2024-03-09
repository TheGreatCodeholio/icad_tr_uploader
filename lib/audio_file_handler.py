import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import shutil
import traceback

module_logger = logging.getLogger('icad_tr_uploader.audio_file')


def convert_wav_mp3(wav_file_path):
    """
    Converts a WAV file to an MP3 file using ffmpeg, ensuring the output MP3 is mono and has a bitrate of 32k.

    :param wav_file_path: The file path of the WAV file to be converted.
    :return: True if conversion is successful, False otherwise.
    """
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return False

    mp3_file_path = wav_file_path.replace('.wav', '.mp3')
    module_logger.info(f'Converting WAV to Mono MP3 at 32k: {wav_file_path} to {mp3_file_path}')

    command = [
        "ffmpeg", "-y", "-i", wav_file_path, "-vn", "-ar", "22050", "-ac", "1", "-b:a", "32k", mp3_file_path
    ]

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted WAV to MP3: {wav_file_path} to {mp3_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to MP3: {e.output}"
        module_logger.error(error_message)
        return False
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {e}"
        module_logger.error(error_message, exc_info=True)
        return False

    return True


def archive_files(files, archive_path):
    """
    Archives a list of files into a directory structure based on the current date.

    :param files: List of file paths to archive.
    :param archive_path: Base path where the archive directories will be created.
    """
    # Get the current date
    current_date = datetime.now()

    # Create folder structure using current date
    folder_path = os.path.join(archive_path, str(current_date.year), str(current_date.month), str(current_date.day))
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        try:
            file_path = Path(file)
            if file_path.is_file():
                # Move file to the archive folder
                shutil.move(str(file_path), folder_path)
                module_logger.debug(f"File {file} archived successfully to {folder_path}.")
            else:
                module_logger.error(f"File {file} does not exist and cannot be archived.")
        except Exception as e:
            module_logger.error(f"Unable to archive file {file}. Error: {e}")


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

