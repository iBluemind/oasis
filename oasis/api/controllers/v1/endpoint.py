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
from oasis.common import exception
from oasis.common import policy
from oasis import objects
from oasis.objects import fields


class EndpointPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/name', '/desc', '/url']
        return types.JsonPatchType.internal_attrs() + internal_attrs


class Endpoint(base.APIBase):
    """API representation of a endpoint.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this endpoint"""

    name = wtypes.StringType(min_length=1, max_length=255)
    """Name of this endpoint"""

    desc = wtypes.StringType(min_length=1, max_length=255)
    """Description of this endpoint"""

    url = wtypes.StringType(min_length=1, max_length=255)
    """Url of this endpoint"""

    project_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    user_id = wsme.wsattr(wtypes.text, readonly=True)
    """Stack id of the heat stack"""

    def __init__(self, **kwargs):
        super(Endpoint, self).__init__()

        self.fields = []
        for field in objects.Endpoint.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(endpoint, url, expand=True):
        if not expand:
            endpoint.unset_fields_except(['id', 'name', 'url', 'desc', 'created_at'])

            endpoint.links = [link.Link.make_link('self', url,
                                         'endpoints', endpoint.id),
                     link.Link.make_link('bookmark', url,
                                         'endpoints', endpoint.id,
                                         bookmark=True)]
        return endpoint

    @classmethod
    def convert_with_links(cls, rpc_endpoint, expand=True):
        endpoint = Endpoint(**rpc_endpoint.as_dict())
        return cls._convert_with_links(endpoint, pecan.request.host_url, expand)


class EndpointCollection(collection.Collection):

    endpoints = [Endpoint]

    def __init__(self, **kwargs):
        self._type = 'endpoints'

    @staticmethod
    def convert_with_links(rpc_endpoints, limit, url=None, expand=False, **kwargs):

        collection = EndpointCollection()
        collection.endpoints = [Endpoint.convert_with_links(p, expand)
                                for p in rpc_endpoints]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class EndpointsController(rest.RestController):

    def __init__(self):
        super(EndpointsController, self).__init__()

    def _get_endpoints_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Endpoint.get_by_id(pecan.request.context,
                                                    marker)

        endpoints = objects.Endpoint.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        print 'aaaa'
        print endpoints
        print 'aaaa'

        return EndpointCollection.convert_with_links(endpoints, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(EndpointCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of endpoints.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'endpoint:get_all',
                       action='endpoint:get_all')
        return self._get_endpoints_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(Endpoint, body=Endpoint, status_code=201)
    def post(self, endpoint):
        """Create a new function.

        :param endpoint: a endpoint within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'endpoint:create',
                       action='endpoint:create')
        endpoint_dict = endpoint.as_dict()

        endpoint_dict['project_id'] = context.project_id
        endpoint_dict['user_id'] = context.user_id

        if endpoint_dict.get('name') is None:
            endpoint_dict['name'] = None
        if endpoint_dict.get('url') is None:
            endpoint_dict['url'] = None
        if endpoint_dict.get('desc') is None:
            endpoint_dict['desc'] = None

        endpoint = objects.Endpoint(context, **endpoint_dict)

        endpoint.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return Endpoint.convert_with_links(endpoint)

    @expose.expose(Endpoint, types.uuid_or_name)
    def get_one(self, endpoint_ident):
        """Retrieve information about the given function.

        :param function_ident: UUID of a function or logical name of the function.
        """
        context = pecan.request.context
        endpoint = api_utils.get_resource('Endpoint', endpoint_ident)
        # policy.enforce(context, 'endpoint:get', function,
        #                action='endpoint:get')

        return Endpoint.convert_with_links(endpoint)
