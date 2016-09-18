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
from oasis.conductor.handlers.common import cert_manager
from oasis.conductor import scale_manager
from oasis.conductor.template_definition import TemplateDefinition as TDef
from oasis.conductor import utils as conductor_utils
from oasis.i18n import _
from oasis.i18n import _LE
from oasis.i18n import _LI
from oasis import objects
from oasis.objects.fields import BayStatus as function_status


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
CONF.import_opt('trustee_domain_id', 'oasis.common.keystone',
                group='trust')

LOG = logging.getLogger(__name__)


def _extract_template_definition(context, function, scale_manager=None):
    functionmodel = conductor_utils.retrieve_functionmodel(context, function)
    cluster_distro = functionmodel.cluster_distro
    cluster_coe = functionmodel.coe
    cluster_server_type = functionmodel.server_type
    definition = TDef.get_template_definition(cluster_server_type,
                                              cluster_distro,
                                              cluster_coe)
    return definition.extract_definition(context, functionmodel, function,
                                         scale_manager=scale_manager)


def _create_stack(context, osc, function, function_create_timeout):
    template_path, heat_params = _extract_template_definition(context, function)

    tpl_files, template = template_utils.get_template_contents(template_path)
    # Make sure no duplicate stack name
    stack_name = '%s-%s' % (function.name, short_id.generate_id())
    if function_create_timeout:
        heat_timeout = function_create_timeout
    elif function_create_timeout == 0:
        heat_timeout = None
    else:
        # no function_create_timeout value was passed in to the request
        # so falling back on configuration file value
        heat_timeout = cfg.CONF.function_heat.function_create_timeout
    fields = {
        'stack_name': stack_name,
        'parameters': heat_params,
        'template': template,
        'files': tpl_files,
        'timeout_mins': heat_timeout
    }
    created_stack = osc.heat().stacks.create(**fields)

    return created_stack


def _update_stack(context, osc, function, scale_manager=None):
    template_path, heat_params = _extract_template_definition(
        context, function, scale_manager=scale_manager)

    tpl_files, template = template_utils.get_template_contents(template_path)
    fields = {
        'parameters': heat_params,
        'template': template,
        'files': tpl_files
    }

    return osc.heat().stacks.update(function.stack_id, **fields)


class Handler(object):

    def __init__(self):
        super(Handler, self).__init__()

    @staticmethod
    def _create_trustee_and_trust(osc, function):
        password = utils.generate_password(length=18)
        trustee = osc.keystone().create_trustee(
            function.uuid,
            password,
            CONF.trust.trustee_domain_id)
        function.trustee_username = trustee.name
        function.trustee_user_id = trustee.id
        function.trustee_password = password
        trust = osc.keystone().create_trust(trustee.id)
        function.trust_id = trust.id

    # Function Operations

    def function_create(self, context, function, function_create_timeout):
        LOG.debug('function_heat function_create')

        osc = clients.OpenStackClients(context)

        function.uuid = uuid.uuid4()
        self._create_trustee_and_trust(osc, function)
        try:
            # Generate certificate and set the cert reference to function
            # cert_manager.generate_certificates_to_function(function)
            created_stack = _create_stack(context, osc, function,
                                          function_create_timeout)
        except exc.HTTPBadRequest as e:
            cert_manager.delete_certificates_from_function(function)
            raise exception.InvalidParameterValue(message=six.text_type(e))
        except Exception:
            raise

        function.stack_id = created_stack['stack']['id']
        function.status = function_status.CREATE_IN_PROGRESS
        function.create()

        self._poll_and_check(osc, function)

        return function

    def function_update(self, context, function):
        LOG.debug('function_heat function_update')

        osc = clients.OpenStackClients(context)
        stack = osc.heat().stacks.get(function.stack_id)
        allow_update_status = (
            function_status.CREATE_COMPLETE,
            function_status.UPDATE_COMPLETE,
            function_status.RESUME_COMPLETE,
            function_status.RESTORE_COMPLETE,
            function_status.ROLLBACK_COMPLETE,
            function_status.SNAPSHOT_COMPLETE,
            function_status.CHECK_COMPLETE,
            function_status.ADOPT_COMPLETE
        )
        if stack.stack_status not in allow_update_status:
            operation = _('Updating a function when stack status is '
                          '"%s"') % stack.stack_status
            raise exception.NotSupported(operation=operation)

        delta = function.obj_what_changed()
        if not delta:
            return function

        manager = scale_manager.ScaleManager(context, osc, function)

        _update_stack(context, osc, function, manager)
        self._poll_and_check(osc, function)

        return function

    @staticmethod
    def _delete_trustee_and_trust(osc, function):
        osc.keystone().delete_trust(function.trust_id)
        osc.keystone().delete_trustee(function.trustee_user_id)

    def function_delete(self, context, uuid):
        LOG.debug('function_heat function_delete')
        osc = clients.OpenStackClients(context)
        function = objects.Bay.get_by_uuid(context, uuid)

        self._delete_trustee_and_trust(osc, function)

        stack_id = function.stack_id
        # NOTE(sdake): This will execute a stack_delete operation.  This will
        # Ignore HTTPNotFound exceptions (stack wasn't present).  In the case
        # that Heat couldn't find the stack representing the function, likely a user
        # has deleted the stack outside the context of Magnum.  Therefore the
        # contents of the function are forever lost.
        #
        # If the exception is unhandled, the original exception will be raised.
        try:
            osc.heat().stacks.delete(stack_id)
        except exc.HTTPNotFound:
            LOG.info(_LI('The stack %s was not be found during function'
                         ' deletion.'), stack_id)
            try:
                cert_manager.delete_certificates_from_function(function)
                function.destroy()
            except exception.BayNotFound:
                LOG.info(_LI('The function %s has been deleted by others.'), uuid)
            return None
        except Exception:
            raise

        self._poll_and_check(osc, function)

        return None

    def _poll_and_check(self, osc, function):
        poller = HeatPoller(osc, function)
        lc = loopingcall.FixedIntervalLoopingCall(f=poller.poll_and_check)
        lc.start(cfg.CONF.function_heat.wait_interval, True)


