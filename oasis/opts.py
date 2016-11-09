# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools

import oasis.api.app
import oasis.common.clients
import oasis.common.exception
import oasis.common.service
import oasis.conductor.config
import oasis.conductor.handlers.nodepool_conductor
import oasis.conductor.template_definition
import oasis.db


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(oasis.common.paths.PATH_OPTS,
                         oasis.common.utils.UTILS_OPTS,
                         oasis.common.rpc_service.periodic_opts,
                         oasis.common.service.service_opts,
                         )),
        ('api', oasis.api.app.API_SERVICE_OPTS),
        ('conductor', oasis.conductor.config.SERVICE_OPTS),
        ('database', oasis.db.sql_opts),
        ('trust', oasis.common.keystone.trust_opts),
        ('heat_client', oasis.common.clients.heat_client_opts),
        ('glance_client', oasis.common.clients.glance_client_opts),
        ('cinder_client', oasis.common.clients.cinder_client_opts),
        ('nova_client', oasis.common.clients.nova_client_opts),
        ('neutron_client', oasis.common.clients.neutron_client_opts),
    ]
