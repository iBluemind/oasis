from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base

from oslo_versionedobjects import fields


@base.OasisObjectRegistry.register
class HttpApi(base.OasisPersistentObject, base.OasisObject, base.OasisObjectDictCompat):

    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'method': fields.StringField(nullable=True),
        'endpoint_id': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(httpapi, db_httpapi):
        """Converts a database entity to a formal object."""
        for field in httpapi.fields:
            if field != 'httpapi':
                httpapi[field] = db_httpapi[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from httpapi to httpapi_id.
        # The httpapi_id must be populated first in the loop before it can be
        # used to find the httpapi.
        httpapi.obj_reset_changes()
        return httpapi

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [HttpApi._from_db_object(cls(context), obj) for obj in db_objects]
    
    @base.remotable_classmethod
    def get(cls, context, httpapi_id):
        """Find a httpapi based on its id or uuid and return a HttpApi object.

        :param httpapi_id: the id *or* uuid of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        if utils.is_int_like(httpapi_id):
            return cls.get_by_id(context, httpapi_id)
        elif utils.is_uuid_like(httpapi_id):
            return cls.get_by_uuid(context, httpapi_id)
        else:
            raise exception.InvalidIdentity(identity=httpapi_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, httpapi_id):
        """Find a httpapi based on its integer id and return a Function object.

        :param httpapi_id: the id of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_id(context, httpapi_id)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a httpapi based on uuid and return a :class:`Function` object.

        :param uuid: the uuid of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_uuid(context, uuid)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a httpapi based on name and return a HttpApi object.

        :param name: the logical name of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_name(context, name)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def get_by_id(cls, context, httpapi_id):
        """Find a httpapi based on its integer id and return a HttpApi object.

        :param httpapi_id: the id of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_id(context, httpapi_id)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a httpapi based on uuid and return a :class:`HttpApi` object.

        :param uuid: the uuid of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_uuid(context, uuid)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a httpapi based on name and return a HttpApi object.

        :param name: the logical name of a httpapi.
        :param context: Security context
        :returns: a :class:`Function` object.
        """
        db_httpapi = cls.dbapi.get_httpapi_by_name(context, name)
        httpapi = HttpApi._from_db_object(cls(context), db_httpapi)
        return httpapi

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of HttpApi objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".

        """

        db_httpapis = cls.dbapi.get_httpapi_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return HttpApi._from_db_object_list(db_httpapis, cls, context)

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
        db_httpapi = self.dbapi.create_httpapi(values)
        self._from_db_object(self, db_httpapi)