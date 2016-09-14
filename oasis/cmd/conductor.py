# Copyright 2014 - Rackspace Hosting
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Starter script for the Magnum conductor service."""

import os
import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
from oslo_service import service

from oasis.common import rpc_service
from oasis.common import service as oasis_service
from oasis.common import short_id
from oasis.i18n import _LE
from oasis.i18n import _LI
from oasis import version

LOG = logging.getLogger(__name__)


def main():
    oasis_service.prepare_service(sys.argv)

    gmr.TextGuruMeditation.setup_autorun(version)

    LOG.info(_LI('Starting server in PID %s'), os.getpid())
    LOG.debug("Configuration:")
    cfg.CONF.log_opt_values(LOG, logging.DEBUG)

    cfg.CONF.import_opt('topic', 'oasis.conductor.config', group='conductor')

    conductor_id = short_id.generate_id()
    endpoints = [

    ]

    server = rpc_service.Service.create(cfg.CONF.conductor.topic,
                                        conductor_id, endpoints,
                                        binary='oasis-conductor')
    launcher = service.launch(cfg.CONF, server)
    launcher.wait()
