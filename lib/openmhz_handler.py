import os

import requests
import logging
import json

from requests_toolbelt.multipart.encoder import MultipartEncoder

module_logger = logging.getLogger('icad_tr_uploader.openmhz_uploader')


def upload_to_openmhz(openmhz, m4a_file_path, call_data):
    try:
        module_logger.info("Sending to OpenMHZ")
        api_key = openmhz.get('api_key')
        short_name = openmhz.get('short_name')

        if not api_key or not short_name:
            module_logger.error("Upload to <<OpenMHZ>> <<failed>> API Key or Short Name not provided in the <<OpenMHZ>> configuration.")
            return False

        source_list = []
        if 'srcList' in call_data and len(call_data['srcList']) != 0:
            for source in call_data['srcList']:
                source_list.append({"pos": source['pos'], "src": source['src']})

        multipart_data = MultipartEncoder(
            fields={
                'call': (os.path.basename(m4a_file_path), open(m4a_file_path, 'rb'), 'application/octet-stream'),
                'freq': str(call_data['freq']),
                'error_count': str(0),
                'spike_count': str(0),
                'start_time': str(call_data['start_time']),
                'stop_time': str(call_data['start_time'] + call_data["call_length"]),
                'call_length': str(call_data["call_length"]),
                'talkgroup_num': str(call_data["talkgroup"]),
                'emergency': str(0),
                'api_key': api_key,
                'source_list': json.dumps(source_list)
            }
        )

        session = requests.Session()
        response = session.post(
            url=f"https://api.openmhz.com/{short_name}/upload",
            data=multipart_data,
            headers={'User-Agent': 'TrunkRecorder1.0', 'Content-Type': multipart_data.content_type}
        )

        if response.status_code == 200:
            module_logger.info('Upload to <<OpenMHZ>> <<successful>>.')
            return True
        else:
            module_logger.error(f'Upload to <<OpenMHZ>> <<failed>> with status code {response.status_code}: {response.text}')
            return False
    except requests.exceptions.RequestException as e:
        module_logger.error(f"Upload to <<OpenMHZ>> <<failed> OpenMHZ failed: {e}")
        return False
    except Exception as e:
        module_logger.error(f"An unexpected <<error>> occurred while uploading to <<OpenMHZ>>: {e}")
        return False
