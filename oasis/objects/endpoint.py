from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class Endpoint(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'project_id': fields.StringField(nullable=True),
        'user_id': fields.StringField(nullable=True),
        'name': fields.StringField(nullable=True),
        'url': fields.StringField(nullable=True),
        'desc': fields.StringField(nullable=True)
    }

    @staticmethod
    def _from_db_object(endpoint, db_endpoint):
        """Converts a database entity to a formal object."""
        for field in endpoint.fields:
            if field != 'endpoint':
                endpoint[field] = db_endpoint[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from endpoint to endpoint_id.
        # The endpoint_id must be populated first in the loop before it can be
        # used to find the endpoint.
        endpoint.obj_reset_changes()
        return endpoint

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [Endpoint._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, endpoint_id):
        """Find a endpoint based on its id or uuid and return a Endpoint object.

        :param endpoint_id: the id *or* uuid of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(endpoint_id):
            return cls.get_by_id(context, endpoint_id)
        elif utils.is_uuid_like(endpoint_id):
            return cls.get_by_uuid(context, endpoint_id)
        else:
            raise exception.InvalidIdentity(identity=endpoint_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, endpoint_id):
        """Find a endpoint based on its integer id and return a Function object.

        :param endpoint_id: the id of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_id(context, endpoint_id)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a endpoint based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_uuid(context, uuid)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a endpoint based on name and return a Endpoint object.

        :param name: the logical name of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_name(context, name)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def get_by_id(cls, context, endpoint_id):
        """Find a endpoint based on its integer id and return a Endpoint object.

        :param endpoint_id: the id of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_id(context, endpoint_id)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a endpoint based on uuid and return a :class:`Endpoint` object.

        :param uuid: the uuid of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_uuid(context, uuid)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a endpoint based on name and return a Endpoint object.

        :param name: the logical name of a endpoint.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_endpoint = cls.dbapi.get_endpoint_by_name(context, name)
        endpoint = Endpoint._from_db_object(cls(context), db_endpoint)
        return endpoint

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of Endpoint objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_endpoints = cls.dbapi.get_endpoint_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return Endpoint._from_db_object_list(db_endpoints, cls, context)

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
        db_endpoint = self.dbapi.create_endpoint(values)
        self._from_db_object(self, db_endpoint)