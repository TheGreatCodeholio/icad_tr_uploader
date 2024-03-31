import logging
import os
import time
import traceback

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ParamValidationError

from paramiko import SSHClient, AutoAddPolicy, RSAKey, SSHException
from paramiko.sftp import SFTPError

module_logger = logging.getLogger('icad_tr_uploader.remote_storage')


def get_storage(remote_storage_config):
    if remote_storage_config.get("storage_type") == 'scp':
        return SCPStorage(remote_storage_config)
    elif remote_storage_config.get("storage_type") == 'google_cloud':
        return GoogleCloudStorage(remote_storage_config)
    elif remote_storage_config.get("storage_type") == 'aws_s3':
        return AWSS3Storage(remote_storage_config)
    else:
        module_logger.error('Invalid remote storage type.')


class GoogleCloudStorage:
    """
    A class to interact with Google Cloud Storage for uploading files.

    Attributes:
    -----------
    remote_path : str
        The remote path in the bucket where files will be stored.
    storage_client : google.cloud.storage.client.Client
        The Google Cloud Storage client.
    bucket_name : str
        The name of the bucket where files will be stored.
    bucket : google.cloud.storage.bucket.Bucket
        The Google Cloud Storage bucket object.

    Methods:
    --------
    upload_file(file, make_public=True):
        Uploads a file to Google Cloud Storage and optionally makes it public.
    """

    def __init__(self, config_data):
        """
        Initializes the GoogleCloudStorage object with configuration data.

        Parameters:
        -----------
        config_data : dict
            A dictionary containing the configuration for Google Cloud Storage.
            Must include 'google_cloud' sub-dictionary with 'credentials_path',
            'project_id', and 'bucket_name'. Also requires 'remote_path' for the
            destination path in the bucket.
        """
        try:
            google_cloud_config = config_data['google_cloud']
            self.remote_path = config_data['remote_path']

            self.storage_client = storage.Client.from_service_account_json(
                google_cloud_config['credentials_path'], project=google_cloud_config['project_id'])
            self.bucket_name = google_cloud_config['bucket_name']
            self.bucket = self.storage_client.get_bucket(self.bucket_name)
        except KeyError as e:
            module_logger.error(f"Google Cloud Missing required configuration data: {e}")
        except GoogleCloudError as e:
            module_logger.error(f"Google Cloud Storage error: {e}")

    def upload_file(self, local_audio_path, make_public=True):
        """
        Uploads a file to Google Cloud Storage and optionally makes it public.

        Parameters:
        -----------
        file : bytes or file-like object
            The file contents or a file-like object to upload.
        make_public : bool, optional
            If True, makes the uploaded file publicly accessible (default is True).

        Returns:
        --------
        str or None
            The public URL of the uploaded file if make_public is True, otherwise None.
            Returns None if the upload fails.
        """
        try:
            if self.bucket:
                blob = self.bucket.blob(self.remote_path)

                with open(local_audio_path, 'rb') as af:
                    blob.upload_from_file(af.read(), content_type='audio/aac')

                if make_public:
                    blob.make_public()

                return blob.public_url if make_public else None
            else:
                module_logger.warning("Google Storage Bucket is not available.")
                return None
        except GoogleCloudError as e:
            module_logger.error(f"Failed to upload file to Google Cloud Storage: {e}")
            return None


