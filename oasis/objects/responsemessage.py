from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class ResponseMessage(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'message': fields.StringField(nullable=True),
        'response_statuscode_id': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(responsemessage, db_responsemessage):
        """Converts a database entity to a formal object."""
        for field in responsemessage.fields:
            if field != 'responsemessage':
                responsemessage[field] = db_responsemessage[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from responsemessage to responsemessage_id.
        # The responsemessage_id must be populated first in the loop before it can be
        # used to find the responsemessage.
        responsemessage.obj_reset_changes()
        return responsemessage

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [ResponseMessage._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, responsemessage_id):
        """Find a responsemessage based on its id or uuid and return a ResponseMessage object.

        :param responsemessage_id: the id *or* uuid of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(responsemessage_id):
            return cls.get_by_id(context, responsemessage_id)
        elif utils.is_uuid_like(responsemessage_id):
            return cls.get_by_uuid(context, responsemessage_id)
        else:
            raise exception.InvalidIdentity(identity=responsemessage_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, responsemessage_id):
        """Find a responsemessage based on its integer id and return a Function object.

        :param responsemessage_id: the id of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_id(context, responsemessage_id)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a responsemessage based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_uuid(context, uuid)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a responsemessage based on name and return a ResponseMessage object.

        :param name: the logical name of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_name(context, name)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def get_by_id(cls, context, responsemessage_id):
        """Find a responsemessage based on its integer id and return a ResponseMessage object.

        :param responsemessage_id: the id of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_id(context, responsemessage_id)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a responsemessage based on uuid and return a :class:`ResponseMessage` object.

        :param uuid: the uuid of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_uuid(context, uuid)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a responsemessage based on name and return a ResponseMessage object.

        :param name: the logical name of a responsemessage.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_responsemessage = cls.dbapi.get_responsemessage_by_name(context, name)
        responsemessage = ResponseMessage._from_db_object(cls(context), db_responsemessage)
        return responsemessage

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of ResponseMessage objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_responsemessages = cls.dbapi.get_responsemessage_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return ResponseMessage._from_db_object_list(db_responsemessages, cls, context)

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
        db_responsemessage = self.dbapi.create_response_message(values)
        self._from_db_object(self, db_responsemessage)