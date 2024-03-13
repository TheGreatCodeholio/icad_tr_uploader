import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.transcribe')


def upload_to_transcribe(transcribe_config, audio_file_path):
    url = transcribe_config['api_url']
    module_logger.info(f'Uploading To Transcribe API: {url}')

    # Use context managers to automatically handle file opening and closing
    try:
        with open(audio_file_path, 'rb') as af:
            data = {
                'file': af,
            }
            response = requests.post(url, files=data)
            response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
            response_json = response.json()
            module_logger.info(f'Successfully received transcript data from: {url}')
            module_logger.debug(f'{response_json}')

            # Check if the status in the response is not 'ok'
            if response_json.get('status') != 'ok':
                raise ValueError(f"Expected status 'ok' but got {response_json.get('status')}")

            return response_json
    except FileNotFoundError as e:
        module_logger.error(f'Transcribe - Audio File not found {audio_file_path}: {e}')
        return None
    except requests.exceptions.RequestException as e:
        # This captures HTTP errors, connection errors, etc.
        module_logger.error(f'Failed Uploading To Transcribe {url}: {e}')
        return None
    except ValueError as e:
        # Specific error when the 'status' in response is not 'ok'
        module_logger.error(f'Error in response status: {e}')
        return None
    except Exception as e:
        # Catch-all for any other unexpected errors
        module_logger.error(f'An unexpected error occurred while upload to Transcribe API {url}: {e}')
        return None
