import json
import argparse
import os
from pathlib import Path

from lib.audio_file_handler import archive_files, clean_files, convert_wav_m4a, convert_wav_mp3
from lib.icad_tone_detect_handler import upload_to_icad
from lib.logging_handler import CustomLogger
from lib.openmhz_handler import upload_to_openmhz
from lib.rdio_handler import upload_to_rdio


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process Arguments.')
    parser.add_argument("sys_name", help="System Name.")
    parser.add_argument("audio_wav", help="Path to WAV.")
    args = parser.parse_args()

    return args


def get_paths(args):
    root_path = os.getcwd()
    config_file = 'config.json'
    config_path = os.path.join(f'{root_path}/etc', config_file)
    wav_path = args.audio_wav
    mp3_path = wav_path.replace(".wav", ".mp3")
    m4a_path = wav_path.replace(".wav", ".m4a")
    log_path = wav_path.replace(".wav", ".log")
    json_path = wav_path.replace(".wav", ".json")
    system_name = args.sys_name
    return config_path, wav_path, mp3_path, m4a_path, log_path, json_path, system_name


def load_config(config_path, app_name, system_name, log_path):
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        logger = CustomLogger(config_data["log_level"], app_name, log_path).logger
        system_config = config_data["systems"][system_name]
        logger.info(f'Successfully loaded configuration.')
        return config_data, logger, system_config
    except FileNotFoundError:
        print(f'Configuration file {config_path} not found.')
        exit(0)
    except json.JSONDecodeError:
        print(f'Configuration file {config_path} is not in valid JSON format.')
        exit(0)


def load_call_data(logger, json_path):
    try:
        with open(json_path, 'r') as fj:
            call_data = json.load(fj)
        logger.info(f'Successfully loaded call json.')
        return call_data
    except FileNotFoundError:
        print(f'JSON Call Data file {json_path} not found.')
        return False
    except json.JSONDecodeError:
        print(f'JSON Call Data file {json_path} is not in valid JSON format.')
        return False


def main():
    app_name = "icad_tr_uploader"
    args = parse_arguments()
    config_path, wav_path, mp3_path, m4a_path, log_path, json_path, system_name = get_paths(args)
    config_data, logger, system_config = load_config(config_path, app_name, system_name, log_path)

    mp3_exists = os.path.isfile(mp3_path)
    m4a_exists = os.path.isfile(m4a_path)

    try:
        call_data = load_call_data(logger, json_path)
        if not call_data:
            logger.error("Could Not Load Call Data JSON")
            exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error("Could Not Load Call Data JSON")
        exit(1)

    logger.debug(call_data)

    # TODO Some Sort of Check For Duplicate Transmissions based on timestamp and length

    # Upload to iCAD Tone Detect
    if system_config["icad_tone_detect"]["enabled"] == 1:
        if mp3_exists:
            if call_data.get("talkgroup", 0) not in system_config["icad_tone_detect"]["talkgroups"]:
                logger.info(f"Not Sending to Tone Detect API not in talkgroups.")
            else:
                upload_success = upload_to_icad(system_config["icad_tone_detect"], mp3_path, call_data)
                if not upload_success:
                    logger.error("Failed to upload to iCAD Tone Detect API.")
                else:
                    logger.info(
                        f"Successfully uploaded to iCAD Tone Detect API: {system_config['icad_tone_detect']['icad_url']}")
        else:
            logger.warning(f"No MP3 file can't send to iCAD Tone Detect API")

    # Upload to RDIO
    for rdio in system_config["rdio_systems"]:
        if rdio["enabled"] == 1:
            if not m4a_exists:
                logger.warning(f"No M4A file can't send to RDIO")
                continue
            try:
                upload_to_rdio(rdio, m4a_path, json_path)
                logger.info(f"Successfully uploaded to RDIO server: {rdio['rdio_url']}")
            except Exception as e:
                logger.error(f"Failed to upload to RDIO server: {rdio['rdio_url']}. Error: {str(e)}", exc_info=True)
                continue
        else:
            logger.info(f"RDIO system is disabled: {rdio['rdio_url']}")
            continue

    # Upload to OpenMHZ
    if system_config["openmhz"]["enabled"] == 1:
        if m4a_exists:
            openmhz_result = upload_to_openmhz(system_config["openmhz"], m4a_path, call_data)
            logger.debug(openmhz_result)
        else:
            logger.info(f"No M4A file can't send to OpenMHZ")

    if system_config["archive_days"] > 0:
        files = [log_path, json_path, mp3_path, m4a_path, wav_path]
        archive_files(files, system_config["archive_path"])
        clean_files(system_config["archive_path"], system_config["archive_days"])
    elif system_config["archive_days"] == 0:
        pass
    elif system_config["archive_days"] == -1:
        files = [log_path, json_path, mp3_path, m4a_path, wav_path]
        for file in files:
            file_path = Path(file)
            if file_path.is_file():
                try:
                    os.remove(file_path)
                    logger.debug(f"File {file} removed successfully.")
                except Exception as e:
                    logger.error(f"Unable to remove file {file}. Error: {str(e)}")
            else:
                logger.error(f"File {file} does not exist.")


if __name__ == "__main__":
    main()
