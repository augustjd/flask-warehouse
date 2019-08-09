import os
import shutil

from flask import Flask, url_for

from .service import Bucket, Cubby, Service


class FileService(Service):
    requires_location = False

    def __init__(self, app: Flask, default_location=None):
        super().__init__('file', default_location=default_location)

        self.root = app.static_folder

        self.abspath = os.path.abspath(self.root)

        if not os.path.isdir(self.abspath):
            os.makedirs(self.abspath)


class FolderBucket(Bucket):
    def __init__(self, service: FileService, name: str, location: str):
        super().__init__(service, name, location)

        self.abspath = os.path.abspath(os.path.join(service.root, name))

        if not os.path.isdir(self.abspath):
            os.makedirs(self.abspath)

    def cubby(self, name, content_type=None, acl='public-read'):
        return FileCubby(self, name, content_type=content_type, acl=acl)

    def delete(self):
        shutil.rmtree(self.abspath)

    def list(self, prefix=None, max_keys=None, **kwargs):
        return [FileCubby(self, key) for key in os.listdir(self.abspath)]


class FileCubby(Cubby):
    def __init__(self, bucket: FolderBucket, name: str, content_type=None, acl='public-read'):
        super().__init__(bucket, name)

        if not os.path.isdir(self.dirpath()):
            os.makedirs(self.dirpath())

        self.content_type = content_type
        self.acl = acl

    def dirpath(self):
        return os.path.dirname(self.filepath())

    def filepath(self):
        return os.path.join(self.bucket.abspath, self.key)

    def keypath(self):
        return os.path.join(self.bucket.name, self.key)

    def url(self, duration=Cubby.DefaultUrlExpiration):
        return url_for('static', filename=self.keypath(), _external=True)

    def store_filelike(self, filelike):
        shutil.copyfileobj(filelike, open(self.filepath(), 'wb'))

    def retrieve_filelike(self, filelike):
        shutil.copyfileobj(open(self.filepath(), 'rb'), filelike)

    def delete(self):
        if self.exists():
            os.remove(self.filepath())

        return not self.exists()

    def filesize(self):
        return os.path.getsize(self.filepath())

    def service_id(self):
        return "file"

    def exists(self):
        return os.path.isfile(self.filepath())

    def copy_to_native_cubby(self, cubby=None):
        shutil.copy(self.filepath(), cubby.filepath())


FileService.__bucket_class__ = FolderBucket