class AWSS3Storage:
    """
    A class to interact with Amazon S3 for uploading files.

    Attributes:
    -----------
    s3 : boto3.resource
        The Boto3 S3 resource.
    bucket_name : str
        The name of the S3 bucket where files will be stored.
    bucket : boto3.resource.Bucket
        The S3 Bucket object.
    remote_path : str
        The remote path in the bucket where files will be stored.

    Methods:
    --------
    upload_file(local_audio_path, make_public=True):
        Uploads a file to Amazon S3 and optionally makes it public.
    """

    def __init__(self, config_data):
        """
        Initializes the AWSS3Storage object with configuration data.

        Parameters:
        -----------
        config_data : dict
            A dictionary containing the configuration for Amazon S3. Must include
            'aws_s3' sub-dictionary with 'access_key_id', 'secret_access_key', and
            'bucket_name'. Also requires 'remote_path' for the destination path in the bucket.
        """
        try:
            aws_s3_config = config_data['aws_s3']

            self.s3 = boto3.resource(
                's3',
                aws_access_key_id=aws_s3_config['access_key_id'],
                aws_secret_access_key=aws_s3_config['secret_access_key']
            )
            self.bucket_name = aws_s3_config['bucket_name']
            self.bucket = self.s3.Bucket(self.bucket_name)
            self.remote_path = config_data['remote_path']
        except KeyError as e:
            module_logger.error(f"AWS S3 Missing required configuration data: {e}")
        except NoCredentialsError as e:
            module_logger.error(f"Credentials not available for AWS S3: {e}")

    def upload_file(self, local_audio_path, make_public=True):
        """
        Uploads a file to Amazon S3 and optionally makes it public.

        Parameters:
        -----------
        local_audio_path : str
            The local file path of the audio file to upload.
        make_public : bool, optional
            If True, makes the uploaded file publicly accessible (default is True).

        Returns:
        --------
        str or None
            The public URL of the uploaded file if make_public is True, otherwise None.
            Returns None if the upload fails.
        """
        try:
            with open(local_audio_path, 'rb') as file:
                self.bucket.put_object(Key=self.remote_path, Body=file)

            if make_public:
                self.s3.ObjectAcl(self.bucket_name, self.remote_path).put(ACL='public-read')

            return f"https://{self.bucket_name}.s3.amazonaws.com/{self.remote_path}" if make_public else None
        except FileNotFoundError:
            module_logger.error(f"Local file {local_audio_path} not found.")
            return None
        except (ClientError, ParamValidationError) as e:
            module_logger.error(f"Error uploading file to AWS S3: {e}")
            return None


class SCPStorage:
    def __init__(self, config_data):
        scp_config = config_data['scp']
        self.host = scp_config['host']
        self.port = scp_config['port']
        self.username = scp_config['user']
        self.password = scp_config['password']
        self.private_key_path = scp_config['private_key_path']
        self.base_url = scp_config['base_url']
        self.remote_path = config_data['remote_path']

    def upload_file(self, local_audio_path, max_attempts=3):
        """Uploads a file to the SCP storage.

        :param max_attempts: Maximum times we will try file upload if there is an SCP exception
        :param local_audio_path: The local path to the audio file to upload.
        :return: Dictionary containing the file URL or False if upload fails.
        """
        attempt = 0
        while attempt < max_attempts:
            try:
                full_remote_path = os.path.join(self.remote_path, os.path.basename(local_audio_path))
                ssh_client, sftp = self._create_sftp_session()

                if not os.path.exists(local_audio_path):
                    module_logger.error(f'Local File {local_audio_path} doesn\'t exist')
                    return False

                try:
                    sftp.stat(self.remote_path)
                except FileNotFoundError:
                    module_logger.error(f'Remote Path {self.remote_path} doesn\'t exist')
                    return False

                sftp.put(local_audio_path, full_remote_path)
                sftp.close()
                ssh_client.close()

                file_url = f"{self.base_url}/{os.path.basename(local_audio_path)}"

                return file_url
            except SFTPError as error:
                traceback.print_exc()
                module_logger.warning(f'Attempt {attempt + 1} failed during uploading a file: {error}')
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(5)
            except Exception as error:
                traceback.print_exc()
                module_logger.error(f'Error occurred during uploading a file: {error}')
                return False

        module_logger.error(f'All {max_attempts} attempts failed.')
        return False

    def _create_sftp_session(self):
        """Creates an SFTP session.

        :return: A tuple of SSH client and SFTP session.
        :raises: FileNotFoundError if private key file doesn't exist.
                  SSHException for other SSH connection errors.
        """
        ssh_client = SSHClient()
        ssh_client.load_system_host_keys()

        # Automatically add host key
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        try:
            # Use the private key for authentication instead of a password
            private_key = RSAKey.from_private_key_file(self.private_key_path)
            ssh_client.connect(self.host, port=self.port, username=self.username, pkey=private_key,
                               look_for_keys=False, allow_agent=False)
        except FileNotFoundError as e:
            module_logger.error(f'Private key file not found: {e}')
            raise FileNotFoundError(f'Private key file not found: {e}')
        except SSHException as e:
            module_logger.error(f'SSH connection error: {e}')
            raise SSHException(f'SSH connection error: {e}')

        sftp = ssh_client.open_sftp()
        return ssh_client, sftp
