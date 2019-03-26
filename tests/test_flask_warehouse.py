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


def test_import():
    """Sample pytest test function with the pytest fixture as an argument.
    """
    warehouse = FlaskWarehouse()
