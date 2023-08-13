import json
import argparse
import os

from lib.audio_file_handler import convert_wav_mp3, archive_files, clean_files
from lib.file_save_handler import get_storage
from lib.icad_api_handler import upload_to_icad
from lib.logging_handler import CustomLogger
from lib.rdio_handler import upload_to_rdio
from lib.alertpage_handler import upload_to_alertpage

log_level = 1

app_name = "tr_uploader"

parser = argparse.ArgumentParser(description='Process Arguments.')
parser.add_argument("sys_name", help="System Name.")
parser.add_argument("audio_wav", help="Path to WAV.")

try:
    args = parser.parse_args()
except argparse.ArgumentError as e:
    # handle argument errors
    print(f'{e}')
    parser.print_usage()
    exit(1)
except Exception as e:
    # handle other exceptions
    print(f'{e}')
    exit(1)

root_path = os.getcwd()
config_file = 'etc/config.json'
config_path = os.path.abspath(os.path.join(root_path, config_file))
log_path = args.audio_wav.replace(".wav", ".log")

logger = CustomLogger(log_level, f'{app_name}', log_path).logger

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    f.close()
    system_name = args.sys_name
    system_config = config_data["systems"][system_name]
    file_storage_config = config_data["file_storage"]

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


def save_to_remote(mp3_file):
    try:
        with open(mp3_file, 'rb') as af:
            audio_data = af.read()
        af.close()

        storage_type = file_storage_config["storage_type"]
        storage = get_storage(storage_type, file_storage_config)

        remote_path = os.path.join(file_storage_config[file_storage_config["storage_type"]]["remote_path"],
                                   file_name.replace(".wav", ".mp3"))

        response = storage.upload_file(audio_data, remote_path)
        if not response:
            mp3_file_url = ""
        else:
            mp3_file_url = response["file_path"]

    except Exception as e:
        return ""

    return mp3_file_url


if not os.path.isfile(json_file):
    logger.error("No JSON File Created Exiting")
    exit(1)

with open(json_file, "r") as c_data:
    call_data = json.load(c_data)

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

    if call_data.get("talkgroup", 0) not in system_config["icad_api"]["talkgroups"]:
        logger.info(f"Not Sending to Tone Detect API not in talkgroups.")
    else:
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
        mp3_file_url = save_to_remote(mp3_file)
        upload_success = upload_to_alertpage(system_config["ap_api"], mp3_file, json_file,
                                             mp3_file_url)
        if not upload_success:
            logger.error("Failed to upload to AlertPage API Server.")
        else:
            logger.info(f"Successfully uploaded to AlertPage API server")
    else:
        logger.error("Can not send to AlertPage API Server. MP3 Compression not enabled.")

if system_config["archive_files"]:
    files = [log_path, json_file, mp3_file, m4a_file, wav_file]
    archive_files(files, system_config["archive_path"])
    clean_files(system_config["archive_path"], system_config["archive_days"])
else:
    for file in [log_path, json_file, mp3_file, m4a_file, wav_file]:
        if file.exists():
            try:
                file.unlink()
                print(f"{file} removed successfully.")
            except Exception as e:
                print(f"Failed to remove {file}. Reason: {str(e)}")
