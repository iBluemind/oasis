#!/usr/bin/env python

from setuptools import setup
from setuptools.command.sdist import sdist as _sdist
import re
import sys
import time
import codecs
import subprocess
if sys.version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

with open("oasis/version.py", "rt") as vfile:
    version_text = vfile.read()
vmatch = re.search(r'version ?= ?"(.+)"$', version_text)
version = vmatch.groups()[0]

release = '0'

# Get the long description from the relevant file
try:
    f = codecs.open('README.rst', encoding='utf-8')
    long_description = f.read()
    f.close()
except:
    long_description = ''

setup(
    name="oasis",
    version=version,
    description="Function as a Service for OpenStack.",
    long_description=long_description,
    author="Samgoon",
    url="https://github.com/samgoon/oasis",
    license='Apache License, Version 2.0',
    keywords="serverless faas openstack",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'oasis-api = oasis.cmd.api:main',
            'oasis-db-manage = oasis.cmd.db_manage:main',
            'oasis-conductor = oasis.cmd.conductor:main',
            'oasis-template-manage = oasis.cmd.template_manage:main',
        ],
        'oslo.config.opts': [
            'oasis = oasis.opts:list_opts'
        ],
        'oslo.config.opts.defaults': [
            'oasis = oasis.common.config:set_cors_middleware_defaults'
        ],
        'oasis.database.migration_backend': [
            'sqlalchemy = oasis.db.sqlalchemy.migration'
        ]
    },
    packages=[
        "oasis"
    ]
)