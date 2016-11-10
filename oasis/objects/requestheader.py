from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

import pecan

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class RequestHeader(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'name': fields.StringField(nullable=True),
        'value': fields.StringField(nullable=True),
        'request_id': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(requestheader, db_requestheader):
        """Converts a database entity to a formal object."""
        for field in requestheader.fields:
            if field != 'requestheader':
                requestheader[field] = db_requestheader[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from requestheader to requestheader_id.
        # The requestheader_id must be populated first in the loop before it can be
        # used to find the requestheader.
        requestheader.obj_reset_changes()
        return requestheader

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [RequestHeader._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, requestheader_id):
        """Find a requestheader based on its id or uuid and return a RequestHeader object.

        :param requestheader_id: the id *or* uuid of a requestheader.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(requestheader_id):
            return cls.get_by_id(context, requestheader_id)
        elif utils.is_uuid_like(requestheader_id):
            return cls.get_by_uuid(context, requestheader_id)
        else:
            raise exception.InvalidIdentity(identity=requestheader_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, requestheader_id):
        """Find a requestheader based on its integer id and return a RequestHeader object.

        :param requestheader_id: the id of a requestheader.
        :param context: Security context
        :returns: a :class:`Function` object.
        """

        db_requestheader = cls.dbapi.get_request_header_by_id(context, requestheader_id)
        if pecan.request.method == 'GET':
            return RequestHeader._from_db_object_list(requestheader_id, cls, context)
        else:
            requestheader = RequestHeader._from_db_object(cls(context), db_requestheader)
            return requestheader

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a requestheader based on uuid and return a :class:`RequestHeader` object.

        :param uuid: the uuid of a requestheader.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_requestheader = cls.dbapi.get_requestheader_by_uuid(context, uuid)
        requestheader = RequestHeader._from_db_object(cls(context), db_requestheader)
        return requestheader

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a requestheader based on name and return a RequestHeader object.

        :param name: the logical name of a requestheader.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_requestheader = cls.dbapi.get_requestheader_by_name(context, name)
        requestheader = RequestHeader._from_db_object(cls(context), db_requestheader)
        return requestheader

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of RequestHeader objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_requestheaders = cls.dbapi.get_request_header_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return RequestHeader._from_db_object_list(db_requestheaders, cls, context)

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
        db_requestheader = self.dbapi.create_request_header(values)
        self._from_db_object(self, db_requestheader)

    @base.remotable
    def destroy(self, context=None):
        """Delete the NodePool from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: NodePool(context)
        """
        self.dbapi.destroy_request_header(self.id)
        self.obj_reset_changes()
