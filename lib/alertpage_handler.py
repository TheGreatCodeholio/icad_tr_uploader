import json
import traceback

import requests
import logging

from lib.file_save_handler import get_storage

module_logger = logging.getLogger('tr_uploader.alertpage_uploader')


def upload_to_alertpage(file_storage_config, ap_data, mp3_path, json_path):
    if not os.path.isfile(mp3_path):
        module_logger.error(f"MP3 file does not exist: {mp3_path}")
        return False

    if not os.path.isfile(json_path):
        module_logger.error(f"JSON file does not exist: {json_path}")
        return False

    module_logger.info(f'Uploading To Alert Page API: {str(ap_data["url"])}')

    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        if not json_data:
            module_logger.critical(f'Failed Uploading To AlertPage API: Empty JSON')
            return False
    except (FileNotFoundError, json.JSONDecodeError) as e:
        module_logger.critical(f'Failed reading JSON file: {str(e)}')
        return False

    try:
        with open(mp3_path, 'rb') as af:
            audio_data = af.read()

        storage_type = file_storage_config["storage_type"]
        storage = get_storage(storage_type, file_storage_config)
        remote_path = f'{ap_data["system"]}/{json_data["talkgroup"]}/{mp3_path.split("/")[-1]}'
        response = storage.upload_file(audio_data, remote_path)
        json_data["filename"] = response["file_path"]
    except Exception as e:
        module_logger.error(f'File Upload Failed: {str(e)}')
        return False

    json_data["auth_key"] = ap_data['auth_key']
    json_data["system"] = ap_data['system']
    json_data["source"] = ap_data['source']

    try:
        hdr = {"Content-Type": "application/json"}
        r = requests.post(ap_data['url'], json=json_data, headers=hdr)
        r.raise_for_status()

        module_logger.info(f'Successfully uploaded to AlertPage API: {r.status_code}, {r.text}')
    except (requests.exceptions.RequestException, IOError) as e:
        module_logger.critical(f'Failed Uploading To AlertPage API: {str(e)}')
        return False

    return True

