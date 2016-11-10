import pecan
from pecan import rest

from wsme import types as wtypes
from oasis.api.controllers import base
from oasis.api.controllers import link
from oasis.api.controllers.v1 import collection
from oasis.api.controllers.v1 import types
from oasis.api import expose
from oasis.api import utils as api_utils
from oasis.common import policy
from oasis import objects


class HttpApiPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/method', '/endpoint_id',]
        return types.JsonPatchType.internal_attrs() + internal_attrs


class HttpApi(base.APIBase):
    """API representation of a http api.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this http api"""

    method = wtypes.StringType(min_length=1, max_length=255)
    """method of this endpoint"""

    endpoint_id = types.uuid
    """id of this endpoint"""

    def __init__(self, **kwargs):
        super(HttpApi, self).__init__()

        self.fields = []
        for field in objects.HttpApi.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(httpapi, url, expand=True):
        if not expand:
            httpapi.unset_fields_except(['id', 'method', 'endpoint_id',])

            httpapi.links = [link.Link.make_link('self', url,
                                         'httpapis', httpapi.id),
                     link.Link.make_link('bookmark', url,
                                         'httpapis', httpapi.id,
                                         bookmark=True)]
        return httpapi

    @classmethod
    def convert_with_links(cls, rpc_httpapi, expand=True):
        httpapi = HttpApi(**rpc_httpapi.as_dict())
        return cls._convert_with_links(httpapi, pecan.request.host_url, expand)


class HttpApiCollection(collection.Collection):

    httpapis = [HttpApi]

    def __init__(self, **kwargs):
        self._type = 'httpapis'

    @staticmethod
    def convert_with_links(rpc_httpapis, limit, url=None, expand=False, **kwargs):
        collection = HttpApiCollection()
        collection.httpapis = [HttpApi.convert_with_links(p, expand)
                                for p in rpc_httpapis]
        collection.next = collection.get_next(limit, url=url, **kwargs)

        return collection


class HttpApisController(rest.RestController):

    def __init__(self):
        super(HttpApisController, self).__init__()

    def _get_httpapis_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None, endpoint_id=None):

        context = pecan.request.context
        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None

        if marker:
            marker_obj = objects.HttpApi.get_by_id(pecan.request.context,
                                                    marker)

        filters = {'endpoint_id': endpoint_id}

        httpapis = objects.HttpApi.list(context,
                                        limit,
                                        marker_obj,
                                        sort_key,
                                        sort_dir,
                                        filters=filters)

        return HttpApiCollection.convert_with_links(httpapis, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(HttpApi, body=HttpApi, status_code=201)
    def post(self, httpapi):
        """Create a new httpapi.

        :param httpapi: a endpoint within the request body.
        """
        context = pecan.request.context
        httpapi_dict = httpapi.as_dict()

        httpapi_dict['project_id'] = context.project_id
        httpapi_dict['user_id'] = context.user_id

        if httpapi_dict.get('method') is None:
            httpapi_dict['method'] = None
        if httpapi_dict.get('endpoint_id') is None:
            httpapi_dict['endpoint_id'] = None

        httpapi = objects.HttpApi(context, **httpapi_dict)

        httpapi.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return HttpApi.convert_with_links(httpapi)

    @expose.expose(HttpApiCollection, types.uuid_or_name)
    def get_one(self, endpoint_ident):
        """Retrieve information about the given bay.

        :param nodepool_ident: ID of a nodepool or logical name of the nodepool.
        """

        return self._get_httpapis_collection(marker=None, limit=None, sort_key='id',
                                             sort_dir='asc', endpoint_id=endpoint_ident)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, httpapi_ident):
        """Delete a HttpApi.

        :param httpapi_ident: ID of a httpapi
        """
        httpapi = api_utils.get_resource('HttpApi', httpapi_ident)
        httpapi.destroy()
