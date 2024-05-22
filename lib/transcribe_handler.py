import io
import json

import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.transcribe')


def upload_to_transcribe(transcribe_config, wav_file_path, call_data, talkgroup_config=None):
    url = transcribe_config['api_url']
    module_logger.info(f'Starting upload to <<iCAD>> <<Transcribe>>: {url}')

    config_data = {}  # Initialize as an empty dict

    if talkgroup_config:
        config_data['whisper_config_data'] = json.dumps(talkgroup_config.get("whisper", {}))

    try:
        json_string = json.dumps(call_data)
        json_bytes = json_string.encode('utf-8')

        with open(wav_file_path, 'rb') as audio_file:
             data = {
                 'audioFile': audio_file,
                 'jsonFile': json_bytes
             }

        response = requests.post(url, files=data, data=config_data)
        response.raise_for_status()
        response_json = response.json()
        module_logger.info(f'<<iCAD>> <<Transcribe>> successfully transcribed audio: {url}')

        return response_json

    except requests.exceptions.HTTPError as err:
        module_logger.error(f"<<HTTP>> <<error>> occurred while uploading to <<iCAD>> <<Transcribe>> API: {err}")
        return None
    except Exception as err:
        module_logger.error(f"<<Unexpected>> <<error>> occurred while uploading to <<iCAD>> <<Transcribe>> API: {err}")
        return None
