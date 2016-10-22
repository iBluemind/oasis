from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class ResponseCode(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'status_code': fields.StringField(nullable=True),
        'response_id': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(responsecode, db_responsecode):
        """Converts a database entity to a formal object."""
        for field in responsecode.fields:
            if field != 'responsecode':
                responsecode[field] = db_responsecode[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from responsecode to responsecode_id.
        # The responsecode_id must be populated first in the loop before it can be
        # used to find the responsecode.
        responsecode.obj_reset_changes()
        return responsecode

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [ResponseCode._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, responsecode_id):
        """Find a responsecode based on its id or uuid and return a ResponseCode object.

        :param responsecode_id: the id *or* uuid of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(responsecode_id):
            return cls.get_by_id(context, responsecode_id)
        elif utils.is_uuid_like(responsecode_id):
            return cls.get_by_uuid(context, responsecode_id)
        else:
            raise exception.InvalidIdentity(identity=responsecode_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, responsecode_id):
        """Find a responsecode based on its integer id and return a Function object.

        :param responsecode_id: the id of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_id(context, responsecode_id)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a responsecode based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_uuid(context, uuid)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a responsecode based on name and return a ResponseCode object.

        :param name: the logical name of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_name(context, name)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def get_by_id(cls, context, responsecode_id):
        """Find a responsecode based on its integer id and return a ResponseCode object.

        :param responsecode_id: the id of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_id(context, responsecode_id)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a responsecode based on uuid and return a :class:`ResponseCode` object.

        :param uuid: the uuid of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_uuid(context, uuid)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a responsecode based on name and return a ResponseCode object.

        :param name: the logical name of a responsecode.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsecode = cls.dbapi.get_responsecode_by_name(context, name)
        responsecode = ResponseCode._from_db_object(cls(context), db_responsecode)
        return responsecode

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of ResponseCode objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_responsecodes = cls.dbapi.get_responsecode_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return ResponseCode._from_db_object_list(db_responsecodes, cls, context)

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
        db_responsecode = self.dbapi.create_response_code(values)
        self._from_db_object(self, db_responsecode)