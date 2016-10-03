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
from oasis.i18n import _
from oasis.i18n import _LE
from oasis.i18n import _LI
from oasis import objects
from oasis.objects.fields import NodePoolStatus as nodepool_status
from oasis.conductor.template_definition import TemplateDefinition as TDef


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


def _extract_template_definition(context, nodepool):
    definition = TDef.get_template_definition()
    return definition.extract_definition(context, nodepool)


def _create_stack(context, osc, nodepool, nodepool_create_timeout):
    template_path, heat_params = _extract_template_definition(context, nodepool)

    tpl_files, template = template_utils.get_template_contents(template_path)
    # Make sure no duplicate stack name
    stack_name = '%s-%s' % (nodepool.name, short_id.generate_id())
    if nodepool_create_timeout:
        heat_timeout = nodepool_create_timeout
    elif nodepool_create_timeout == 0:
        heat_timeout = None
    else:
        # no bay_create_timeout value was passed in to the request
        # so falling back on configuration file value
        heat_timeout = cfg.CONF.nodepool_heat.nodepool_create_timeout
    fields = {
        'stack_name': stack_name,
        'parameters': heat_params,
        'template': template,
        'files': tpl_files,
        'timeout_mins': heat_timeout
    }
    created_stack = osc.heat().stacks.create(**fields)

    return created_stack


def _update_stack(context, osc, nodepool, scale_manager=None):
    template_path, heat_params = _extract_template_definition(
        context, nodepool)

    tpl_files, template = template_utils.get_template_contents(template_path)
    fields = {
        'parameters': heat_params,
        'template': template,
        'files': tpl_files
    }

    return osc.heat().stacks.update(nodepool.stack_id, **fields)


class Handler(object):

    def __init__(self):
        super(Handler, self).__init__()

    @staticmethod
    def _create_trustee_and_trust(osc, nodepool):
        password = utils.generate_password(length=18)
        trustee = osc.keystone().create_trustee(
            nodepool.uuid,
            password,
            CONF.trust.trustee_domain_id)
        nodepool.trustee_username = trustee.name
        nodepool.trustee_user_id = trustee.id
        nodepool.trustee_password = password
        trust = osc.keystone().create_trust(trustee.id)
        nodepool.trust_id = trust.id

    @staticmethod
    def _delete_trustee_and_trust(osc, bay):
        osc.keystone().delete_trust(bay.trust_id)
        osc.keystone().delete_trustee(bay.trustee_user_id)

    # Function Operations
    def nodepool_create(self, context, nodepool, nodepool_create_timeout):
        LOG.debug('nodepool_create')
        osc = clients.OpenStackClients(context)

        nodepool.uuid = uuid.uuid4()
        self._create_trustee_and_trust(osc, nodepool)
        try:
            created_stack = _create_stack(context, osc, nodepool,
                                          nodepool_create_timeout)
        except Exception:
            raise

        nodepool.stack_id = created_stack['stack']['id']
        nodepool.status = nodepool_status.CREATE_IN_PROGRESS
        nodepool.create()

        self._poll_and_check(osc, nodepool)
        return nodepool

    def nodepool_update(self, context, nodepool):
        LOG.debug('nodepool_update')

        osc = clients.OpenStackClients(context)
        stack = osc.heat().stacks.get(nodepool.stack_id)
        allow_update_status = (
            nodepool_status.CREATE_COMPLETE,
            nodepool_status.UPDATE_COMPLETE,
            nodepool_status.RESUME_COMPLETE,
            nodepool_status.RESTORE_COMPLETE,
            nodepool_status.ROLLBACK_COMPLETE,
            nodepool_status.SNAPSHOT_COMPLETE,
            nodepool_status.CHECK_COMPLETE,
            nodepool_status.ADOPT_COMPLETE
        )
        if stack.stack_status not in allow_update_status:
            operation = _('Updating a bay when stack status is '
                          '"%s"') % stack.stack_status
            raise exception.NotSupported(operation=operation)

        delta = nodepool.obj_what_changed()
        if not delta:
            return nodepool

        manager = scale_manager.ScaleManager(context, osc, bay)

        _update_stack(context, osc, nodepool, manager)
        self._poll_and_check(osc, nodepool)

        return nodepool

    def nodepool_delete(self, context, uuid):
        LOG.debug('nodepool_delete')

        osc = clients.OpenStackClients(context)
        nodepool = objects.NodePool.get_by_uuid(context, uuid)

        self._delete_trustee_and_trust(osc, nodepool)

        stack_id = nodepool.stack_id
        # NOTE(sdake): This will execute a stack_delete operation.  This will
        # Ignore HTTPNotFound exceptions (stack wasn't present).  In the case
        # that Heat couldn't find the stack representing the bay, likely a user
        # has deleted the stack outside the context of Oasis.  Therefore the
        # contents of the bay are forever lost.
        #
        # If the exception is unhandled, the original exception will be raised.
        try:
            osc.heat().stacks.delete(stack_id)
        except exc.HTTPNotFound:
            LOG.info(_LI('The stack %s was not be found during bay'
                         ' deletion.'), stack_id)
            try:
                nodepool.destroy()
            except exception.NodePoolNotFound:
                LOG.info(_LI('The nodepool %s has been deleted by others.'), uuid)
            return None
        except Exception:
            raise

        self._poll_and_check(osc, nodepool)
        return None

    def _poll_and_check(self, osc, bay):
        poller = HeatPoller(osc, bay)
        lc = loopingcall.FixedIntervalLoopingCall(f=poller.poll_and_check)
        lc.start(cfg.CONF.bay_heat.wait_interval, True)


