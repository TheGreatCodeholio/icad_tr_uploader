from google.cloud import storage
import boto3


def get_storage(storage_type, config_data):
    if storage_type == 'google_cloud':
        return GoogleCloudStorage(config_data)
    elif storage_type == 'aws_s3':
        return AWSS3Storage(config_data)
    else:
        raise ValueError(f"Invalid storage type: {storage_type}")


class GoogleCloudStorage:
    def __init__(self, config_data):
        google_cloud_config = config_data['google_cloud']

        self.storage_client = storage.Client.from_service_account_json(
            google_cloud_config['credentials_path'], project=google_cloud_config['project_id'])
        self.bucket_name = google_cloud_config['bucket_name']
        self.bucket = self.storage_client.get_bucket(self.bucket_name)

    def upload_file(self, file, remote_path, make_public=True):
        if self.bucket:
            # Read the contents of the file into memory
            file_contents = file

            blob = self.bucket.blob(remote_path)
            blob.upload_from_string(file_contents)

            if make_public:
                blob.make_public()



            public_url = blob.public_url if make_public else None
            return {"file_path": public_url}

    def download_file(self, remote_path, local_path):
        if self.bucket:
            blob = self.bucket.blob(remote_path)
            blob.download_to_filename(local_path)

    def delete_file(self, remote_path):
        if self.bucket:
            blob = self.bucket.blob(remote_path)
            blob.delete()

    def list_files(self, prefix=None):
        if self.bucket:
            blobs = self.storage_client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]


class AWSS3Storage:
    def __init__(self, config_data):
        aws_s3_config = config_data['aws_s3']

        self.s3 = boto3.resource(
            's3',
            aws_access_key_id=aws_s3_config['access_key_id'],
            aws_secret_access_key=aws_s3_config['secret_access_key']
        )
        self.bucket_name = aws_s3_config['bucket_name']
        self.bucket = self.s3.Bucket(self.bucket_name)

    def upload_file(self, file, remote_path, make_public=True):
        if self.bucket:
            # Read the contents of the file into memory
            file_contents = file

            # Upload the file from memory
            obj = self.bucket.put_object(Key=remote_path, Body=file_contents)

            if make_public:
                obj.Acl().put(ACL='public-read')

            public_url = f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}" if make_public else None

            return {"file_path": public_url}

    def download_file(self, remote_path, local_path):
        if self.bucket:
            self.bucket.download_file(remote_path, local_path)

    def delete_file(self, remote_path):
        if self.bucket:
            self.s3.Object(self.bucket_name, remote_path).delete()

    def list_files(self, prefix=None):
        if self.bucket:
            return [obj.key for obj in self.bucket.objects.filter(Prefix=prefix)]
