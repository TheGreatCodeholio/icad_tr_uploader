import json
import argparse
import os
import traceback
from datetime import datetime
from pathlib import Path

from lib.audio_file_handler import archive_files, clean_files
from lib.broadcastify_calls_handler import upload_to_broadcastify_calls
from lib.icad_player_handler import upload_to_icad_player
from lib.icad_tone_detect_handler import upload_to_icad, upload_to_icad_legacy
from lib.logging_handler import CustomLogger
from lib.openmhz_handler import upload_to_openmhz
from lib.rdio_handler import upload_to_rdio
from lib.remote_storage_handler import get_storage, GoogleCloudStorage, SCPStorage, AWSS3Storage
from lib.transcribe_handler import upload_to_transcribe


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
    m4a_path = wav_path.replace(".wav", ".m4a")
    log_path = wav_path.replace(".wav", ".log")
    json_path = wav_path.replace(".wav", ".json")
    system_name = args.sys_name
    return config_path, wav_path, m4a_path, log_path, json_path, system_name


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


def save_call_json(json_file_path, call_data):
    with open(json_file_path, 'w') as f:
        json.dump(call_data, f, indent=4, sort_keys=True)


def load_call_data(logger, json_path):
    try:
        with open(json_path, 'r') as fj:
            call_data = json.load(fj)
            call_data["transcript"] = None
            call_data["audio_url"] = None
            call_data["tone_detection"] = None
        logger.info(f'Successfully loaded call json.')
        return call_data
    except FileNotFoundError:
        print(f'JSON Call Data file {json_path} not found.')
        return None
    except json.JSONDecodeError:
        print(f'JSON Call Data file {json_path} is not in valid JSON format.')
        return None


def main():
    app_name = "icad_tr_uploader"
    args = parse_arguments()
    config_path, wav_path, m4a_path, log_path, json_path, system_name = get_paths(args)
    config_data, logger, system_config = load_config(config_path, app_name, system_name, log_path)

    m4a_exists = os.path.isfile(m4a_path)
    wav_exists = os.path.isfile(wav_path)

    try:
        call_data = load_call_data(logger, json_path)
        talkgroup_decimal = call_data.get("talkgroup", 0)
        if not call_data:
            logger.error("Could Not Load Call Data JSON")
            exit(1)
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Could Not Load Call Data JSON: {e}")
        exit(1)

    logger.debug(call_data)

    # TODO Some Sort of Check For Duplicate Transmissions based on timestamp and length

    # upload to remote storage
    storage_config = system_config.get("file_storage", {})

    if storage_config.get("enabled", 0) == 1:
        if m4a_exists:
            storage_type = get_storage(storage_config)
            if storage_type:
                try:
                    upload_response = storage_type.upload_file(m4a_path)
                    call_data["audio_url"] = upload_response
                except Exception as e:
                    traceback.print_exc()
                    logger.error(f'File <<Upload>> <<failed>> File Save Error: {e}')
        else:
            logger.warning(f"No M4A file can't send to Remote Storage")

    if system_config.get("transcribe", {}).get("enabled", 0) == 1:
        if m4a_exists:

            if talkgroup_decimal not in system_config.get("transcribe", {}).get("talkgroups",
                                                                                []) and "*" not in system_config.get(
                "transcribe", {}).get("talkgroups", []):
                logger.info(f"Not Sending to Transcribe API talkgroup not in allowed talkgroups.")
            else:
                talkgroup_config = system_config.get("talkgroup_config", {}).get(str(talkgroup_decimal))

                transcribe_json = upload_to_transcribe(system_config.get("transcribe", {}), m4a_path, json_path,
                                                       talkgroup_config)
                if transcribe_json:
                    call_data["transcript"] = transcribe_json

        else:
            logger.warning(f"No M4A file can't send to Transcribe API")

    # Upload to iCAD Tone Detect
    for icad_detect in system_config.get("icad_tone_detect", []):
        if icad_detect.get("enabled", 0) == 1:
            if not m4a_exists:
                logger.warning(f"No M4A file can't send to iCAD Tone Detect")
                continue
            try:
                if icad_detect.get("legacy", 0) == 1:
                    icad_result = upload_to_icad_legacy(icad_detect, m4a_path, call_data)
                else:
                    icad_result = upload_to_icad(icad_detect, m4a_path, json_path)

                if icad_result:
                    logger.info(f"Successfully uploaded to iCAD Detect server: {icad_detect.get('icad_url')}")
                else:
                    raise Exception('Unknown Error')
            except Exception as e:
                logger.error(f"Failed to upload to iCAD Detect server: {icad_detect.get('icad_url')}. Error: {str(e)}",
                             exc_info=True)
                continue
        else:
            logger.warning(f"iCAD Detect is disabled: {icad_detect.get('icad_url')}")
            continue

    save_call_json(json_path, call_data)

    if system_config.get("icad_player", {}).get("enabled", 0) == 1:
        if m4a_exists and call_data.get('audio_url', None):

            if talkgroup_decimal not in system_config.get("icad_player", {}).get("talkgroups",
                                                                                 []) and "*" not in system_config.get(
                "icad_player", {}).get("talkgroups", []):
                logger.info(f"Not Sending to iCAD Player talkgroup not in allowed talkgroups.")
            else:
                upload_to_icad_player(system_config.get("icad_player", {}), call_data)
        else:
            logger.warning(f"No M4A file can't send to iCAD Tone Detect API")

    # Upload to RDIO
    for rdio in system_config.get("rdio_systems", []):
        if rdio.get("enabled", 0) == 1:
            if not m4a_exists:
                logger.warning(f"No M4A file can't send to RDIO")
                continue
            try:
                upload_to_rdio(rdio, m4a_path, json_path)
                logger.info(f"Successfully uploaded to RDIO server: {rdio.get('rdio_url')}")
            except Exception as e:
                logger.error(f"Failed to upload to RDIO server: {rdio.get('rdio_url')}. Error: {str(e)}", exc_info=True)
                continue
        else:
            logger.warning(f"RDIO system is disabled: {rdio.get('rdio_url')}")
            continue

    # Upload to OpenMHZ
    if system_config.get("openmhz", {}).get("enabled", 0) == 1:
        if m4a_exists:
            openmhz_result = upload_to_openmhz(system_config.get("openmhz", {}), m4a_path, call_data)
        else:
            logger.warning(f"No M4A file can't send to OpenMHZ")

    if system_config.get("broadcastify_calls", {}).get("enabled", 0) == 1:
        if m4a_exists:
            bcfy_calls_result = upload_to_broadcastify_calls(system_config.get("broadcastify_calls", {}), m4a_path,
                                                             call_data)
        else:
            logger.warning(f"No M4A file can't send to Broadcastify Calls")

    files = [log_path, json_path, m4a_path, wav_path]

    archive_days = storage_config.get("archive_days", 0)
    archive_path = system_config.get("archive_path", None)

    if archive_days > 0:
        filtered_files = [file for file in files if
                          any(file.endswith(ext) for ext in system_config.get("archive_extensions", []))]
        archive_files(files, filtered_files, archive_path)
        clean_files(archive_path, archive_days)
    elif archive_days == 0:
        pass
    elif archive_days == -1:
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
