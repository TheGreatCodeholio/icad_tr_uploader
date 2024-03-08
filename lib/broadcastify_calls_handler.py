import logging
import os
from urllib.error import HTTPError

import requests
import urllib3

module_logger = logging.getLogger('icad_tr_uploader.broadcastify_calls')


def send_request(method, url, **kwargs):
    """
    Send an HTTP request using the requests library and return the response object.
    Handles exceptions and logs errors.
    """
    try:
        response = requests.request(method, url, **kwargs)
        if response.status_code != 200:
            module_logger.critical(f"HTTP request failed with status {response.status_code}: {response.text}")
            return None
        return response
    except requests.exceptions.RequestException as e:
        module_logger.critical(f"HTTP request encountered an error: {e}")
        return None


def upload_to_broadcastify_calls(broadcastify_config, m4a_file_path, call_data):
    module_logger.info("Uploading to Broadcastify Calls")

    broadcastify_url = "https://api.broadcastify.com/call-upload"
    module_logger.info("Requesting Call Upload Url")

    files = {
        'metadata': (os.path.basename(m4a_file_path.replace(".m4a", ".json")), open(m4a_file_path.replace(".m4a", ".json"), 'rb'), 'application/json'),
        'audio': (os.path.basename(m4a_file_path), open(m4a_file_path, 'rb'), 'audio/aac'),
        'callDuration': (None, str(call_data["call_length"])),
        'systemId': (None, str(broadcastify_config["system_id"])),
        'apiKey': (None, broadcastify_config["api_key"]),
    }

    upload_request_response = requests.post(broadcastify_url, files=files)
    if not upload_request_response:
        return False

    module_logger.info("Uploading Call Audio")
    response_data = upload_request_response
    if response_data.status_code == 200:
        upload_url = response_data.text.split(" ")[1]
    else:
        module_logger.error("Unable to get Upload URL from Broadcastify Calls")
        return False

    try:
        with open(m4a_file_path, 'rb') as up_file:
            file_data = up_file.read()
    except IOError as e:
        module_logger.critical(f"Failed to read the audio file: {e}")
        return False

    upload_response = send_request('PUT', upload_url, headers={'Content-Type': 'audio/aac'}, body=file_data)
    if not upload_response:
        module_logger.debug("Uploading Audio to Broadcastify Calls Failed.")
        return False

    if upload_response.status_code == 200:
        module_logger.info("Broadcastify Calls Audio Upload Complete")
        return True

    module_logger.debug("Uploading Audio to Broadcastify Calls Failed.")
    return False
