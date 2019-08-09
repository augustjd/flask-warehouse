#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
        assert cubby.delete()


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