import re

from flask import current_app

from .service import Service, Bucket

from .file import FileService
from .s3 import S3Service


STORAGE_BUCKET_REGEX = \
    re.compile(r"(?P<service>(s3|file)):\/\/(?P<location>[^\/]+)\/(?P<bucket>[^\/]+)")
STORAGE_STRING_REGEX = \
    re.compile(r"{}\/(?P<key>.+)".format(STORAGE_BUCKET_REGEX.pattern))


class FlaskWarehouse:
    """
    Clean abstraction over several file storage backends (S3, Alicloud, local).
    """

    def __init__(self, app=None):
        self.services = {
            's3': S3Service,
            'file': FileService,
        }

        self.service: Service = None
        self.default_bucket: Bucket = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        app.config.setdefault('STORAGE_DEFAULT_SERVICE', 's3')
        app.config.setdefault('STORAGE_DEFAULT_LOCATION', 'us-west-1')

        default_service_key = self.app.config['STORAGE_DEFAULT_SERVICE']

        default_location = self.app.config['STORAGE_DEFAULT_LOCATION']

        self.service = self._create_service(service=default_service_key, location=default_location, app=app)
        self.default_bucket = app.config.get('STORAGE_DEFAULT_BUCKET')

    def bucket(self, name=None):
        if self.app is None:
            raise RuntimeError("Storage.init_app() was not called!")

        if self.default_bucket is None and name is None:
            raise Exception("'STORAGE_DEFAULT_BUCKET' is not set!")

        return self.service.bucket(name or self.default_bucket)

    def _create_service(self, service=None, location=None, app=None):
        try:
            service_constructor = self.services[service]
        except KeyError:
            raise Exception("No StorageService was registered named '{}'".format(service))

        return service_constructor(app or current_app, default_location=location)

    def _create_bucket_or_cubby(self, service=None, location=None, bucket=None, key=None, app=None):
        service = self._create_service(service=service, location=location)
        bucket = service.bucket(bucket)

        if key is None:
            return bucket

        return bucket.cubby(key)

    def __call__(self, bucket_or_key_str):
        match = (STORAGE_STRING_REGEX.match(bucket_or_key_str)
                 or STORAGE_BUCKET_REGEX.match(bucket_or_key_str))

        if match:
            return self._create_bucket_or_cubby(**match.groupdict())

        raise Exception("Could not parse '{}' as a Bucket or Cubby str".format(bucket_or_key_str))

    def __repr__(self):
        return "<Storage service={} default_bucket={}>".format(self.service, self.default_bucket)

    def __str__(self):
        return repr(self)


__all__ = ["FlaskWarehouse"]
