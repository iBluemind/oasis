from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class Request(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'http_api_id': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(request, db_request):
        """Converts a database entity to a formal object."""
        for field in request.fields:
            if field != 'request':
                request[field] = db_request[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from request to request_id.
        # The request_id must be populated first in the loop before it can be
        # used to find the request.
        request.obj_reset_changes()
        return request

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [Request._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, request_id):
        """Find a request based on its id or uuid and return a Request object.

        :param request_id: the id *or* uuid of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(request_id):
            return cls.get_by_id(context, request_id)
        elif utils.is_uuid_like(request_id):
            return cls.get_by_uuid(context, request_id)
        else:
            raise exception.InvalidIdentity(identity=request_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, request_id):
        """Find a request based on its integer id and return a Function object.

        :param request_id: the id of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_id(context, request_id)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a request based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_uuid(context, uuid)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a request based on name and return a Request object.

        :param name: the logical name of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_name(context, name)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def get_by_id(cls, context, request_id):
        """Find a request based on its integer id and return a Request object.

        :param request_id: the id of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_id(context, request_id)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a request based on uuid and return a :class:`Request` object.

        :param uuid: the uuid of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_uuid(context, uuid)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a request based on name and return a Request object.

        :param name: the logical name of a request.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_request = cls.dbapi.get_request_by_name(context, name)
        request = Request._from_db_object(cls(context), db_request)
        return request

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of Request objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_requests = cls.dbapi.get_request_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return Request._from_db_object_list(db_requests, cls, context)

    @base.remotable
    def create(self, context=None):
        """Create a NodePool record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: NodePool(context)

        """
        values = self.obj_get_changes()
        db_request = self.dbapi.create_request(values)
        self._from_db_object(self, db_request)