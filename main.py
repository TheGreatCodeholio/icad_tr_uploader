import json

import traceback
import argparse
import os
import time

from lib.audio_file_handler import convert_wav_mp3, convert_wav_m4a
from lib.icad_api_handler import upload_to_icad
from lib.logging_handler import CustomLogger
from lib.rdio_handler import upload_to_rdio
from lib.alertpage_handler import upload_to_alertpage

log_level = 1

app_name = "tr_uploader"

parser = argparse.ArgumentParser(description='Process Arguments.')
parser.add_argument("sys_name", help="System Name.")
parser.add_argument("audio_wav", help="Path to WAV.")

root_path = os.getcwd()
config_file = 'etc/config.json'
config_path = os.path.abspath(os.path.join(root_path, config_file))
log_path = os.path.abspath(os.path.join(root_path, 'log'))
log_file_name = f"{app_name}.log"

if not os.path.exists(log_path):
    os.makedirs(log_path)

logger = CustomLogger(log_level, f'{app_name}', os.path.abspath(os.path.join(log_path, log_file_name))).logger

try:
    args = parser.parse_args()
except argparse.ArgumentError as e:
    # handle argument errors
    logger.error(f'{e}')
    parser.print_usage()
    exit(1)
except Exception as e:
    # handle other exceptions
    logger.error(f'{e}')
    exit(1)

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    f.close()
    system_name = args.sys_name
    system_config = config_data["systems"][system_name]
    file_storage_config = config_data["file_storage"]

    # Create our file variables.
    log_path = args.audio_wav.replace(".wav", ".log")
    json_file = args.audio_wav.replace(".wav", ".json")
    mp3_file = args.audio_wav.replace(".wav", ".mp3")
    m4a_file = args.audio_wav.replace(".wav", ".m4a")
    wav_file = args.audio_wav
    file_name = wav_file.split('/')[-1]
    file_path = wav_file.replace("/" + file_name, "")

except FileNotFoundError:
    logger.error(f'Configuration file {config_file} not found.')
    exit(1)
except json.JSONDecodeError:
    logger.error(f'Configuration file {config_file} is not in valid JSON format.')
    exit(1)
else:
    logger.info(f'Successfully loaded configuration from {config_file}')

# compress to mp3 if enabled
mp3_exists = os.path.isfile(mp3_file)
if system_config["compress_mp3"] == 1 and not mp3_exists:
    error_message = convert_wav_mp3(system_config, wav_file)
    if error_message:
        logger.error(f"Exiting due to error: {error_message}")
        exit(1)
    mp3_exists = True

m4a_exists = os.path.isfile(m4a_file)
if system_config["compress_m4a"] == 1 and not m4a_exists:
    error_message = convert_wav_m4a(system_config, wav_file)
    if error_message:
        logger.error(f"Exiting due to error: {error_message}")
        exit(1)
    m4a_exists = True

# Upload to RDIO
for rdio in system_config["rdio_systems"]:
    if system_config["compress_mp3"] == 1 or mp3_exists:
        if rdio["system_enabled"] == 1:
            try:
                upload_to_rdio(rdio, mp3_file, json_file)
                logger.info(f"Successfully uploaded to RDIO server: {rdio['rdio_url']}")
            except Exception as e:
                logger.error(f"Failed to upload to RDIO server: {rdio['rdio_url']}. Error: {str(e)}", exc_info=True)
                continue
        else:
            logger.info(f"RDIO system is disabled: {rdio['rdio_url']}")
            continue
    else:
        logger.error("Can not send to RDIO Server. MP3 Compression not enabled.")
        continue

# Upload to iCAD API
if system_config["icad_api"]["enabled"] == 1:
    if system_config["compress_mp3"] == 1 or mp3_exists:
        upload_success = upload_to_icad(system_config["icad_api"], mp3_file, json_file)
        if not upload_success:
            logger.error("Failed to upload to iCAD API Server.")
        else:
            logger.info(f"Successfully uploaded to iCAD API server: {system_config['icad_api']['icad_url']}")
    else:
        logger.error("Can not send to iCAD API Server. MP3 Compression not enabled.")

# Upload to AlertPage
if system_config["ap_api"]["enabled"] == 1:
    if system_config["compress_mp3"] == 1 or mp3_exists:
        upload_success = upload_to_alertpage(file_storage_config, system_config["ap_api"], mp3_file, json_file)
        if not upload_success:
            logger.error("Failed to upload to AlertPage API Server.")
        else:
            logger.info(f"Successfully uploaded to AlertPage API server")
    else:
        logger.error("Can not send to AlertPage API Server. MP3 Compression not enabled.")

current_time = time.time()
count = 0
for f in os.listdir(file_path):
    path = os.path.join(file_path, f)
    creation_time = os.path.getctime(path)
    if (current_time - creation_time) // (24 * 3600) >= system_config["keep_audio_days"]:
        try:
            os.unlink(path)
            count += 1
            logger.debug(f"Successfully cleaned file: {path}")
        except Exception as e:
            logger.error(f"Failed to clean file: {path}, Error: {str(e)}")
            traceback.print_exc()

logger.debug(f"Cleaned {count} files.")