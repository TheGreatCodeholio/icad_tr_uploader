import logging
from urllib.error import HTTPError

import urllib3

module_logger = logging.getLogger('icad_tr_uploader.broadcastify_calls')


def send_request(http, method, url, **kwargs):
    """
    Send an HTTP request and return the response object.
    Handles exceptions and logs errors.
    """
    try:
        response = http.request(method, url, **kwargs)
        if response.status != 200:
            module_logger.critical(f"HTTP request failed with status {response.status}: {response.data}")
            return None
        return response
    except HTTPError as e:
        module_logger.critical(f"HTTP request encountered an error: {e}")
        return None


def upload_to_broadcastify_calls(broadcastify_config, m4a_file_path, call_data):
    module_logger.info("Uploading to Broadcastify Calls")

    broadcastify_url = "https://api.broadcastify.com/call-upload"
    module_logger.info("Requesting Call Upload Url")

    http = urllib3.PoolManager()
    upload_request_response = send_request(
        http, 'POST', broadcastify_url,
        fields={
            'apiKey': broadcastify_config["api_key"],
            'systemId': broadcastify_config["system_id"],
            'callDuration': str(call_data["call_length"]),
            'ts': str(call_data['start_time']),
            'tg': str(call_data['talkgroup']) if broadcastify_config["calls_slot"] == -1 else str(broadcastify_config["calls_slot"]),
            'freq': str(call_data['freq']),
            'enc': 'm4a'
        }
    )

    if not upload_request_response:
        return False

    module_logger.info("Uploading Call Audio")
    response_data = upload_request_response.data.decode('utf-8').split(' ')
    upload_url = response_data[1]

    try:
        with open(m4a_file_path, 'rb') as up_file:
            file_data = up_file.read()
    except IOError as e:
        module_logger.critical(f"Failed to read the audio file: {e}")
        return False

    upload_response = send_request(http, 'PUT', upload_url, headers={'Content-Type': 'audio/aac'}, body=file_data)
    if upload_response:
        module_logger.info("Upload Call Audio Complete")
        return True

    return False
