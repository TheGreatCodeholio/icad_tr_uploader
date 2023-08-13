import json
import os
import requests
import logging


module_logger = logging.getLogger('tr_uploader.icad_uploader')


def upload_to_icad(icad_data, mp3_path, json_path):
    if not os.path.isfile(mp3_path):
        module_logger.error(f"MP3 file does not exist: {mp3_path}")
        return False

    if not os.path.isfile(json_path):
        module_logger.error(f"JSON file does not exist: {json_path}")
        return False

    module_logger.info(f'Uploading To iCAD API: {str(icad_data["icad_url"])}')

    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        module_logger.critical(f'Failed reading JSON file: {str(e)}')
        return False

    if not json_data:
        module_logger.critical(f'Failed Uploading To iCAD API: Empty JSON')
        return False

    json_data["api_key"] = icad_data['icad_url']
    json_data["system_id"] = icad_data['system_id']

    try:
        with open(mp3_path, 'rb') as audio_file:
            files = {'file': audio_file}
            data = json_data
            r = requests.post(icad_data['icad_url'], files=files, data=data)
            r.raise_for_status()

            module_logger.info(f'Successfully uploaded to iCAD API: {r.status_code}, {r.text}')

            # # Save the response JSON
            # json_path = mp3_path.replace(".mp3", "_tones.json")
            # with open(json_path, 'w') as json_file:
            #     json_file.write(r.text)
            # json_file.close()

    except (FileNotFoundError, requests.exceptions.RequestException, IOError) as e:
        module_logger.critical(f'Failed Uploading To iCAD API: {str(e)} {r.status_code} {r.text}')
        return False

    return True
