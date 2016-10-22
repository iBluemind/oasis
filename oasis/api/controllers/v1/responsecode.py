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


class ResponseCodePatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/status_code', '/response_id', ]
        return types.JsonPatchType.internal_attrs() + internal_attrs


class ResponseCode(base.APIBase):
    """API representation of a responsecode.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this responsecode"""

    status_code = wtypes.StringType(min_length=1, max_length=255)
    """Name of this responsecode"""

    response_id = types.uuid
    """Description of this responsecode"""

    def __init__(self, **kwargs):
        super(ResponseCode, self).__init__()

        self.fields = []
        for field in objects.ResponseCode.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(responsecode, url, expand=True):
        if not expand:
            responsecode.unset_fields_except(['id', 'status_code', 'response_id', 'created_at'])

            responsecode.links = [link.Link.make_link('self', url,
                                    'responsecodes', responsecode.id),
                                    link.Link.make_link('bookmark', url,
                                     'responsecodes', responsecode.id,
                                     bookmark=True)]
        return responsecode

    @classmethod
    def convert_with_links(cls, rpc_responsecode, expand=True):
        responsecode = ResponseCode(**rpc_responsecode.as_dict())
        return cls._convert_with_links(responsecode, pecan.request.host_url, expand)


class ResponseCodeCollection(collection.Collection):

    responsecodes = [ResponseCode]

    def __init__(self, **kwargs):
        self._type = 'responsecodes'

    @staticmethod
    def convert_with_links(rpc_responsecodes, limit, url=None, expand=False, **kwargs):
        collection = ResponseCodeCollection()
        collection.responsecodes = [ResponseCode.convert_with_links(p, expand)
                                for p in rpc_responsecodes]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class ResponseCodesController(rest.RestController):

    def __init__(self):
        super(ResponseCodesController, self).__init__()

    def _get_responsecodes_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.ResponseCode.get_by_id(pecan.request.context,
                                                    marker)

        responsecodes = objects.ResponseCode.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return ResponseCodeCollection.convert_with_links(responsecodes, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(ResponseCodeCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of responsecodes.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        policy.enforce(context, 'responsecode:get_all',
                       action='responsecode:get_all')
        return self._get_responsecodes_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(ResponseCode, body=ResponseCode, status_code=201)
    def post(self, responsecode):
        """Create a new function.

        :param responsecode: a responsecode within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, 'responsecode:create',
                       action='responsecode:create')
        responsecode_dict = responsecode.as_dict()

        if responsecode_dict.get('status_code') is None:
            responsecode_dict['status_code'] = None
        if responsecode_dict.get('response_id') is None:
            responsecode_dict['response_id'] = None

        responsecode = objects.ResponseCode(context, **responsecode_dict)

        responsecode.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return ResponseCode.convert_with_links(responsecode)
