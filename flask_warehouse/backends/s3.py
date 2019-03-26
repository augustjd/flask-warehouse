from tempfile import SpooledTemporaryFile

from flask import Flask

import boto3
from botocore.exceptions import ClientError

from .service import Bucket, Cubby, Service


class S3Service(Service):
    def __init__(self, app: Flask, aws_access_key_id=None, aws_secret_access_key=None, default_location=None):
        super().__init__('s3', default_location=default_location)

        self.session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key,
                                     region_name=default_location)

        self.s3 = boto3.resource('s3')
        self.client = boto3.client('s3')

        try:
            self.client.list_buckets()
        except Exception:
            raise Exception("Failed to connect to S3 - ensure that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are both set.")


class S3Bucket(Bucket):
    def __init__(self, service: S3Service, name: str, location: str):
        super().__init__(service, name, location)

        self._bucket = self.service.s3.Bucket(name)

        try:
            bucket_configuration = {'LocationConstraint': location}
            self._bucket.create(CreateBucketConfiguration=bucket_configuration)
        except ClientError:
            pass

    def cubby(self, name, content_type=None, acl='public-read'):
        return S3Cubby(self, name, content_type=content_type, acl=acl)

    def delete(self):
        self._bucket.delete()

    def list(self, prefix=None, max_keys=None, **kwargs):
        if prefix is not None:
            kwargs['Prefix'] = prefix
        if max_keys is not None:
            kwargs['MaxKeys'] = max_keys

        keys = self._bucket.objects.filter(**kwargs)

        return [S3Cubby(self, key.key) for key in keys]


class S3Cubby(Cubby):
    def __init__(self, bucket, name, content_type=None, acl=None, key=None):
        super().__init__(bucket, name)

        self.content_type = content_type

        if key is None:
            self._key = self.bucket._bucket.Object(name)
        else:
            self._key = key
            self.name = self._key.name

        self.acl = acl

    def store_filelike(self, filelike, tempcopy=False):
        if tempcopy:
            copy = SpooledTemporaryFile()  # boto3 now closes the file.
            copy.write(filelike.read())
            copy.seek(0)

            filelike = copy

        ExtraArgs = {}

        if self.acl:
            ExtraArgs['ACL'] = self.acl

        if self.content_type:
            ExtraArgs['ContentType'] = self.content_type

        self._key.upload_fileobj(filelike, ExtraArgs=ExtraArgs)

        return self.url()

    def retrieve_filelike(self, filelike):
        if filelike.closed:
            raise Exception("File provided was already closed.")

        return self._key.download_fileobj(filelike)

    def url(self, expiration=Cubby.DefaultUrlExpiration):
        service: S3Service = self.bucket.service
        result = service.client.generate_presigned_url('get_object',
                                                       Params={
                                                           "Bucket": self.bucket.name,
                                                           "Key": self.key
                                                       },
                                                       ExpiresIn=int(expiration.total_seconds()) if expiration else None)

        if expiration is None:
            # chop off ?AWSAccessKeyId= etc. - if public, this will work.
            result = result.split('?')[0]

        return result

    def delete(self):
        self._key.delete()
        return not self.exists()

    def filesize(self):
        return self._key.content_length

    def exists(self):
        matches = list(self.bucket._bucket.objects.filter(Prefix=self.key))
        return len(matches) > 0 and matches[0].key == self.key


S3Service.__bucket_class__ = S3Bucket
