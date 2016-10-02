# Copyright 2014 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from heatclient.common import template_utils
from heatclient import exc
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import loopingcall
import six

from oasis.common import clients
from oasis.common import exception
from oasis.common import short_id
from oasis.common import utils
# from oasis.conductor.handlers.common import cert_manager
# from oasis.conductor import scale_manager
# from oasis.conductor.template_definition import TemplateDefinition as TDef
# from oasis.conductor import utils as conductor_utils
from oasis.i18n import _
from oasis.i18n import _LE
from oasis.i18n import _LI
from oasis import objects
from oasis.objects.fields import FunctionStatus as function_status
from oasis.agent import api as agent_rpc
from oasis.common import context


oasis_heat_opts = [
    cfg.IntOpt('max_attempts',
               default=2000,
               help=('Number of attempts to query the Heat stack for '
                     'finding out the status of the created stack and '
                     'getting template outputs.  This value is ignored '
                     'during function creation if timeout is set as the poll '
                     'will continue until function creation either ends '
                     'or times out.')),
    cfg.IntOpt('wait_interval',
               default=1,
               help=('Sleep time interval between two attempts of querying '
                     'the Heat stack.  This interval is in seconds.')),
    cfg.IntOpt('function_create_timeout',
               help=('The length of time to let function creation continue.  This '
                     'interval is in minutes.  The default is no timeout.'))
]

CONF = cfg.CONF
CONF.register_opts(oasis_heat_opts, group='oasis_heat')
# CONF.import_opt('trustee_domain_id', 'oasis.common.keystone',
#                 group='trust')

LOG = logging.getLogger(__name__)

# TODO real data
headers = {}
user_name = headers.get('X-User-Name')
user_id = headers.get('X-User-Id')
project = headers.get('X-Project-Name')
project_id = headers.get('X-Project-Id')
domain_id = headers.get('X-User-Domain-Id')
domain_name = headers.get('X-User-Domain-Name')
auth_token = headers.get('X-Auth-Token')
roles = headers.get('X-Roles', '').split(',')
auth_token_info = None

auth_url = None

# auth_url = CONF.keystone_authtoken.auth_uri

agent_context = context.make_context(
    auth_token=auth_token,
    auth_url=auth_url,
    auth_token_info=auth_token_info,
    user_name=user_name,
    user_id=user_id,
    project_name=project,
    project_id=project_id,
    domain_id=domain_id,
    domain_name=domain_name,
    roles=roles)


class Handler(object):

    def __init__(self):
        super(Handler, self).__init__()

    # Function Operations

    def nodepool_create(self, context, nodepool):
        LOG.debug('nodepool_create')


        # logic...

        api = agent_rpc.AgentAPI(context=agent_context)
        api.nodepool_create('nodepool')

        # self._poll_and_check(osc, function)

        return nodepool

    def nodepool_update(self, context, nodepool):
        LOG.debug('nodepool_update')

        # logic...

        api = agent_rpc.AgentAPI(context=agent_context)
        api.nodepool_update('nodepool')
        # self._poll_and_check(osc, function)

        return nodepool


    def nodepool_delete(self, context, nodepool):
        LOG.debug('nodepool_delete')

        # logic...

        api = agent_rpc.AgentAPI(context=agent_context)
        api.nodepool_delete('nodepool')

        # self._poll_and_check(osc, function)

        return None

