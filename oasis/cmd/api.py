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

"""Starter script for the Oasis API service."""

import os
import sys
from wsgiref import simple_server

from oslo_config import cfg
from oslo_log import log as logging

from oasis.api import app as api_app
from oasis.common import service
from oasis.i18n import _LI
from oasis import version


LOG = logging.getLogger(__name__)


def main():
    service.prepare_service(sys.argv)
    app = api_app.load_app()

    # Create the WSGI server and start it
    host, port = cfg.CONF.api.host, cfg.CONF.api.port
    srv = simple_server.make_server(host, port, app)

    LOG.info(_LI('Starting server in PID %s'), os.getpid())
    LOG.debug("Configuration:")
    cfg.CONF.log_opt_values(LOG, logging.DEBUG)

    LOG.info(_LI('serving on http://%(host)s:%(port)s'),
             dict(host=host, port=port))

    srv.serve_forever()
