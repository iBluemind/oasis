from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class Response(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'http_api_id': fields.StringField(nullable=True)
    }

    @staticmethod
    def _from_db_object(response, db_response):
        """Converts a database entity to a formal object."""
        for field in response.fields:
            if field != 'response':
                response[field] = db_response[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from response to response_id.
        # The response_id must be populated first in the loop before it can be
        # used to find the response.
        response.obj_reset_changes()
        return response

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [Response._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, response_id):
        """Find a response based on its id or uuid and return a Response object.

        :param response_id: the id *or* uuid of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(response_id):
            return cls.get_by_id(context, response_id)
        elif utils.is_uuid_like(response_id):
            return cls.get_by_uuid(context, response_id)
        else:
            raise exception.InvalidIdentity(identity=response_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, response_id):
        """Find a response based on its integer id and return a Function object.

        :param response_id: the id of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_id(context, response_id)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a response based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_uuid(context, uuid)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a response based on name and return a Response object.

        :param name: the logical name of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_name(context, name)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def get_by_id(cls, context, response_id):
        """Find a response based on its integer id and return a Response object.

        :param response_id: the id of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_id(context, response_id)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a response based on uuid and return a :class:`Response` object.

        :param uuid: the uuid of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_uuid(context, uuid)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a response based on name and return a Response object.

        :param name: the logical name of a response.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_response = cls.dbapi.get_response_by_name(context, name)
        response = Response._from_db_object(cls(context), db_response)
        return response

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of Response objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_responses = cls.dbapi.get_response_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return Response._from_db_object_list(db_responses, cls, context)

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
        db_response = self.dbapi.create_response(values)
        self._from_db_object(self, db_response)