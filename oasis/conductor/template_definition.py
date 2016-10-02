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

from oasis.common import clients
from oasis.common import exception
from oasis.common import paths
from oasis.i18n import _
from oasis.i18n import _LW


LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('trustee_domain_id', 'oasis.common.keystone', group='trust')


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
    def __init__(self, heat_param, node_attr=None,
                 nodepool_attr=None,
                 required=False,
                 param_type=lambda x: x):
        self.heat_param = heat_param
        self.node_attr = node_attr
        self.nodepool_attr = nodepool_attr
        self.required = required
        self.param_type = param_type

    def set_param(self, params, node, nodepool):
        value = None

        if (self.node_attr and
                    getattr(node, self.node_attr, None) is not None):
            value = getattr(node, self.node_attr)
        elif (self.nodepool_attr and
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
    Magnum understands.
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
    '''A mapping between Magnum objects and Heat templates.

    A TemplateDefinition is essentially a mapping between Magnum objects
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

    def get_params(self, context, node, nodepool, **kwargs):
        """Pulls template parameters from Baymodel and/or Bay.

        :param context: Context to pull template parameters for
        :param baymodel: Baymodel to pull template parameters from
        :param bay: Bay to pull template parameters from
        :param extra_params: Any extra params to be provided to the template

        :return: dict of template parameters
        """
        template_params = dict()
        for mapping in self.param_mappings:
            mapping.set_param(template_params, node, nodepool)
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

    def extract_definition(self, context, node, nodepool, **kwargs):
        return self.template_path, self.get_params(context, node, nodepool, **kwargs)


class BaseTemplateDefinition(TemplateDefinition):
    @abc.abstractproperty
    def template_path(self):
        pass

    def get_params(self, context, node, nodepool, **kwargs):
        extra_params = kwargs.pop('extra_params', {})
        extra_params['trustee_domain_id'] = CONF.trust.trustee_domain_id
        extra_params['trustee_user_id'] = context.trustee_user_id
        extra_params['trustee_username'] = context.trustee_username
        extra_params['trustee_password'] = context.trustee_password
        extra_params['trust_id'] = context.trust_id
        extra_params['auth_url'] = context.auth_url

        return super(BaseTemplateDefinition,
                     self).get_params(context, node, nodepool,
                                      extra_params=extra_params,
                                      **kwargs)

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
        super(NodePoolTemplateDefinition).__init__()
        self.add_parameter('flavor', node_attr='flavor')
        self.add_parameter('image', node_attr='image')
        self.add_parameter('private_network', node_pool_attr='private_network')
        self.add_parameter('public_network', node_pool_attr='public_network')
        self.add_parameter('subnet', node_pool_attr='subnet')
        self.add_parameter('key_name', node_attr='key_name')

    def get_params(self, context, node, nodepool, **kwargs):
        extra_params = kwargs.pop('extra_params', {})
        # HACK(apmelton) - This uses the user's bearer token, ideally
        # it should be replaced with an actual trust token with only
        # access to do what the template needs it to do.
        osc = clients.OpenStackClients(context)
        extra_params['auth_url'] = context.auth_url
        extra_params['username'] = context.user_name
        extra_params['tenant_name'] = context.tenant
        extra_params['domain_name'] = context.domain_name
        extra_params['region_name'] = osc.cinder_region_name()

        return super(NodePoolTemplateDefinition,
                     self).get_params(context, node, nodepool,
                                      extra_params=extra_params,
                                      **kwargs)
