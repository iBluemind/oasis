# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import timeutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes

from oasis.api.controllers import base
from oasis.api.controllers import link
from oasis.api.controllers.v1 import collection
from oasis.api.controllers.v1 import types
from oasis.api import expose
from oasis.api import utils as api_utils
# from oasis.api.validation import validate_function_properties
from oasis.common import exception
from oasis.common import policy
from oasis import objects
from oasis.objects import fields


class NodePoolPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return []

    @staticmethod
    def internal_attrs():
        internal_attrs = []
        return types.JsonPatchType.internal_attrs() + internal_attrs


class NodePool(base.APIBase):
    """API representation of a nodepool.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a nodepool.
    """

    id = types.uuid

    project_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    user_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    stack_id = types.uuid

    function_id = types.uuid

    nodepool_policy_id = types.uuid

    host = wtypes.StringType(min_length=1, max_length=255)

    name = wtypes.StringType(min_length=1, max_length=255)

    status = wtypes.Enum(str, *fields.NodePoolStatus.ALL)
    """Status of the function from the heat stack"""

    status_reason = wtypes.text
    """Status reason of the function from the heat stack"""

    def __init__(self, **kwargs):
        super(NodePool, self).__init__()

        self.fields = []
        for field in objects.NodePool.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(nodepool, url, expand=True):
        if not expand:
            nodepool.unset_fields_except(['id', 'name', 'updated_at', 'created_at',
                                          'proejct_id', 'stack_id', 'user_id', 'host',
                                          'status', 'function_id', 'nodepool_policy_id', 'status_reason'])
            nodepool.links = [link.Link.make_link('self', url,
                                         'nodepools', nodepool.id),
                     link.Link.make_link('bookmark', url,
                                         'nodepools', nodepool.id,
                                         bookmark=True)]
        return nodepool

    @classmethod
    def convert_with_links(cls, rpc_nodepool, expand=True):
        nodepool = NodePool(**rpc_nodepool.as_dict())
        return cls._convert_with_links(nodepool, pecan.request.host_url, expand)

    @classmethod
    def sample(cls, expand=True):
        sample = cls(id='88c3153e-d5bf-4b7e-c234-fb518e17f34c',
                     project_id='88c3153e-d5bf-4b7e-c234-fb518e17f34c',
                     user_id='4a96ac4b-2447-43f1-8ca6-9fd6f36d146d',
                     stack_id='4a96ac4b-2447-43f1-8ca6-9fd6f36d146d',
                     function_id='4a96ac4b-2447-43f1-8ca6-9fd6f36d146d',
                     nodepool_policy_id='4a96ac4b-2447-43f1-8ca6-9fd6f36d146d',
                     host='192.168.0.1',
                     name='test',
                     status='Running')
        return cls._convert_with_links(sample, 'http://localhost:9417', expand)


class NodePoolCollection(collection.Collection):
    """API representation of a collection of nodepools."""

    nodepools = [NodePool]
    """A list containing nodepools objects"""

    def __init__(self, **kwargs):
        self._type = 'nodepools'

    @staticmethod
    def convert_with_links(rpc_bays, limit, url=None, expand=False, **kwargs):
        collection = NodePoolCollection()
        collection.nodepools = [NodePool.convert_with_links(p, expand)
                           for p in rpc_bays]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection

    @classmethod
    def sample(cls):
        sample = cls()
        sample.nodepools = [NodePool.sample(expand=False)]
        return sample


class NodePoolsController(rest.RestController):
    """REST controller for NodePools."""
    def __init__(self):
        super(NodePoolsController, self).__init__()

    _custom_actions = {
        'detail': ['GET'],
    }

    def _get_nodepools_collection(self, marker, limit,
                             sort_key, sort_dir, expand=False,
                             resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.NodePool.get_by_id(pecan.request.context,
                                                 marker)

        nodepools = objects.NodePool.list(pecan.request.context, limit,
                                marker_obj, sort_key=sort_key,
                                sort_dir=sort_dir)

        return NodePoolCollection.convert_with_links(nodepools, limit,
                                                url=resource_url,
                                                expand=expand,
                                                sort_key=sort_key,
                                                sort_dir=sort_dir)

    @expose.expose(NodePoolCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of nodepools.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        return self._get_nodepools_collection(marker, limit, sort_key,
                                         sort_dir)

    @expose.expose(NodePoolCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def detail(self, marker=None, limit=None, sort_key='id',
               sort_dir='asc'):
        """Retrieve a list of nodepools with detail.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context

        # NOTE(lucasagomes): /detail should only work against collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "nodepools":
            raise exception.HTTPNotFound

        expand = True
        resource_url = '/'.join(['nodepools', 'detail'])
        return self._get_nodepools_collection(marker, limit,
                                         sort_key, sort_dir, expand,
                                         resource_url)

    @expose.expose(NodePool, types.uuid_or_name)
    def get_one(self, nodepool_ident):
        """Retrieve information about the given bay.

        :param nodepool_ident: ID of a nodepool or logical name of the nodepool.
        """
        nodepool = api_utils.get_resource('NodePool', nodepool_ident)
        return NodePool.convert_with_links(nodepool)

    @expose.expose(NodePool, body=NodePool, status_code=201)
    def post(self, nodepool):
        """Create a new nodepool.

        :param nodepool: a nodepool within the request body.
        """
        context = pecan.request.context
        nodepool_dict = nodepool.as_dict()
        nodepool_dict['project_id'] = context.project_id
        nodepool_dict['user_id'] = context.user_id

        nodepool = objects.NodePool(context, **nodepool_dict)
        # nodepool.create()

        pecan.request.conductor_rpcapi.nodepool_create(nodepool, nodepool_create_timeout=30000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('nodepools', nodepool.id)
        return NodePool.convert_with_links(nodepool)

        # res_nodepool = pecan.request.conductor_rpcapi.nodepool_create(nodepool,
        #                                           nodepool.nodepool_create_timeout)

        # # Set the HTTP Location Header
        # pecan.response.location = link.build_url('nodepools', res_nodepool.uuid)
        # return NodePool.convert_with_links(res_nodepool)

    @wsme.validate(types.uuid, [NodePoolPatchType])
    @expose.expose(NodePool, types.uuid_or_name, body=[NodePoolPatchType])
    def patch(self, nodepool_ident, patch):
        """Update an existing nodepool.

        :param bay_ident: UUID or logical name of a nodepool.
        :param patch: a json PATCH document to apply to this nodepool.
        """
        context = pecan.request.context
        nodepool = api_utils.get_resource('NodePool', nodepool_ident)
        try:
            nodepool_dict = nodepool.as_dict()
            nodepool_dict['project_id'] = context.project_id
            nodepool_dict['user_id'] = context.user_id
            new_nodepool = NodePool(**api_utils.apply_jsonpatch(nodepool_dict, patch))
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.NodePool.fields:
            try:
                patch_val = getattr(new_nodepool, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if nodepool[field] != patch_val:
                nodepool[field] = patch_val

        # delta = nodepool.obj_what_changed()

        # validate_function_properties(delta)

        # res_nodepool = pecan.request.conductor_rpcapi.nodepool_update(nodepool)
        nodepool.save()

        return NodePool.convert_with_links(nodepool)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, nodepool_ident):
        """Delete a nodepool.

        :param nodepool_ident: UUID of a nodepool or logical name of the nodepool.
        """
        context = pecan.request.context
        nodepool = api_utils.get_resource('NodePool', nodepool_ident)

        # pecan.request.conductor_rpcapi.function_delete(nodepool)
        nodepool.destroy()
