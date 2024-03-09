import os

import requests
import logging

module_logger = logging.getLogger('ap_tr_uploader.rdio_uploader')


def upload_to_rdio(rdio_data, m4a_path, json_path):
    module_logger.info(f'Uploading To RDIO: {rdio_data["rdio_url"]}')

    # Use context managers to automatically handle file opening and closing
    try:
        with open(m4a_path, 'rb') as audio_file, open(json_path, 'rb') as json_file:
            data = {
                'key': rdio_data['rdio_api_key'],
                'system': rdio_data['system_id'],
                'audio': (os.path.basename(m4a_path), audio_file, 'audio/mpeg'),
                'meta': (os.path.basename(json_path), json_file, 'application/json')
            }
            response = requests.post(rdio_data['rdio_url'], files=data)
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

