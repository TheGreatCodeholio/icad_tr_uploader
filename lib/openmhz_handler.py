import os

import requests
import logging
import json

from requests_toolbelt.multipart.encoder import MultipartEncoder

module_logger = logging.getLogger('icad_tr_uploader.openmhz_uploader')


def upload_to_openmhz(openmhz, m4a_path, call_data):
    api_key = openmhz.get('api_key', None)
    short_name = openmhz.get('short_name', None)

    if not api_key or not short_name:
        module_logger.error("API Key or Short Name not found.")
        return False

    call_data["short_name"] = short_name
    call_data["api_key"] = api_key

    source_list = []
    if len(call_data.get('srcList', 0)) != 0:
        for source in call_data['srcList']:
            source_list.append({"pos": source['pos'], "src": source['src']})

    multipart_data = MultipartEncoder(
        fields={
            'call': (os.path.basename(m4a_path), open(m4a_path, 'rb'), 'application/octet-stream'),
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
        module_logger.info('Upload successful.')
    else:
        module_logger.error('Upload failed.')
    return response
