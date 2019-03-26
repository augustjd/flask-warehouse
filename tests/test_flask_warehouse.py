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

from flask_warehouse import FlaskWarehouse


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


def test_default_service_is_file(app):
    """Sample pytest test function with the pytest fixture as an argument.
    """
    warehouse = FlaskWarehouse(app)

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
