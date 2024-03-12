import base64
import logging
import os
import time

import requests

module_logger = logging.getLogger('icad_tr_uploader.broadcastify_calls')


def send_request(method, url, **kwargs):
    """
    Send an HTTP request using the requests library and return the response object.
    Handles exceptions and logs errors with more context.
    """
    try:
        response = requests.request(method, url, **kwargs)
        if response.status_code != 200:
            module_logger.error(
                f"Error in {method} request to {url}: Status {response.status_code}, Response: {response.text}")
            return None
        return response
    except requests.exceptions.RequestException as e:
        module_logger.error(f"Exception during {method} request to {url}: {e}")
        return None


def upload_to_broadcastify_calls(broadcastify_config, m4a_file_path, call_data):
    module_logger.info("Uploading to Broadcastify Calls")

    broadcastify_url = "https://api.broadcastify.com/call-upload"
    metadata_path = m4a_file_path.replace(".m4a", ".json")

    headers = {
        "User-Agent": "TrunkRecorder1.0"
    }

    try:
        with open(m4a_file_path, 'rb') as audio_file:
            files = {
                'apiKey': (None, broadcastify_config["api_key"]),
                'systemId': (None, str(broadcastify_config["system_id"])),
                'ts': str(time.time()),
                'tg': str(call_data['talkgroup']),
                'freq': str(call_data["freq"]),
                'callDuration': (None, str(call_data["call_length"]))
            }

            print(files)

            response = requests.post(broadcastify_url, headers, files=files)
            module_logger.debug(response.text)
            if response.status_code != 200:
                module_logger.error(
                    f"Failed to upload to Broadcastify Calls: Status {response.status_code}, Response: {response.text}")
                return False

            # Assuming the response contains JSON with a direct URL for uploading
            try:
                upload_url = response.text.split(" ")[1]
                if not upload_url:
                    module_logger.error("Upload URL not found in the Broadcastify response.")
                    return False
            except ValueError:
                module_logger.error("Failed to parse response from Broadcastify as JSON.")
                return False

            #base_64 = base64.b64encode(audio_file.read()).decode("utf-8")
            fields = {
                "filefield": (os.path.basename(m4a_file_path), audio_file, 'audio/aac')
            }

            # Reuse the send_request function for the PUT request
            upload_response = send_request('PUT', upload_url, headers={'Content-Type': 'audio/aac'}, data=audio_file.read())
            module_logger.debug(upload_response.text)
            if not upload_response:
                module_logger.error("Failed to post call to Broadcastify Calls AWS Failed.")
                return False

            module_logger.info("Broadcastify Calls Audio Upload Complete")
            return True
    except IOError as e:
        module_logger.error(f"File error: {e}")
        return False
