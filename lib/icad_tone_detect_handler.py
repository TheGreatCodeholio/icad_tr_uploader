import json
import os

import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.icad_uploader')


def upload_to_icad_legacy(icad_data, mp3_path, call_data):
    module_logger.info(f'Uploading to iCAD Tone Detect API: {icad_data["icad_url"]}')

    if not call_data:
        module_logger.error('Failed uploading to iCAD API: Empty call_data JSON')
        return False

    # This should likely be setting a correct API key field from icad_data if it exists.
    call_data["api_key"] = icad_data.get('api_key')

    try:
        with open(mp3_path, 'rb') as audio_file:
            files = {'file': (mp3_path, audio_file, 'audio/mpeg')}
            response = requests.post(icad_data['icad_url'], files=files, data=call_data)
            response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
            module_logger.info(f'Successfully uploaded to iCAD API: {response.status_code}, {response.text}')
            return True

    except FileNotFoundError:
        module_logger.error(f'File not found: {mp3_path}')
    except requests.exceptions.HTTPError as e:
        # This captures HTTP errors and logs them. `e.response` contains the response that caused this error.
        module_logger.error(f'HTTP error uploading to iCAD API: {e.response.status_code}, {e.response.text}')
    except requests.exceptions.RequestException as e:
        # This captures other requests-related errors
        module_logger.error(f'Error uploading to iCAD API: {e}')
    except IOError as e:
        # This captures general IO errors (broader than just FileNotFoundError)
        module_logger.error(f'IO error with file: {mp3_path}, {e}')

    return False


def upload_to_icad(icad_data, m4a_path, json_path):
    module_logger.info(f'Uploading to iCAD Tone Detect API: {icad_data["icad_url"]}')

    try:
        with open(m4a_path, 'rb') as af, open(json_path, 'rb') as jf:
            files = {'audioFile': (os.path.basename(m4a_path), af, 'application/octet-stream'),
                     'jsonFile': (os.path.basename(json_path), jf, 'application/json')}
            response = requests.post(icad_data['icad_url'], files=files)
            response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
            module_logger.info(f'Successfully uploaded to iCAD API: {response.status_code}, {response.text}')

            detect_data = json.loads(response.text)
            return detect_data

    except FileNotFoundError:
        module_logger.error(f'File not found: {m4a_path} or {json_path}')
    except requests.exceptions.HTTPError as e:
        # This captures HTTP errors and logs them. `e.response` contains the response that caused this error.
        module_logger.error(f'HTTP error uploading to iCAD API: {e.response.status_code}, {e.response.text}')
    except requests.exceptions.RequestException as e:
        # This captures other requests-related errors
        module_logger.error(f'Error uploading to iCAD API: {e}')
    except IOError as e:
        # This captures general IO errors (broader than just FileNotFoundError)
        module_logger.error(f'IO error with file: {m4a_path} or {json_path}, {e}')

    return False
