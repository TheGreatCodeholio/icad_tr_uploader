import requests
import logging

module_logger = logging.getLogger('icad_tr_uploader.icad_player_upload')


def upload_to_icad_player(player_config, call_data):
    url = player_config['api_url']
    module_logger.info(f'Uploading To iCAD Player: {url}')

    try:
        response = requests.post(url, json=call_data)

        response.raise_for_status()
        module_logger.info(
            f"Successfully uploaded to iCAD Player: {url}")
        return True
    except requests.exceptions.RequestException as e:
        # This captures HTTP errors, connection errors, etc.
        module_logger.error(f'Failed Uploading To iCAD Player: {e}')
    except Exception as e:
        # Catch-all for any other unexpected errors
        module_logger.error(f'An unexpected error occurred while upload to iCAD Player {url}: {e}')

    return False
