import json
import os

import requests
import logging

module_logger = logging.getLogger('tr_uploader.alertpage_uploader')


def upload_to_alertpage(ap_data, mp3_path, json_path, mp3_url):

    if mp3_url == "":
        module_logger.error(f"MP3 Wasn't uploaded to remote storage: {mp3_path}")
        return False

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

    json_data["filename"] = mp3_url
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

