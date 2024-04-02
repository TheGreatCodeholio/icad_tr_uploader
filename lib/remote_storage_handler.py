import datetime
import logging
import os
import time
import traceback
from stat import S_ISDIR

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
        Uploads a file to Google Cloud Storage into a date-based directory structure and optionally makes it public.

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
            current_date = datetime.datetime.utcnow()
            date_path = f"{current_date.year}/{current_date.month}/{current_date.day}"
            remote_path = f"{date_path}/{os.path.basename(local_audio_path)}"  # Updated remote path with date

            if self.bucket:
                blob = self.bucket.blob(remote_path)

                with open(local_audio_path, 'rb') as af:
                    blob.upload_from_file(af, content_type='audio/aac')  # Use af directly instead of af.read()

                if make_public:
                    blob.make_public()

                return blob.public_url if make_public else None
            else:
                module_logger.warning("Google Storage Bucket is not available.")
                return None
        except GoogleCloudError as e:
            module_logger.error(f"Failed to upload file to Google Cloud Storage: {e}")
            return None

    def clean_remote_files(self, archive_days):
        """
        Deletes files from Google Cloud Storage that are older than a specified number of days.
        Identifies empty directories for potential cleanup.

        Parameters:
        -----------
        archive_days : int
            The number of days after which files should be deleted.
        """
        try:
            blobs = self.bucket.list_blobs()
            now = datetime.datetime.utcnow()
            for blob in blobs:
                if (now - blob.time_created).days > archive_days:
                    print(f"Deleting: {blob.name}")
                    blob.delete()

            # Google Cloud Storage does not support empty directories in the same way
            # traditional file systems do, since it is object-based.
            # Thus, "cleaning" directories would typically involve removing 'directory' objects
            # or objects with paths that no longer contain files. This can be complex and
            # often unnecessary unless you have specific organizational needs for it.

        except GoogleCloudError as e:
            module_logger.error(f"Failed to clean Google Cloud Storage: {e}")


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
        Uploads a file to Amazon S3 into a date-based directory structure and optionally makes it public.

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
        current_date = datetime.datetime.utcnow()
        date_path = f"{current_date.year}/{current_date.month}/{current_date.day}"
        remote_path = f"{date_path}/{os.path.basename(local_audio_path)}"  # Include the date in the remote path

        try:
            with open(local_audio_path, 'rb') as file:
                self.bucket.put_object(Key=remote_path, Body=file)  # Use the updated remote path

            if make_public:
                self.s3.ObjectAcl(self.bucket_name, remote_path).put(ACL='public-read')

            return f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}" if make_public else None
        except FileNotFoundError:
            module_logger.error(f"Local file {local_audio_path} not found.")
            return None
        except (ClientError, ParamValidationError) as e:
            module_logger.error(f"Error uploading file to AWS S3: {e}")
            return None

    def clean_remote_files(self, archive_days):
        """
        Deletes files from an S3 bucket that are older than a specified number of days.

        Parameters:
        -----------
        archive_days : int
            The number of days after which files should be deleted.
        """
        s3_client = boto3.client('s3')
        bucket_name = self.bucket_name  # Your S3 bucket name

        try:
            # List all objects within the bucket
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket_name)

            for page in page_iterator:
                if "Contents" in page:
                    for obj in page['Contents']:
                        last_modified = obj['LastModified']
                        if last_modified < datetime.datetime.utcnow().replace(tzinfo=None) - datetime.timedelta(days=archive_days):
                            print(f"Deleting {obj['Key']}")
                            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

            # Additional logic for removing empty 'directories' could be implemented here
            # Note: S3 does not actually have directories, but you can check for and delete empty prefixes
        except ClientError as e:
            module_logger.error(f"Error cleaning S3 files: {e}")


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
        """Uploads a file to the SCP storage with a date-based directory structure.

        :param max_attempts: Maximum times we will try file upload if there is an SCP exception
        :param local_audio_path: The local path to the audio file to upload.
        :return: Dictionary containing the file URL or False if upload fails.
        """
        attempt = 0
        current_date = datetime.datetime.utcnow()
        date_path = os.path.join(str(current_date.year), str(current_date.month), str(current_date.day))
        remote_directory = os.path.join(self.remote_path, date_path)

        while attempt < max_attempts:
            try:
                ssh_client, sftp = self._create_sftp_session()

                # Check if local file exists
                if not os.path.exists(local_audio_path):
                    module_logger.error(f'Local File {local_audio_path} doesn\'t exist')
                    return False

                # Ensure the remote directory exists or create it
                nested_dirs = remote_directory.split('/')
                current_dir = ''
                for dir in nested_dirs:
                    current_dir = os.path.join(current_dir, dir) if current_dir else dir
                    try:
                        sftp.chdir(current_dir)  # Try to change to the directory
                    except FileNotFoundError:  # Corrected to catch FileNotFoundError
                        sftp.mkdir(current_dir)  # Create if it does not exist
                        sftp.chdir(current_dir)

                # Upload the file
                remote_file_path = os.path.join(remote_directory, os.path.basename(local_audio_path))
                sftp.put(local_audio_path, remote_file_path)
                sftp.close()
                ssh_client.close()

                file_url = f"{self.base_url}/{date_path}/{os.path.basename(local_audio_path)}"
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

    def clean_remote_files(self, archive_days):
        """Removes files older than a specified number of days within the remote archive path.

        :param archive_days: The age in days beyond which files should be removed.
        """
        try:
            ssh_client, sftp = self._create_sftp_session()
            current_time = time.time()
            count = 0

            # Recursive function to traverse and clean directories
            def clean_directory(path):
                nonlocal count
                try:
                    for entry in sftp.listdir_attr(path):
                        remote_path = os.path.join(path, entry.filename)
                        if S_ISDIR(entry.st_mode):  # If entry is a directory, recurse into it
                            clean_directory(remote_path)
                            # Try to remove the directory if it's empty
                            try:
                                sftp.rmdir(remote_path)
                            except IOError:
                                pass  # Directory not empty
                        else:
                            file_time = entry.st_mtime
                            days_difference = (current_time - file_time) / (24 * 3600)
                            if days_difference >= archive_days:
                                sftp.remove(remote_path)
                                count += 1
                                module_logger.debug(f"Successfully cleaned remote file: {remote_path}")
                except Exception as e:
                    module_logger.error(f"Failed to clean directory: {path}, Error: {e}")

            clean_directory(self.remote_path)
            module_logger.info(f"Cleaned {count} files remotely.")
        except Exception as e:
            module_logger.error(f"Error during remote cleanup: {e}")
        finally:
            if sftp:
                sftp.close()
            if ssh_client:
                ssh_client.close()

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
