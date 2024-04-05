import json

import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.transcribe')


def upload_to_transcribe(transcribe_config, audio_file_path, json_file_path, call_data, talkgroup_config=None):
    url = transcribe_config['api_url']
    module_logger.info(f'Uploading To Transcribe API: {url}')

    talkgroup_dec = call_data.get("talkgroup", 0)
    config_data = {}  # Initialize as an empty dict

    # Determine the appropriate talkgroup configuration
    if talkgroup_dec > 0 and talkgroup_config:
        talkgroup_dec_str = str(talkgroup_dec)
        config_data['whisper_config_data'] = json.dumps(
            talkgroup_config.get(talkgroup_dec_str) or
            talkgroup_config.get("*", {})
        )

    # Use context managers to automatically handle file opening and closing
    try:
        with open(audio_file_path, 'rb') as af, open(json_file_path, 'rb') as jf:
            data = {
                'audioFile': af,
                'jsonFile': jf
            }

            response = requests.post(url, files=data, data=config_data)
            response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
            response_json = response.json()
            module_logger.info(f'Successfully received transcript data from: {url}')
            module_logger.debug(f'{response_json}')

            return response_json
    except FileNotFoundError as e:
        module_logger.error(f'Transcribe - Audio File not found {audio_file_path}: {e}')
        return None
    except requests.exceptions.HTTPError as err:
        module_logger.error(f"Transcribe - HTTP error occurred: {err}")
        return None
    except Exception as err:
        module_logger.error(f"Error uploading to Transcribe API: {err}")
        return None
