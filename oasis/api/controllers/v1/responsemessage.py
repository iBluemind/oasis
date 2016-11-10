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


class ResponseMessagePatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/stack_id']

    @staticmethod
    def internal_attrs():
        internal_attrs = ['/message', '/response_statuscode_id', ]
        return types.JsonPatchType.internal_attrs() + internal_attrs


class ResponseMessage(base.APIBase):
    """API representation of a responsemessage.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a function.
    """

    id = types.uuid
    """Unique UUID for this responsemessage"""

    message = wtypes.StringType(min_length=1, max_length=255)
    """Name of this responsemessage"""

    response_statuscode_id = wtypes.StringType(min_length=1, max_length=255)
    """Description of this responsemessage"""

    def __init__(self, **kwargs):
        super(ResponseMessage, self).__init__()

        self.fields = []
        for field in objects.ResponseMessage.fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @staticmethod
    def _convert_with_links(responsemessage, url, expand=True):
        if not expand:
            responsemessage.unset_fields_except(['id', 'message', 'response_statuscode_id', 'created_at'])

            responsemessage.links = [link.Link.make_link('self', url,
                                    'responsemessages', responsemessage.id),
                                    link.Link.make_link('bookmark', url,
                                     'responsemessages', responsemessage.id,
                                     bookmark=True)]
        return responsemessage

    @classmethod
    def convert_with_links(cls, rpc_responsemessage, expand=True):
        responsemessage = ResponseMessage(**rpc_responsemessage.as_dict())
        return cls._convert_with_links(responsemessage, pecan.request.host_url, expand)


class ResponseMessageCollection(collection.Collection):

    responsemessages = [ResponseMessage]

    def __init__(self, **kwargs):
        self._type = 'responsemessages'

    @staticmethod
    def convert_with_links(rpc_responsemessages, limit, url=None, expand=False, **kwargs):
        collection = ResponseMessageCollection()
        collection.responsemessages = [ResponseMessage.convert_with_links(p, expand)
                                for p in rpc_responsemessages]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class ResponseMessagesController(rest.RestController):

    def __init__(self):
        super(ResponseMessagesController, self).__init__()

    def _get_responsemessages_collection(self, marker, limit, sort_key,
                                  sort_dir, expand=False, resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.ResponseMessage.get_by_id(pecan.request.context,
                                                    marker)

        responsemessages = objects.ResponseMessage.list(pecan.request.context, limit,
                                          marker_obj, sort_key=sort_key,
                                          sort_dir=sort_dir)

        return ResponseMessageCollection.convert_with_links(responsemessages, limit,
                                                     url=resource_url,
                                                     expand=expand,
                                                     sort_key=sort_key,
                                                     sort_dir=sort_dir)

    @expose.expose(ResponseMessageCollection, types.uuid, int, wtypes.text,
                   wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id',
                sort_dir='asc'):
        """Retrieve a list of responsemessages.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        return self._get_responsemessages_collection(marker, limit, sort_key, sort_dir)

    @expose.expose(ResponseMessage, body=ResponseMessage, status_message=201)
    def post(self, responsemessage):
        """Create a new function.

        :param responsemessage: a responsemessage within the request body.
        """
        context = pecan.request.context
        responsemessage_dict = responsemessage.as_dict()

        if responsemessage_dict.get('message') is None:
            responsemessage_dict['message'] = None
        if responsemessage_dict.get('response_statuscode_id') is None:
            responsemessage_dict['response_statuscode_id'] = None

        responsemessage = objects.ResponseMessage(context, **responsemessage_dict)

        responsemessage.create()

        # pecan.request.rpcapi.function_create(function, function_create_timeout=1000)

        # Set the HTTP Location Header
        # pecan.response.location = link.build_url('functions',
        #                                          function.id)
        return ResponseMessage.convert_with_links(responsemessage)
