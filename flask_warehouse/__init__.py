# -*- coding: utf-8 -*-

"""
    flaskext.flask-warehouse
    ---------------

    A clean abstraction over cloud file storage platforms like S3, Alicloud, or
    Heroku.

    :copyright: (c) by Joshua Augustin.
    :license: MIT license , see LICENSE for more details.
"""


__author__ = """Joshua Augustin"""
__email__ = 'augustinspring@gmail.com'
__version__ = '0.1.1'


from .flask_warehouse import Warehouse
assert(Warehouse)
