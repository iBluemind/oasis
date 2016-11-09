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

from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class FunctionPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/project_id']
        return types.JsonPatchType.internal_attrs() + internal_attrs


class Function(base.APIBase):
    """API representation of a function.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this function"""

    name = wtypes.StringType(min_length=1, max_length=255)
    """Name of this function"""
    desc = wtypes.StringType(min_length=1, max_length=255)
    """Description of this function"""

    endpoint_id = wtypes.StringType(min_length=1, max_length=255)
    """Endpoint Id of this function"""

    nodepool_id = wtypes.StringType(min_length=1, max_length=255)
    """Nodepool Id of this function"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link and associated function links"""

    stack_id = wsme.wsattr(wtypes.text, readonly=False)
    """Stack id of the heat stack"""

    project_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    user_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    status = wtypes.text

    body = wtypes.text
    """Url used for function node discovery"""

    def __init__(self, **kwargs):
        super(Function, self).__init__()

        self.fields = []
        for field in objects.Function.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(function, url, expand=True):
        if not expand:
            function.unset_fields_except(['id', 'name',
                                     'status', 'status_reason', 'desc',
                                     'nodepool_id', 'endpoint_id',
                                     'body', 'stack_id', 'created_at'])

            function.links = [link.Link.make_link('self', url,
                                         'functions', function.id),
                     link.Link.make_link('bookmark', url,
                                         'functions', function.id,
                                         bookmark=True)]
        return function

    @classmethod
    def convert_with_links(cls, rpc_function, expand=True):
        function = Function(**rpc_function.as_dict())
        return cls._convert_with_links(function, pecan.request.host_url, expand)

    @classmethod
    def sample(cls, expand=True):
        sample = cls(id='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
                     name='example',
                     project_id='4a96ac4b-2447-43f1-8ca6-9fd6f36d146d',
                     user_id=2,
                     function_create_timeout=15,
                     desc='example description',
                     endpoint_id='123afsfrw34534terw',
                     nodepool_id='13fgerg45tyerfger',
                     stack_id='49dc23f5-ffc9-40c3-9d34-7be7f9e34d63',
                     status=fields.FunctionStatus.CREATE_COMPLETE,
                     status_reason="CREATE completed successfully",
                     body='def hello(): print \'hello\'',
                     created_at=timeutils.utcnow(),
                     updated_at=timeutils.utcnow())
        return cls._convert_with_links(sample, 'http://localhost:9417', expand)


class FunctionCollection(collection.Collection):
    """API representation of a collection of functions."""

    functions = [Function]
    """A list containing functions objects"""

    def __init__(self, **kwargs):
        self._type = 'functions'

    @staticmethod
    def convert_with_links(rpc_functions, limit, url=None, expand=False, **kwargs):
        collection = FunctionCollection()
        collection.functions = [Function.convert_with_links(p, expand)
                           for p in rpc_functions]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection

    @classmethod
    def sample(cls):
        sample = cls()
        sample.functions = [Function.sample(expand=False)]
        return sample


class FunctionsController(rest.RestController):
    """REST controller for Functions."""
    def __init__(self):
        super(FunctionsController, self).__init__()

    _custom_actions = {
        'detail': ['GET'],
    }

    def _get_functions_collection(self, marker, limit,
                                  sort_key, sort_dir, expand=False,
                                  resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Function.get_by_id(pecan.request.context,
                                                    marker)

        functions = objects.Function.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return FunctionCollection.convert_with_links(functions, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(FunctionCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of functions.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'function:get_all',
                       action='function:get_all')
        return self._get_functions_collection(marker, limit, sort_key,
                                         sort_dir)

    @expose.expose(FunctionCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def detail(self, marker=None, limit=None, sort_key='id',
               sort_dir='asc'):
        """Retrieve a list of functions with detail.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'function:detail',
                       action='function:detail')

        # NOTE(lucasagomes): /detail should only work against collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "functions":
            raise exception.HTTPNotFound

        expand = True
        resource_url = '/'.join(['functions', 'detail'])
        return self._get_functions_collection(marker, limit,
                                         sort_key, sort_dir, expand,
                                         resource_url)

    @expose.expose(Function, types.uuid_or_name)
    def get_one(self, function_ident):
        """Retrieve information about the given function.

        :param function_ident: UUID of a function or logical name of the function.
        """
        context = pecan.request.context

        function = api_utils.get_resource('Function', function_ident)
        policy.enforce(context, 'function:get', function,
                       action='function:get')

        return Function.convert_with_links(function)

    @expose.expose(Function, body=Function, status_code=201)
    def post(self, function):
        """Create a new function.

        :param function: a function within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'function:create',
                       action='function:create')
        function_dict = function.as_dict()

        function_dict['project_id'] = context.project_id
        function_dict['user_id'] = context.user_id

        if function_dict.get('name') is None:
            function_dict['name'] = None
        if function_dict.get('body') is None:
            function_dict['body'] = None
        if function_dict.get('desc') is None:
            function_dict['desc'] = None
        if function_dict.get('endpoint_id') is None:
            function_dict['endpoint_id'] = None
        if function_dict.get('nodepool_id') is None:
            function_dict['nodepool_id'] = None

        function = objects.Function(context, **function_dict)

        function.create()

        pecan.request.agent_rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return Function.convert_with_links(function)

    @wsme.validate(types.uuid, [FunctionPatchType])
    @expose.expose(Function, types.uuid_or_name, body=[FunctionPatchType])
    def patch(self, function_ident, patch):
        """Update an existing function.

        :param function_ident: UUID or logical name of a function.
        :param patch: a json PATCH document to apply to this function.
        """
        context = pecan.request.context
        function = api_utils.get_resource('Function', function_ident)

        # policy.enforce(context, 'function:update', function,
        #                action='function:update')
        try:
            function_dict = function.as_dict()
            new_function = Function(**api_utils.apply_jsonpatch(function_dict, patch))
            LOG.debug(new_function)
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.Function.fields:
            try:
                patch_val = getattr(new_function, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if function[field] != patch_val:
                function[field] = patch_val

        # delta = function.obj_what_changed()
        function.save()
        # validate_function_properties(delta)

        # res_function = pecan.request.agent_rpcapi.function_update(function)
        return Function.convert_with_links(function)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, function_ident):
        """Delete a function.

        :param function_ident: UUID of a bay or logical name of the function.
        """
        context = pecan.request.context
        function = api_utils.get_resource('Function', function_ident)
        policy.enforce(context, 'function:delete', function,
                       action='function:delete')
        function.destroy()
        # pecan.request.agent_rpcapi.function_delete(function)


