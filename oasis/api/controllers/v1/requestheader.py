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


class RequestHeaderPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/name', '/value', '/request_id']
        return types.JsonPatchType.internal_attrs() + internal_attrs


class RequestHeader(base.APIBase):
    """API representation of a requestheader.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this requestheader"""

    name = wtypes.StringType(min_length=1, max_length=255)
    """Name of this requestheader"""

    value = wtypes.StringType(min_length=1, max_length=255)
    """Description of this requestheader"""

    request_id = types.uuid
    """Url of this requestheader"""

    def __init__(self, **kwargs):
        super(RequestHeader, self).__init__()

        self.fields = []
        for field in objects.RequestHeader.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(requestheader, url, expand=True):
        if not expand:
            requestheader.unset_fields_except(['id', 'name', 'value', 'request_id', 'created_at'])

            requestheader.links = [link.Link.make_link('self', url,
                                         'requestheaders', requestheader.id),
                     link.Link.make_link('bookmark', url,
                                         'requestheaders', requestheader.id,
                                         bookmark=True)]
        return requestheader

    @classmethod
    def convert_with_links(cls, rpc_requestheader, expand=True):
        requestheader = RequestHeader(**rpc_requestheader.as_dict())
        return cls._convert_with_links(requestheader, pecan.request.host_url, expand)


class RequestHeaderCollection(collection.Collection):

    requestheaders = [RequestHeader]

    def __init__(self, **kwargs):
        self._type = 'requestheaders'

    @staticmethod
    def convert_with_links(rpc_requestheaders, limit, url=None, expand=False, **kwargs):
        collection = RequestHeaderCollection()
        collection.requestheaders = [RequestHeader.convert_with_links(p, expand)
                                for p in rpc_requestheaders]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class RequestHeadersController(rest.RestController):

    def __init__(self):
        super(RequestHeadersController, self).__init__()

    def _get_requestheaders_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.RequestHeader.get_by_id(pecan.request.context,
                                                    marker)

        requestheaders = objects.RequestHeader.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return RequestHeaderCollection.convert_with_links(requestheaders, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(RequestHeaderCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of requestheaders.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'requestheader:get_all',
                       action='requestheader:get_all')
        return self._get_requestheaders_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(RequestHeader, body=RequestHeader, status_code=201)
    def post(self, requestheader):
        """Create a new function.

        :param requestheader: a requestheader within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'requestheader:create',
                       action='requestheader:create')
        requestheader_dict = requestheader.as_dict()

        if requestheader_dict.get('name') is None:
            requestheader_dict['name'] = None
        if requestheader_dict.get('value') is None:
            requestheader_dict['value'] = None
        if requestheader_dict.get('request_id') is None:
            requestheader_dict['request_id'] = None

        requestheader = objects.RequestHeader(context, **requestheader_dict)

        requestheader.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return RequestHeader.convert_with_links(requestheader)
