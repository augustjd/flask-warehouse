#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Flask>=1.0',
]

test_requirements = [
    'Flask>=1.0',
]

setup(
    name='flask_warehouse',
    version='0.1.2',
    description="A clean abstraction over cloud file storage platforms like S3, Alicloud, or Heroku.",
    long_description=readme + '\n\n' + history,
    author="Joshua Augustin",
    author_email='augustinspring@gmail.com',
    url='https://github.com/augustjd/flask-warehouse',
    packages=[
        'flask_warehouse',
        'flask_warehouse.backends',
    ],
    package_dir={'flask_warehouse':
                 'flask_warehouse'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='flask_warehouse',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
