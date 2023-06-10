import json
import os
import logging
import time
import datetime

import urllib3
from colorama import Fore, Style
from pydub import AudioSegment

module_logger = logging.getLogger('icad_tr_uploader.broadcastify_calls')


# post_call(int(time.time()), "test.wav") example request
# process steps
# load wav file - convert to m4a 32k with 22050 bitrate
# load mp4 get length
# send upload request
# get back url
# read m4a file as data
# put m4a file to the url


def post_call(icad_config, json_file_path, m4a_file_path):
    module_logger.debug(Fore.YELLOW + "Uploading to Broadcastify Calls" + Style.RESET_ALL)

    call_data = open(json_file_path, 'r')
    call_json = json.load(call_data)

    call_length = call_json["call_length"]
    call_timestamp = call_json["stop_time"]
    call_talkgroup = call_json[""]

    broadcastify_url = "https://api.broadcastify.com/call-upload"
    module_logger.debug(Fore.YELLOW + "Requesting Call Upload Url" + Style.RESET_ALL)

    data = {'apiKey': icad_config["broadcastify_settings"]["calls_api_key"],
                'systemId': icad_config["broadcastify_settings"]["calls_system_id"], 'callDuration': str(call_duration),
                'ts': str(call_timestamp), 'tg': "",
                'freq': icad_config["broadcastify_settings"]["calls_frequency"],
                'enc': 'm4a'}