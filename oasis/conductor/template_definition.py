# Copyright 2014 Rackspace Inc. All rights reserved.
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
import abc

from oslo_config import cfg
from oslo_log import log as logging
from pkg_resources import iter_entry_points
import requests
import six

from oasis.common import paths
from oasis.common import clients
from oasis.common import exception
from oasis.i18n import _
from oasis.i18n import _LW


LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('trustee_domain_id', 'oasis.common.keystone', group='trust')

template_def_opts = [
    cfg.StrOpt('nodepool_template_path',
           default=paths.basedir_def('templates/server-nodepool.yaml'),
           help=_('Location of template to build a Mesos cluster '
                  'on Ubuntu.')),
]

CONF.register_opts(template_def_opts)


class ParameterMapping(object):
    """A mapping associating heat param and bay/baymodel attr.

    A ParameterMapping is an association of a Heat parameter name with
    an attribute on a Bay, Baymodel, or both.

    In the case of both baymodel_attr and bay_attr being set, the Baymodel
    will be checked first and then Bay if the attribute isn't set on the
    Baymodel.

    Parameters can also be set as 'required'. If a required parameter
    isn't set, a RequiredArgumentNotProvided exception will be raised.
    """
    def __init__(self, heat_param,
                 nodepool_attr=None,
                 required=False,
                 param_type=lambda x: x):
        self.heat_param = heat_param
        self.nodepool_attr = nodepool_attr
        self.required = required
        self.param_type = param_type

    def set_param(self, params, nodepool):
        value = None

        if (self.nodepool_attr and
                  getattr(nodepool, self.nodepool_attr, None) is not None):
            value = getattr(nodepool, self.nodepool_attr)
        elif self.required:
            kwargs = dict(heat_param=self.heat_param)
            raise exception.RequiredParameterNotProvided(**kwargs)

        value = self.param_type(value)
        params[self.heat_param] = value


class OutputMapping(object):
    """A mapping associating heat outputs and bay attr.

    An OutputMapping is an association of a Heat output with a key
    Oasis understands.
    """

    def __init__(self, heat_output, node_attr=None):
        self.node_attr = node_attr
        self.heat_output = heat_output

    def set_output(self, stack, node, nodepool):
        if self.node_attr is None:
            return
        output_value = self.get_output_value(stack)
        if output_value is not None:
            setattr(node, self.node_attr, output_value)

    def matched(self, output_key):
        return self.heat_output == output_key

    def get_output_value(self, stack):
        for output in stack.to_dict().get('outputs', []):
            if output['output_key'] == self.heat_output:
                return output['output_value']

        LOG.warning(_LW('stack does not have output_key %s'), self.heat_output)
        return None


@six.add_metaclass(abc.ABCMeta)
class TemplateDefinition(object):
    '''A mapping between Oasis objects and Heat templates.

    A TemplateDefinition is essentially a mapping between Oasis objects
    and Heat templates. Each TemplateDefinition has a mapping of Heat
    parameters.
    '''
    definitions = None
    provides = list()

    def __init__(self):
        self.param_mappings = list()
        self.output_mappings = list()

    @staticmethod
    def get_template_definition():
        return NodePoolTemplateDefinition()

    def add_parameter(self, *args, **kwargs):
        param = ParameterMapping(*args, **kwargs)
        self.param_mappings.append(param)

    def add_output(self, *args, **kwargs):
        mapping_type = kwargs.pop('mapping_type', OutputMapping)
        output = mapping_type(*args, **kwargs)
        self.output_mappings.append(output)

    def get_output(self, *args, **kwargs):
        for output in self.output_mappings:
            if output.matched(*args, **kwargs):
                return output
        return None

    def get_params(self, context, nodepool, nodepool_policy, **kwargs):
        """Pulls template parameters from Baymodel and/or Bay.

        :param context: Context to pull template parameters for
        :param baymodel: Baymodel to pull template parameters from
        :param bay: Bay to pull template parameters from
        :param extra_params: Any extra params to be provided to the template

        :return: dict of template parameters
        """
        template_params = dict()
        for mapping in self.param_mappings:
            mapping.set_param(template_params, nodepool)
        if 'extra_params' in kwargs:
            template_params.update(kwargs.get('extra_params'))
        return template_params

    def get_heat_param(self, node_attr=None, nodepool_attr=None):
        """Returns stack param name.

        Return stack param name using bay and baymodel attributes
        :param bay_attr bay attribute from which it maps to stack attribute
        :param baymodel_attr baymodel attribute from which it maps
         to stack attribute

        :return stack parameter name or None
        """
        for mapping in self.param_mappings:
            if (mapping.node_attr == node_attr and
                    mapping.nodepool_attr == nodepool_attr):
                return mapping.heat_param
        return None

    def update_outputs(self, stack):
        for output in self.output_mappings:
            output.set_output(stack)

    def extract_definition(self, context, nodepool, nodepool_policy, **kwargs):
        return self.template_path, self.get_params(context, nodepool, nodepool_policy, **kwargs)

    @abc.abstractproperty
    def template_path(self):
        pass


