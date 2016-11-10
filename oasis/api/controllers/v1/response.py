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


class ResponsePatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/http_api_id', ]
        return types.JsonPatchType.internal_attrs() + internal_attrs


class Response(base.APIBase):
    """API representation of a response.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this response"""

    http_api_id = types.uuid
    """Url of this response"""

    def __init__(self, **kwargs):
        super(Response, self).__init__()

        self.fields = []
        for field in objects.Response.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(response, url, expand=True):
        if not expand:
            response.unset_fields_except(['id', 'http_api_id', 'created_at'])

            response.links = [link.Link.make_link('self', url,
                                         'responses', response.id),
                     link.Link.make_link('bookmark', url,
                                         'responses', response.id,
                                         bookmark=True)]
        return response

    @classmethod
    def convert_with_links(cls, rpc_response, expand=True):
        response = Response(**rpc_response.as_dict())
        return cls._convert_with_links(response, pecan.request.host_url, expand)


class ResponseCollection(collection.Collection):

    responses = [Response]

    def __init__(self, **kwargs):
        self._type = 'responses'

    @staticmethod
    def convert_with_links(rpc_responses, limit, url=None, expand=False, **kwargs):
        collection = ResponseCollection()
        collection.responses = [Response.convert_with_links(p, expand)
                                for p in rpc_responses]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class ResponsesController(rest.RestController):

    def __init__(self):
        super(ResponsesController, self).__init__()

    def _get_responses_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Response.get_by_id(pecan.request.context,
                                                    marker)

        responses = objects.Response.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return ResponseCollection.convert_with_links(responses, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(ResponseCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of responses.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        return self._get_responses_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(Response, body=Response, status_code=201)
    def post(self, response):
        """Create a new function.

        :param response: a response within the request body.
        """
        context = pecan.request.context
        response_dict = response.as_dict()

        if response_dict.get('http_api_id') is None:
            response_dict['http_api_id'] = None

        response = objects.Response(context, **response_dict)

        response.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return Response.convert_with_links(response)