class HeatPoller(object):

    def __init__(self, openstack_client, function):
        self.openstack_client = openstack_client
        self.context = self.openstack_client.context
        self.function = function
        self.attempts = 0
        self.functionmodel = conductor_utils.retrieve_functionmodel(self.context, function)
        self.template_def = TDef.get_template_definition(
            self.functionmodel.server_type,
            self.functionmodel.cluster_distro, self.functionmodel.coe
        )

    def poll_and_check(self):
        # TODO(yuanying): temporary implementation to update api_address,
        # node_addresses and function status
        stack = self.openstack_client.heat().stacks.get(self.function.stack_id)
        self.attempts += 1
        # poll_and_check is detached and polling long time to check status,
        # so another user/client can call delete function/stack.
        if stack.stack_status == function_status.DELETE_COMPLETE:
            self._delete_complete()
            raise loopingcall.LoopingCallDone()

        if stack.stack_status in (function_status.CREATE_COMPLETE,
                                  function_status.UPDATE_COMPLETE):
            self._sync_function_and_template_status(stack)
            raise loopingcall.LoopingCallDone()
        elif stack.stack_status != self.function.status:
            self._sync_function_status(stack)

        if stack.stack_status in (function_status.CREATE_FAILED,
                                  function_status.DELETE_FAILED,
                                  function_status.UPDATE_FAILED):
            self._sync_function_and_template_status(stack)
            self._function_failed(stack)
            raise loopingcall.LoopingCallDone()
        # only check max attempts when the stack is being created when
        # the timeout hasn't been set. If the timeout has been set then
        # the loop will end when the stack completes or the timeout occurs
        if stack.stack_status == function_status.CREATE_IN_PROGRESS:
            if (stack.timeout_mins is None and
               self.attempts > cfg.CONF.function_heat.max_attempts):
                LOG.error(_LE('Bay check exit after %(attempts)s attempts,'
                              'stack_id: %(id)s, stack_status: %(status)s') %
                          {'attempts': cfg.CONF.function_heat.max_attempts,
                           'id': self.function.stack_id,
                           'status': stack.stack_status})
                raise loopingcall.LoopingCallDone()
        else:
            if self.attempts > cfg.CONF.function_heat.max_attempts:
                LOG.error(_LE('Bay check exit after %(attempts)s attempts,'
                              'stack_id: %(id)s, stack_status: %(status)s') %
                          {'attempts': cfg.CONF.function_heat.max_attempts,
                           'id': self.function.stack_id,
                           'status': stack.stack_status})
                raise loopingcall.LoopingCallDone()

    def _delete_complete(self):
        LOG.info(_LI('Bay has been deleted, stack_id: %s')
                 % self.function.stack_id)
        try:
            cert_manager.delete_certificates_from_function(self.function)
            self.function.destroy()
        except exception.BayNotFound:
            LOG.info(_LI('The function %s has been deleted by others.')
                     % self.function.uuid)

    def _sync_function_status(self, stack):
        self.function.status = stack.stack_status
        self.function.status_reason = stack.stack_status_reason
        stack_nc_param = self.template_def.get_heat_param(
            function_attr='node_count')
        self.function.node_count = stack.parameters[stack_nc_param]
        self.function.save()

    def _sync_function_and_template_status(self, stack):
        self.template_def.update_outputs(stack, self.functionmodel, self.function)
        self._sync_function_status(stack)

    def _function_failed(self, stack):
        LOG.error(_LE('Bay error, stack status: %(function_status)s, '
                      'stack_id: %(stack_id)s, '
                      'reason: %(reason)s') %
                  {'function_status': stack.stack_status,
                   'stack_id': self.function.stack_id,
                   'reason': self.function.status_reason})
