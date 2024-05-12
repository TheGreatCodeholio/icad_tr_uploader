import json
import os
import time
from datetime import datetime

import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.rdio_uploader')


def upload_to_rdio(rdio_data, wav_file_path, call_data):
    module_logger.info(f'Uploading To RDIO: {rdio_data["rdio_url"]}')

    # Use context managers to automatically handle file opening and closing
    try:

        utc_time = datetime.utcfromtimestamp(call_data.get('start_time', time.time()))
        formatted_time = utc_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        with open(wav_file_path, 'rb') as audio_file:
            files = {
                'audio': (call_data['filename'], audio_file, 'audio/x-wav')
            }

            # Prepare additional data for the post request
            data = {
                "audioName": call_data['filename'],
                "audioType": "audio/x-wav",
                "dateTime": formatted_time,
                "frequencies": json.dumps(call_data.get('freqList', [])),
                "frequency": call_data['freq'],
                "key": rdio_data['rdio_api_key'],
                "patches": json.dumps(call_data.get('patches', [])),
                "sources": json.dumps(call_data.get('srcList', [])),
                "system": rdio_data['system_id'],
                "systemLabel": call_data['short_name'],
                "talkgroup": call_data['talkgroup'],
                "talkgroupGroup": call_data['talkgroup_group'],
                "talkgroupLabel": call_data['talkgroup_description'],
                "talkgroupTag": call_data['talkgroup_tag']
            }

            response = requests.post(rdio_data['rdio_url'], files=files, data=data)
            response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
            module_logger.info(f'Successfully uploaded to RDIO: {response.status_code}, {response.text}')
            return True
    except FileNotFoundError as e:
        module_logger.error(f'RDIO {rdio_data["rdio_url"]} - File not found: {e}')
    except requests.exceptions.RequestException as e:
        # This captures HTTP errors, connection errors, etc.
        module_logger.error(f'Failed Uploading To RDIO {rdio_data["rdio_url"]}: {e}')
    except Exception as e:
        # Catch-all for any other unexpected errors
        module_logger.error(f'An unexpected error occurred while upload to RDIO {rdio_data["rdio_url"]}: {e}')

    return False