class BaseTemplateDefinition(TemplateDefinition):

    @abc.abstractproperty
    def template_path(self):
        pass

    def get_params(self, context, nodepool, nodepool_policy, **kwargs):
        extra_params = kwargs.pop('extra_params', {})
        # extra_params['trustee_domain_id'] = CONF.trust.trustee_domain_id
        # extra_params['trustee_user_id'] = nodepool.trustee_user_id
        # extra_params['trustee_username'] = nodepool.trustee_username
        # extra_params['trustee_password'] = nodepool.trustee_password
        # extra_params['trust_id'] = nodepool.trust_id
        # extra_params['auth_url'] = context.auth_url

        return super(BaseTemplateDefinition, self).get_params(context, nodepool, nodepool_policy,
                                                              extra_params=extra_params, **kwargs)

    def _get_user_token(self, context, osc, bay):
        """Retrieve user token from the Heat stack or context.

        :param context: The security context
        :param osc: The openstack client
        :param bay: The bay
        :return: A user token
        """
        if hasattr(bay, 'stack_id'):
            stack = osc.heat().stacks.get(bay.stack_id)
            return stack.parameters['user_token']
        else:
            return context.auth_token


class NodePoolTemplateDefinition(BaseTemplateDefinition):

    def __init__(self):
        super(NodePoolTemplateDefinition, self).__init__()
        # self.add_parameter('flavor', nodepool_attr='flavor')
        # self.add_parameter('image', nodepool_attr='image')
        # self.add_parameter('key_name', nodepool_attr='key_name')

    def get_params(self, context, nodepool, nodepool_policy, **kwargs):
        extra_params = kwargs.pop('extra_params', {})
        osc = clients.OpenStackClients(context)
        extra_params['min_size'] = nodepool_policy.min_size
        extra_params['max_size'] = nodepool_policy.max_size
        extra_params['scaleup_adjust'] = nodepool_policy.scaleup_adjust
        extra_params['scaleup_cooldown'] = nodepool_policy.scaleup_cooldown
        extra_params['scaleup_period'] = nodepool_policy.scaleup_period
        extra_params['scaleup_evaluation_periods'] = nodepool_policy.scaleup_evaluation_periods
        extra_params['scaleup_threshold'] = nodepool_policy.scaleup_threshold
        extra_params['scaledown_adjust'] = nodepool_policy.scaledown_adjust
        extra_params['scaledown_cooldown'] = nodepool_policy.scaledown_cooldown
        extra_params['scaledown_period'] = nodepool_policy.scaledown_period
        extra_params['scaledown_evaluation_periods'] = nodepool_policy.scaledown_evaluation_periods
        extra_params['scaledown_threshold'] = nodepool_policy.scaledown_threshold

        extra_params['nodepool_id'] = nodepool.id
        extra_params['amqp_host'] = cfg.CONF.oslo_messaging_rabbit.rabbit_host
        extra_params['amqp_password'] = cfg.CONF.oslo_messaging_rabbit.rabbit_password
        extra_params['amqp_userid'] = cfg.CONF.oslo_messaging_rabbit.rabbit_userid

        return super(NodePoolTemplateDefinition,
                     self).get_params(context, nodepool, nodepool_policy,
                                      extra_params=extra_params,
                                      **kwargs)
    @property
    def template_path(self):
        return cfg.CONF.nodepool_template_path