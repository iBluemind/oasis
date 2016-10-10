# coding=utf-8
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_versionedobjects import fields
from oasis.objects import fields as m_fields

from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base
from oasis.objects import fields as m_fields


@base.OasisObjectRegistry.register
class NodePool(base.OasisPersistentObject, base.OasisObject,
          base.OasisObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'project_id': fields.StringField(nullable=True),
        'user_id': fields.StringField(nullable=True),
        'stack_id': fields.StringField(nullable=True),
        'function_id': fields.StringField(nullable=True),
        'nodepool_policy_id': fields.StringField(nullable=True),
        'host': fields.StringField(nullable=True),
        'name': fields.StringField(nullable=True),
        'status': m_fields.NodePoolStatusField(nullable=True),
        'status_reason': fields.StringField(nullable=True),
    }

    @staticmethod
    def _from_db_object(nodepool, db_nodepool):
        """Converts a database entity to a formal object."""
        for field in nodepool.fields:
            if field != 'nodepool':
                nodepool[field] = db_nodepool[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from nodepool to nodepool_id.
        # The nodepool_id must be populated first in the loop before it can be
        # used to find the nodepool.
        nodepool.obj_reset_changes()
        return nodepool

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [NodePool._from_db_object(cls(context), obj) for obj in db_objects]

    @base.remotable_classmethod
    def get(cls, context, nodepool_id):
        """Find a nodepool based on its id or uuid and return a NodePool object.

        :param nodepool_id: the id *or* uuid of a nodepool.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        if utils.is_int_like(nodepool_id):
            return cls.get_by_id(context, nodepool_id)
        elif utils.is_uuid_like(nodepool_id):
            return cls.get_by_uuid(context, nodepool_id)
        else:
            raise exception.InvalidIdentity(identity=nodepool_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, nodepool_id):
        """Find a nodepool based on its integer id and return a NodePool object.

        :param nodepool_id: the id of a nodepool.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool = cls.dbapi.get_nodepool_by_id(context, nodepool_id)
        nodepool = NodePool._from_db_object(cls(context), db_nodepool)
        return nodepool

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a nodepool based on uuid and return a :class:`NodePool` object.

        :param uuid: the uuid of a nodepool.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool = cls.dbapi.get_nodepool_by_uuid(context, uuid)
        nodepool = NodePool._from_db_object(cls(context), db_nodepool)
        return nodepool

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a nodepool based on name and return a NodePool object.

        :param name: the logical name of a nodepool.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool = cls.dbapi.get_nodepool_by_name(context, name)
        nodepool = NodePool._from_db_object(cls(context), db_nodepool)
        return nodepool

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of NodePool objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: filter dict, can includes 'nodepool_id', 'name',
                        'node_count', 'stack_id', 'api_address',
                        'node_addresses', 'project_id', 'user_id',
                        'status'(should be a status list), 'master_count'.
        :returns: a list of :class:`NodePool` object.

        """
        db_nodepools = cls.dbapi.get_nodepool_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return NodePool._from_db_object_list(db_nodepools, cls, context)

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
        db_nodepool = self.dbapi.create_nodepool(values)
        self._from_db_object(self, db_nodepool)

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
        self.dbapi.destroy_nodepool(self.uuid)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this NodePool.

        Updates will be made column by column based on the result
        of self.what_changed().

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: NodePool(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_nodepool(self.uuid, updates)

        self.obj_reset_changes()

    @base.remotable
    def refresh(self, context=None):
        """Loads updates for this NodePool.

        Loads a nodepool with the same uuid from the database and
        checks for updated attributes. Updates are applied from
        the loaded nodepool column by column, if there are any updates.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: NodePool(context)
        """
        current = self.__class__.get_by_uuid(self._context, uuid=self.uuid)
        for field in self.fields:
            if self.obj_attr_is_set(field) and self[field] != current[field]:
                self[field] = current[field]
