#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
from flask import Flask

"""
test_flask_warehouse
----------------------------------

Tests for `flask_warehouse` module.
"""

import pytest

from contextlib import contextmanager
from click.testing import CliRunner

from flask_warehouse import Warehouse

from moto import mock_s3


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


@pytest.fixture
def s3_app():
    app = Flask(__name__)

    app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'
    app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'

    return app


def test_default_service_is_file(app):
    """Sample pytest test function with the pytest fixture as an argument.
    """
    warehouse = Warehouse(app)

    assert warehouse.service is not None
    assert warehouse.service.id == 'file'

    with app.app_context():
        cubby = warehouse('file:///something/beautiful')
        assert cubby.delete()
        assert not cubby.exists()
        cubby.store(bytes=b'12345')
        assert cubby.exists()
        assert cubby.retrieve() == b'12345'
        assert cubby.delete()


def test_default_service_is_file(app):
    """Sample pytest test function with the pytest fixture as an argument.
    """
    warehouse = Warehouse(app)

    assert warehouse.service is not None
    assert warehouse.service.id == 'file'

    with app.app_context():
        cubby = warehouse('file:///something/beautiful')
        assert cubby.delete()
        assert not cubby.exists()
        cubby.store(bytes=b'12345')
        assert cubby.exists()
        assert cubby.retrieve() == b'12345'
        assert cubby.delete()


@mock_s3
def test_s3_service(app):
    """Sample pytest test function with the pytest fixture as an argument.
    """
    app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'
    app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'

    warehouse = Warehouse(app)

    assert warehouse.service is not None
    assert warehouse.service.id == 's3'

    with app.app_context():
        cubby = warehouse('s3:///something/beautiful')
        assert cubby.delete()
        assert not cubby.exists()
        cubby.store(bytes=b'12345')
        assert cubby.exists()
        assert cubby.retrieve() == b'12345'
        assert cubby.filesize() == 5
        assert cubby.mimetype() == None
        cubby.set_mimetype("application/octet-stream")
        assert cubby.mimetype() == 'application/octet-stream'

        assert cubby.metadata() == {}
        metadata = {"tag": "value"}
        assert cubby.set_metadata(metadata)
        assert cubby.metadata() == metadata

        assert cubby.content_encoding() is None
        cubby.set_content_encoding("gzip")
        assert cubby.content_encoding() == 'gzip'

        assert cubby.delete()

@mock_s3
def test_s3_service_gzipped_content(app):
    """Tests gzip support for cubby
    """
    app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'
    app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'

    warehouse = Warehouse(app)

    assert warehouse.service is not None
    assert warehouse.service.id == 's3'

    with app.app_context():
        cubby = warehouse('s3:///something/beautiful')
        cubby.store(bytes=b'12345')
        assert cubby.exists()

        # set up attributes for the cubby
        cubby.set_mimetype("application/octet-stream")
        cubby.set_content_encoding("gzip")

        # confirm all attributes are set
        assert cubby.mimetype() == "application/octet-stream"
        assert cubby.content_encoding() == 'gzip'

        ## Assert gzipped content can be read and written correctly
        cubby.store(bytes=b'12345')

        # assert gzipped content was written
        expected_content = gzip.compress(b'12345')
        actual_content = cubby._key.get()['Body'].read()
        # convert byte arrays to lists for comparison
        assert list(expected_content) == list(actual_content)

        # assert no attributes were changed
        assert cubby.mimetype() == 'application/octet-stream'
        assert cubby.content_encoding() == 'gzip'

        # assert can read data correctly
        assert cubby.retrieve() == b'12345'


@mock_s3
def test_s3_service_readme(app):
    """Runs the example from the README."""
    import os

    from flask import Flask
    from flask_warehouse import Warehouse
    
    # 1. Configuring Warehouse
    app = Flask(__name__)
    app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'          # or 'file' for filesystem
    app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'  # required for 's3'
    app.config['WAREHOUSE_DEFAULT_BUCKET'] = None

    app.config['AWS_ACCESS_KEY_ID'] = '...'  # required for 's3'
    app.config['AWS_SECRET_ACCESS_KEY'] = '...'  # required for 's3'
    
    warehouse = Warehouse(app)
    
    # Object-oriented approach:
    bucket = warehouse.bucket('mybucket')
    oo_cubby = bucket.cubby('keys')

    # Or compact approach:
    compact_cubby = warehouse('s3:///mybucket/keys')

    assert oo_cubby == compact_cubby

    cubby = oo_cubby
    
    # 2. Writing to/from bytes
    contents = b'12345'
    cubby.store(bytes=contents)
    
    assert cubby.filesize() == 5
    
    cubby_contents = cubby.retrieve()
    assert cubby_contents == contents

    # 3. Writing to/from files
    filepath = "local.txt"
    with open(filepath, 'wb') as f:
        f.write(b"Here are the contents of a file.")

    cubby.store(filepath=filepath)
    assert os.path.getsize(filepath) == cubby.filesize()

    assert cubby.retrieve() == open(filepath, 'rb').read()


@mock_s3
def test_copy_move(app):
    """Runs the example from the README."""
    app.config['WAREHOUSE_DEFAULT_SERVICE'] = 's3'
    app.config['WAREHOUSE_DEFAULT_LOCATION'] = 'us-west-1'

    warehouse = Warehouse(app)
    
    # Object-oriented approach:
    source_bucket = warehouse.bucket('source')
    destination_bucket = warehouse.bucket('destination')

    example_source = source_bucket.cubby('example')
    contents = b"Hello, world!"
    example_source.store(bytes=contents)

    example_source.copy_to(key="another")
    another_source = source_bucket.cubby("another")

    assert example_source.retrieve() == another_source.retrieve()

    example_destination = destination_bucket.cubby("destination")

    example_source.copy_to(cubby=example_destination)

    assert example_source.retrieve() == example_destination.retrieve()

    example_source.move_to(cubby=example_destination)
    assert example_destination.retrieve()  == contents
    assert not example_source.exists()


@mock_s3
def test_change_acl(s3_app):
    """Runs the example from the README."""
    warehouse = Warehouse(s3_app)

    source_bucket = warehouse.bucket('source')

    contents = b"Hello, world!"
    example_source = source_bucket.cubby('example', acl='public-read').store(bytes=contents)
    assert example_source.mimetype() is None

    example_source._key.Acl().load()
    grants = example_source._key.Acl().grants  # grants should be the same before/after

    example_source.set_mimetype("application/json")

    example_source._key.Acl().load()
    assert example_source._key.Acl().grants == grants  # grants should be the same before/after