class HeatPoller(object):

    def __init__(self, openstack_client, nodepool):
        self.openstack_client = openstack_client
        self.context = self.openstack_client.context
        self.nodepool = nodepool
        self.attempts = 0
        self.template_def = TDef.get_template_definition()

    def poll_and_check(self):
        # TODO(yuanying): temporary implementation to update api_address,
        # node_addresses and bay status
        stack = self.openstack_client.heat().stacks.get(self.nodepool.stack_id)
        self.attempts += 1
        # poll_and_check is detached and polling long time to check status,
        # so another user/client can call delete bay/stack.
        if stack.stack_status == nodepool_status.DELETE_COMPLETE:
            self._delete_complete()
            raise loopingcall.LoopingCallDone()

        if stack.stack_status in (nodepool_status.CREATE_COMPLETE,
                                  nodepool_status.UPDATE_COMPLETE):
            # self._sync_bay_and_template_status(stack)
            raise loopingcall.LoopingCallDone()
        elif stack.stack_status != self.nodepool.status:
            self._sync_bay_status(stack)

        if stack.stack_status in (nodepool_status.CREATE_FAILED,
                                  nodepool_status.DELETE_FAILED,
                                  nodepool_status.UPDATE_FAILED):
            # self._sync_bay_and_template_status(stack)
            self._bay_failed(stack)
            raise loopingcall.LoopingCallDone()
        # only check max attempts when the stack is being created when
        # the timeout hasn't been set. If the timeout has been set then
        # the loop will end when the stack completes or the timeout occurs
        if stack.stack_status == nodepool_status.CREATE_IN_PROGRESS:
            if (stack.timeout_mins is None and
                        self.attempts > cfg.CONF.bay_heat.max_attempts):
                LOG.error(_LE('Bay check exit after %(attempts)s attempts,'
                              'stack_id: %(id)s, stack_status: %(status)s') %
                          {'attempts': cfg.CONF.bay_heat.max_attempts,
                           'id': self.nodepool.stack_id,
                           'status': stack.stack_status})
                raise loopingcall.LoopingCallDone()
        else:
            if self.attempts > cfg.CONF.bay_heat.max_attempts:
                LOG.error(_LE('Bay check exit after %(attempts)s attempts,'
                              'stack_id: %(id)s, stack_status: %(status)s') %
                          {'attempts': cfg.CONF.bay_heat.max_attempts,
                           'id': self.nodepool.stack_id,
                           'status': stack.stack_status})
                raise loopingcall.LoopingCallDone()

    def _delete_complete(self):
        LOG.info(_LI('Bay has been deleted, stack_id: %s')
                 % self.nodepool.stack_id)
        try:
            self.nodepool.destroy()
        except exception.NodePoolNotFound:
            LOG.info(_LI('The bay %s has been deleted by others.')
                     % self.nodepool.uuid)

    def _sync_bay_status(self, stack):
        self.nodepool.status = stack.stack_status
        self.nodepool.status_reason = stack.stack_status_reason
        stack_nc_param = self.template_def.get_heat_param(
            bay_attr='node_count')
        self.nodepool.node_count = stack.parameters[stack_nc_param]
        self.nodepool.save()

    def _sync_bay_and_template_status(self, stack):
        self.template_def.update_outputs(stack, self.nodepool)
        self._sync_bay_status(stack)

    def _bay_failed(self, stack):
        LOG.error(_LE('Bay error, stack status: %(bay_status)s, '
                      'stack_id: %(stack_id)s, '
                      'reason: %(reason)s') %
                  {'bay_status': stack.stack_status,
                   'stack_id': self.nodepool.stack_id,
                   'reason': self.nodepool.status_reason})

