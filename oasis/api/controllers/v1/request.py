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


class RequestPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/http_api_id',]
        return types.JsonPatchType.internal_attrs() + internal_attrs


class Request(base.APIBase):
    """API representation of a http api.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this http api"""

    http_api_id = types.uuid
    """id of this endpoint"""

    def __init__(self, **kwargs):
        super(Request, self).__init__()

        self.fields = []
        for field in objects.Request.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(request, url, expand=True):
        if not expand:
            request.unset_fields_except(['id', 'http_api_id', 'created_at'])

            request.links = [link.Link.make_link('self', url,
                                         'requests', request.id),
                     link.Link.make_link('bookmark', url,
                                         'requests', request.id,
                                         bookmark=True)]
        return request

    @classmethod
    def convert_with_links(cls, rpc_request, expand=True):
        request = Request(**rpc_request.as_dict())
        return cls._convert_with_links(request, pecan.request.host_url, expand)


class RequestCollection(collection.Collection):

    requests = [Request]

    def __init__(self, **kwargs):
        self._type = 'requests'

    @staticmethod
    def convert_with_links(rpc_requests, limit, url=None, expand=False, **kwargs):
        collection = RequestCollection()
        collection.endpoints = [Request.convert_with_links(p, expand)
                                for p in rpc_requests]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class RequestsController(rest.RestController):

    def __init__(self):
        super(RequestsController, self).__init__()

    def _get_requests_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Request.get_by_id(pecan.request.context,
                                                    marker)

        endpoints = objects.Request.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return RequestCollection.convert_with_links(endpoints, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(RequestCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of requests.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'request:get_all',
                       action='request:get_all')
        return self._get_requests_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(Request, body=Request, status_code=201)
    def post(self, request):
        """Create a new request.

        :param request: a endpoint within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'request:create',
                       action='request:create')
        request_dict = request.as_dict()

        if request_dict.get('http_api_id') is None:
            request_dict['http_api_id'] = None

        request = objects.Request(context, **request_dict)

        request.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return Request.convert_with_links(request)
