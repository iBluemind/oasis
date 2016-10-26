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

from oasis.common import exception
from oasis.common import utils
from oasis.db import api as dbapi
from oasis.objects import base
from oasis.objects import fields as m_fields


@base.OasisObjectRegistry.register
class NodePoolPolicy(base.OasisPersistentObject, base.OasisObject,
          base.OasisObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(),
        'name': fields.StringField(),
        'min_size': fields.IntegerField(nullable=True),
        'max_size': fields.IntegerField(nullable=True),
        'scaleup_adjust': fields.IntegerField(nullable=True),
        'scaleup_cooldown': fields.IntegerField(nullable=True),
        'scaleup_period': fields.IntegerField(nullable=True),
        'scaleup_evaluation_periods': fields.IntegerField(nullable=True),
        'scaleup_threshold': fields.IntegerField(nullable=True),
        'scaledown_adjust': fields.IntegerField(nullable=True),
        'scaledown_cooldown': fields.IntegerField(nullable=True),
        'scaledown_period': fields.IntegerField(nullable=True),
        'scaledown_evaluation_periods': fields.IntegerField(nullable=True),
        'scaledown_threshold': fields.IntegerField(nullable=True)
    }

    @staticmethod
    def _from_db_object(nodepool_policy, db_nodepool_policy):
        """Converts a database entity to a formal object."""
        for field in nodepool_policy.fields:
            if field != 'nodepool_policy':
                nodepool_policy[field] = db_nodepool_policy[field]

        # Note(eliqiao): The following line needs to be placed outside the
        # loop because there is a dependency from nodepool_policy to nodepool_policy_id.
        # The nodepool_policy_id must be populated first in the loop before it can be
        # used to find the nodepool_policy.
        nodepool_policy.obj_reset_changes()
        return nodepool_policy

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [NodePoolPolicy._from_db_object(cls(context), obj) for obj in db_objects]

    @base.remotable_classmethod
    def get(cls, context, nodepool_policy_id):
        """Find a nodepool_policy based on its id or uuid and return a NodePool object.

        :param nodepool_policy_id: the id *or* uuid of a nodepool_policy.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        if utils.is_int_like(nodepool_policy_id):
            return cls.get_by_id(context, nodepool_policy_id)
        elif utils.is_uuid_like(nodepool_policy_id):
            return cls.get_by_uuid(context, nodepool_policy_id)
        else:
            raise exception.InvalidIdentity(identity=nodepool_policy_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, nodepool_policy_id):
        """Find a nodepool_policy based on its integer id and return a NodePool object.

        :param nodepool_policy_id: the id of a nodepool_policy.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool_policy = cls.dbapi.get_nodepool_policy_by_id(context, nodepool_policy_id)
        nodepool_policy = NodePoolPolicy._from_db_object(cls(context), db_nodepool_policy)
        return nodepool_policy

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a nodepool_policy based on uuid and return a :class:`NodePool` object.

        :param uuid: the uuid of a nodepool_policy.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool_policy = cls.dbapi.get_nodepool_policy_by_uuid(context, uuid)
        nodepool_policy = NodePoolPolicy._from_db_object(cls(context), db_nodepool_policy)
        return nodepool_policy

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a nodepool_policy based on name and return a NodePool object.

        :param name: the logical name of a nodepool_policy.
        :param context: Security context
        :returns: a :class:`NodePool` object.
        """
        db_nodepool_policy = cls.dbapi.get_nodepool_policy_by_name(context, name)
        nodepool_policy = NodePoolPolicy._from_db_object(cls(context), db_nodepool_policy)
        return nodepool_policy

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of NodePool objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: filter dict, can includes 'nodepool_policy_id', 'name',
                        'node_count', 'stack_id', 'api_address',
                        'node_addresses', 'project_id', 'user_id',
                        'status'(should be a status list), 'master_count'.
        :returns: a list of :class:`NodePool` object.

        """
        db_nodepool_policies = cls.dbapi.get_nodepool_policy_list(context, limit=limit,
                                         marker=marker,
                                         sort_key=sort_key,
                                         sort_dir=sort_dir,
                                         filters=filters)
        return NodePoolPolicy._from_db_object_list(db_nodepool_policies, cls, context)

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
        db_nodepool_policy = self.dbapi.create_nodepool_policy(values)
        self._from_db_object(self, db_nodepool_policy)

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
        self.dbapi.destroy_nodepool_policy(self.id)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this NodePoolPolicy.

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
        self.dbapi.update_nodepool_policy(self.id, updates)

        self.obj_reset_changes()

    @base.remotable
    def refresh(self, context=None):
        """Loads updates for this NodePoolPolicy.

        Loads a nodepool_policy with the same uuid from the database and
        checks for updated attributes. Updates are applied from
        the loaded nodepool_policy column by column, if there are any updates.

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
