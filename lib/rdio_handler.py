import requests
import logging

module_logger = logging.getLogger('ap_tr_uploader.rdio_uploader')


def upload_to_rdio(rdio_data, mp3_path, json_path):
    module_logger.info(f'Uploading To RDIO: {str(rdio_data["rdio_url"])}')
    try:
        with open(mp3_path, 'rb') as audio_file, open(json_path, 'rb') as json_file:
            data = {
                'key': rdio_data['rdio_api_key'],
                'system': rdio_data['system_id'],
                'audio': (mp3_path.split('/')[-1], audio_file, 'audio/mpeg'),
                'meta': (json_path.split('/')[-1], json_file, 'application/json')
            }
            r = requests.post(rdio_data['rdio_url'], files=data)
            r.raise_for_status()
    except FileNotFoundError as e:
        module_logger.critical(f'File not found: {str(e)}')
    except (requests.exceptions.RequestException, IOError) as e:
        module_logger.critical(f'Failed Uploading To RDIO: {str(e)}')

    try:
        audio_file.close()
    except NameError:
        pass
    try:
        json_file.close()
    except NameError:
        pass
