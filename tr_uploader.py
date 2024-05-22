import json
import argparse
import os
import time
import traceback
from pathlib import Path

from lib.audio_file_handler import save_temporary_files, load_call_json
from lib.call_processor import process_tr_call
from lib.config_handler import load_config_file
from lib.logging_handler import CustomLogger

app_name = "icad_tr_uploader"
__version__ = "1.0"

root_path = os.getcwd()
config_file_name = "config.json"

log_file_name = f"{app_name}.log"

log_path = os.path.join(root_path, 'log')

if not os.path.exists(log_path):
    os.makedirs(log_path)

config_path = os.path.join(root_path, 'etc')

logging_instance = CustomLogger(1, f'{app_name}',
                                os.path.join(log_path, log_file_name))

try:
    config_data = load_config_file(os.path.join(config_path, config_file_name))
    logging_instance.set_log_level(config_data["log_level"])
    logger = logging_instance.logger
    logger.info("Loaded Config File")
except Exception as e:
    traceback.print_exc()
    print(f'Error while <<loading>> configuration : {e}')
    time.sleep(5)
    exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process Arguments.')
    parser.add_argument("-s", "--system_short_name", type=str, help="System Short Name.")
    parser.add_argument("-a", "--audio_wav_path", type=str, help="Path to WAV.")
    args = parser.parse_args()

    return args


def main():
    logger.debug("Running Main")

    args = parse_arguments()

    # copy files to tmp
    copy_result = save_temporary_files(config_data.get('temp_file_path', '/dev/shm'), args.audio_wav_path)
    if not copy_result:
        exit(1)

    # load call data
    call_data = load_call_json(os.path.join(config_data.get('temp_file_path', '/dev/shm'), os.path.basename(args.audio_wav_path).replace(".wav", ".json")))
    if not call_data:
        exit(1)

    # start call processing
    process_tr_call(config_data, os.path.join(config_data.get('temp_file_path', '/dev/shm'), os.path.basename(args.audio_wav_path)), call_data, args.system_short_name)


if __name__ == '__main__':
    main()
