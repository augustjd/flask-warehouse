import re

from flask import current_app

from .backends import Service, FileService, S3Service


# A regex for bucket strings like s3://us-west-1/bucket
WAREHOUSE_BUCKET_REGEX = \
    re.compile(r"(?P<service>(s3|file)):\/\/(?P<location>[^\/]+)?\/(?P<bucket>[^\/]+)")


# A regex for cubby strings like s3://us-west-1/bucket/key
WAREHOUSE_CUBBY_REGEX = \
    re.compile(r"{}\/(?P<key>.+)".format(WAREHOUSE_BUCKET_REGEX.pattern))


class Warehouse(Service):
    """
    Clean abstraction over several file storage backends (S3, Alicloud, local).
    """

    def __init__(self, app=None):
        self.services = {
            's3': S3Service,
            'file': FileService,
        }

        self.service: Service = None
        self.default_bucket = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        app.config.setdefault('WAREHOUSE_DEFAULT_SERVICE', 'file')

        default_service_key = app.config['WAREHOUSE_DEFAULT_SERVICE']

        self.default_location = app.config.get('WAREHOUSE_DEFAULT_LOCATION')
        self.default_bucket = app.config.get('WAREHOUSE_DEFAULT_BUCKET')

        self.service = self._create_service(service=default_service_key,
                                            location=self.default_location,
                                            app=app)

    def bucket(self, name=None, location=None):
        if self.app is None:
            raise RuntimeError("Storage.init_app() was not called!")

        if self.default_bucket is None and name is None:
            raise Exception("'WAREHOUSE_DEFAULT_BUCKET' is not set!")

        return self.service.bucket(name or self.default_bucket, location or self.default_location)

    def _create_service(self, service=None, location=None, app=None):
        try:
            service_constructor = self.services[service]
        except KeyError:
            raise Exception("No StorageService was registered named '{}'".format(service))

        return service_constructor(app or current_app, default_location=location or self.default_location)

    def _create_bucket_or_cubby(self, service=None, location=None, bucket=None, key=None, app=None):
        service = self._create_service(service=service, location=location)
        bucket = service.bucket(bucket)

        if key is None:
            return bucket

        return bucket.cubby(key)

    def __call__(self, bucket_or_key_str):
        match = (WAREHOUSE_CUBBY_REGEX.match(bucket_or_key_str)
                 or WAREHOUSE_BUCKET_REGEX.match(bucket_or_key_str))

        if match:
            return self._create_bucket_or_cubby(**match.groupdict())

        raise Exception("Could not parse '{}' as a Bucket or Cubby str".format(bucket_or_key_str))

    def __repr__(self):
        return "<Warehouse service={} default_bucket={}>".format(self.service, self.default_bucket)

    def __str__(self):
        return repr(self)


__all__ = ["Warehouse"]
