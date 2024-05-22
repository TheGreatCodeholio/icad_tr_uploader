import json
import logging
import os
import shutil
import subprocess

module_logger = logging.getLogger('icad_tr_uploader.audio_file_handler')


def save_temporary_json_file(tmp_path, json_file_path):
    try:
        # Ensure the directory exists
        os.makedirs(tmp_path, exist_ok=True)

        # Construct the target path for the WAV file
        json_path = os.path.join(tmp_path, os.path.basename(json_file_path))

        # Copy the WAV file to the target path
        shutil.copy(json_file_path, json_path)

        module_logger.debug(f"<<JSON>> <<file>> saved successfully at {json_path}")
    except Exception as e:
        module_logger.error(f"Failed to save <<JSON>> <<file>> at {json_path}: {e}")
        raise


def save_call_data(json_file_path, call_data):
    try:
        # Writing call data to JSON file
        with open(json_file_path, "w") as json_file:
            json.dump(call_data, json_file, indent=4)
        module_logger.debug(f"JSON file saved successfully at {json_file_path}")
    except Exception as e:
        module_logger.error(f"Failed to save JSON file at {json_file_path}: {e}")
        raise  # Re-raise the exception to handle it in a higher-level function


def save_temporary_wav_file(tmp_path, wav_file_path):
    try:
        # Ensure the directory exists
        os.makedirs(tmp_path, exist_ok=True)

        # Construct the target path for the WAV file
        wav_path = os.path.join(tmp_path, os.path.basename(wav_file_path))

        # Copy the WAV file to the target path
        shutil.copy(wav_file_path, wav_path)

        module_logger.debug(f"<<WAV>> <<file>> saved successfully at {wav_path}")
    except Exception as e:
        module_logger.error(f"Failed to save <<WAV>> <<file>> at {wav_path}: {e}")
        raise


def load_call_json(json_file_path):
    try:
        with open(json_file_path, 'r') as f:
            call_data = json.load(f)
        module_logger.info(f"Loaded <<Call>> <<Metadata>> Successfully")
        return call_data
    except FileNotFoundError:
        # Call Metadata JSON not found.
        module_logger.warning(f'<<Call>> <<Metadata>> file {json_file_path} not found.')
        return None
    except json.JSONDecodeError:
        module_logger.error(f'<<Call>> <<Metadata>> file {json_file_path} is not in valid JSON format.')
        return None
    except Exception as e:
        module_logger.error(f"Unexpected <<Error>> while loading <<Call>> <<Metadata>> {json_file_path}: {e}")
        return None


def save_temporary_files(tmp_path, wav_file_path):
    try:
        save_temporary_wav_file(tmp_path, wav_file_path)
        save_temporary_json_file(tmp_path, wav_file_path.replace(".wav", ".json"))
        module_logger.info(f"<<Temporary>> <<Files>> Saved to {tmp_path}")
        return True
    except OSError as e:
        if e.errno == 28:
            module_logger.error(
                f"<<Failed>> to write temp files to {tmp_path}. <<No>> <<space>> <<left>> on device to write files")
        else:
            module_logger.error(f"<<Failed>> to write files to {tmp_path}. <<OS>> <<error>> occurred: {e}")
        return False
    except Exception as e:
        module_logger.error(
            f"An <<unexpected>> <<error>> occurred while <<writing>> <<temporary>> <<files>> to {tmp_path}: {e}")
        return False


def clean_temp_files(wav_file_path, m4a_file_path, json_file_path):
    if os.path.isfile(wav_file_path):
        os.remove(wav_file_path)

    if os.path.isfile(m4a_file_path):
        os.remove(m4a_file_path)

    if os.path.isfile(json_file_path):
        os.remove(json_file_path)


def compress_wav(compression_config, wav_file_path):
    # Check if the WAV file exists
    if not os.path.isfile(wav_file_path):
        module_logger.error(f"WAV file does not exist: {wav_file_path}")
        return False

    module_logger.info(
        f'Converting WAV to M4A at {compression_config.get("sample_rate")}@{compression_config.get("bitrate", 96)}')

    # Construct the ffmpeg command
    m4a_file_path = wav_file_path.replace('.wav', '.m4a')
    command = ["ffmpeg", "-y", "-i", wav_file_path, "-af", "aresample=resampler=soxr", "-ar",
               f"{compression_config.get('sample_rate', 16000)}", "-c:a", "aac",
               "-ac", "1", "-b:a", f"{compression_config.get('bitrate', 96)}k", m4a_file_path]

    try:
        # Execute the ffmpeg command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        module_logger.debug(f"ffmpeg output: {result.stdout}")
        module_logger.info(f"Successfully converted WAV to M4A for file: {wav_file_path}")
        return True
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert WAV to M4A for file {wav_file_path}. Error: {e}"
        module_logger.error(error_message)
        return False
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion of {wav_file_path}: {e}"
        module_logger.error(error_message)
        return False
