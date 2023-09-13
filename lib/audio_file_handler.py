import logging
import os
import subprocess
from pathlib import Path
import time
import shutil
import traceback

module_logger = logging.getLogger('icad_tr_uploader.audio_file')


def convert_wav_m4a(system_config, wav_file_path):
    bitrate = system_config.get("m4a_bitrate", 32)
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return f"MP3 file does not exist: {wav_file_path}"

    module_logger.info(f'Converting WAV to Mono M4A at {bitrate}k')

    command = f'ffmpeg -y -i {wav_file_path} -af aresample=resampler=soxr -ar 22050 -c:a aac -ac 1 -b:a {bitrate}k {wav_file_path.replace(".wav", ".m4a")}'

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted WAV to M4A from file: {wav_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to M4A: {e.output}"
        module_logger.error(error_message)
        return False
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {str(e)}"
        module_logger.error(error_message, exc_info=True)
        return False

    return True


def convert_wav_mp3(system_config, wav_file_path):
    bitrate = system_config.get("mp3_bitrate", 32)
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return f"MP3 file does not exist: {wav_file_path}"

    module_logger.info(f'Converting WAV to Mono MP3 at {bitrate}k')

    command = f"ffmpeg -y -i {wav_file_path} -vn -ar 22050 -ac 1 -b:a {bitrate}k {wav_file_path.replace('.wav', '.mp3')}"

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted WAV to MP3 from file: {wav_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to MP3: {e.output}"
        module_logger.error(error_message)
        return False
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {str(e)}"
        module_logger.error(error_message, exc_info=True)
        return False

    return True


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
