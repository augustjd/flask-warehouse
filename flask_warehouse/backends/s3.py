import gzip

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

        self._bucket: boto3.s3.bucket.Bucket = self.service.s3.Bucket(name)

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

    def __eq__(self, other):
        if not isinstance(other, S3Bucket):
            return False
        
        return (self.service == other.service 
        and self.name == other.name 
        and self.location == other.location)

    def copy_key(self, dst_key: str, src_key: str, src_bucket_name: str = None):
        if src_bucket_name is None:
            src_bucket_name = self.name

        self._bucket.copy({"Bucket":src_bucket_name, "Key": src_key}, dst_key)


class S3Cubby(Cubby):
    def __init__(self, bucket: S3Bucket, name, content_type=None, acl=None, key=None):
        super().__init__(bucket, name)

        self.content_type = content_type

        if key is None:
            self._key = self.bucket._bucket.Object(name)
        else:
            self._key = key
            self.key = self._key.nameG

        self.acl = acl

    @staticmethod
    def apply_func_filelike(filelike, fn):
        """Applies a function to content in a file like object.

            fn: a function that accepts a single argument of the original content, and returns a single
                variable as the updated content.
        """
        content = filelike.read()
        content = fn(content)

        # replace the content in the file like object
        filelike.seek(0)
        filelike.write(content)
        filelike.truncate()

        # seek back to the start so the filelike object is usable
        filelike.seek(0)

    def store_filelike(self, filelike, tempcopy=False):
        if tempcopy:
            copy = SpooledTemporaryFile()  # boto3 now closes the file.
            copy.write(filelike.read())
            copy.seek(0)

            filelike = copy

        ExtraArgs = {}

        if self.acl:
            ExtraArgs['ACL'] = self.acl

        new_content_type = self.content_type
        existing_content_type = (self.exists() and self.mimetype()) or None
        if new_content_type or existing_content_type:
            ExtraArgs['ContentType'] = new_content_type or existing_content_type

        if self.exists() and self.content_encoding() == "gzip":
            self.apply_func_filelike(filelike, fn=gzip.compress)
            ExtraArgs['ContentEncoding'] = self.content_encoding(reload=False)

        self._key.upload_fileobj(filelike, ExtraArgs=ExtraArgs)

        return self.url()

    def retrieve_filelike(self, filelike):
        if filelike.closed:
            raise Exception("File provided was already closed.")

        self._key.download_fileobj(filelike)

        # when ContentEncoding is set, 'download_fileobj' seems to read the filelike
        # object, so that's why the next line is needed, there's an open issue on moto for that
        # ref: https://github.com/spulec/moto/issues/2926
        filelike.seek(0)

        if self.content_encoding() == "gzip":
            self.apply_func_filelike(filelike, fn=gzip.decompress)

        return

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

    def filesize(self, reload=True):
        if reload:
            self._key.reload()

        return self._key.content_length

    def exists(self):
        matches = list(self.bucket._bucket.objects.filter(Prefix=self.key))
        return len(matches) > 0 and matches[0].key == self.key

    def metadata(self, reload=True):
        if reload:
            self._key.reload()

        return self._key.metadata

    def mimetype(self, reload=True):
        if reload:
            self._key.reload()

        return self._key.content_type

    def set_mimetype(self, mimetype):
        if not self.acl:
            raise Exception(
                "S3Cubby's acl must be set or it will be removed by set_mimetype()!"
            )

        args = dict(
            CopySource={"Bucket": self.bucket.name, "Key": self.key},
            MetadataDirective="REPLACE",
            ACL=self.acl,
            ContentType=mimetype,
        )

        if self.content_encoding():
            args["ContentEncoding"] = self.content_encoding(reload=False)

        self._key.copy_from(**args)

        return self.mimetype()

    def content_encoding(self, reload=True):
        if reload:
            self._key.reload()

        return self._key.content_encoding

    def set_content_encoding(self, content_encoding):
        if not self.acl:
            raise Exception(
                "S3Cubby's acl must be set or it will be removed by set_content_encoding()!"
            )

        args = dict(
            CopySource={"Bucket": self.bucket.name, "Key": self.key},
            MetadataDirective="REPLACE",
            ACL=self.acl,
            ContentEncoding=content_encoding,
        )

        if self.mimetype():
            args["ContentType"] = self.mimetype(reload=False)

        self._key.copy_from(**args)
        return self.content_encoding()

    def set_metadata(self, metadata: dict = {}):
        self._key.copy_from(CopySource={'Bucket': self.bucket.name, 'Key': self.key},
                            MetadataDirective="REPLACE",
                            Metadata=metadata)
        self._key.reload()
        return metadata

    def __eq__(self, other):
        if not isinstance(other, S3Cubby):
            return False
        
        return self.bucket == other.bucket and self.key == other.key

    def copy_to_native_cubby(self, cubby=None):
        cubby.bucket.copy_key(cubby.key, self.key, src_bucket_name=self.bucket.name)


S3Service.__bucket_class__ = S3Bucket
