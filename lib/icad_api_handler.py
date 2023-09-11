import requests
import logging


module_logger = logging.getLogger('icad_tr_uploader.icad_uploader')


def upload_to_icad(icad_data, mp3_path, call_data):

    module_logger.info(f'Uploading To iCAD Tone Detect API: {str(icad_data["icad_url"])}')

    if not call_data:
        module_logger.critical(f'Failed Uploading To iCAD API: Empty JSON')
        return False

    call_data["api_key"] = icad_data['icad_url']

    try:
        with open(mp3_path, 'rb') as audio_file:
            files = {'file': audio_file}
            data = call_data
            r = requests.post(icad_data['icad_url'], files=files, data=data)
            r.raise_for_status()

            module_logger.info(f'Successfully uploaded to iCAD API: {r.status_code}, {r.text}')

    except (FileNotFoundError, requests.exceptions.RequestException, IOError) as e:
        module_logger.critical(f'Failed Uploading To iCAD API: {str(e)} {r.status_code} {r.text}')
        return False

    return True
