import logging
import os
import subprocess

module_logger = logging.getLogger('tr_uploader.mp3')


def convert_wav_mp3(system_config, wav_file_path):
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return f"WAV file does not exist: {wav_file_path}"

    module_logger.info(f'Converting WAV to Mono MP3 at {str(system_config["mp3_bitrate"])}k')

    command = f"ffmpeg -y -i {wav_file_path} -vn -ar 22050 -ac 1 -b:a {system_config['mp3_bitrate']}k {wav_file_path.replace('.wav', '.mp3')}"

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted WAV to MP3 for file: {wav_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to MP3: {e.output}"
        module_logger.critical(error_message)
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {str(e)}"
        module_logger.critical(error_message, exc_info=True)
        return error_message

    return None


def convert_wav_m4a(system_config, wav_file_path):
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return f"WAV file does not exist: {wav_file_path}"

    module_logger.info(f'Converting WAV to Mono M4A at {str(system_config["m4a_bitrate"])}k')

    command = f"ffmpeg -y -i {wav_file_path} -af aresample=resampler=soxr -ar 22050 -c:a aac -ac 1 -b:a {system_config['m4a_bitrate']}k {wav_file_path.replace('.wav', '.m4a')}"

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted WAV to M4A for file: {wav_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to M4A: {e.output}"
        module_logger.critical(error_message)
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {str(e)}"
        module_logger.critical(error_message, exc_info=True)
        return error_message

    return None
