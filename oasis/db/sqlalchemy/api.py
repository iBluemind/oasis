# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""SQLAlchemy storage backend."""

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_utils import timeutils
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from oasis.common import exception
from oasis.common import utils
from oasis.db import api
from oasis.db.sqlalchemy import models
from oasis.i18n import _

CONF = cfg.CONF


_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade.from_config(CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.

    :param session: if present, the session to use
    """

    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


def add_identity_filter(query, value):
    """Adds an identity filter to a query.

    Filters results by ID, if supplied value is a valid integer.
    Otherwise attempts to filter results by UUID.

    :param query: Initial query to add filter to.
    :param value: Value for filtering results by.
    :return: Modified query.
    """
    if utils.is_int_like(value):
        return query.filter_by(id=value)
    elif utils.is_uuid_like(value):
        return query.filter_by(uuid=value)
    else:
        raise exception.InvalidIdentity(identity=value)


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None):
    if not query:
        query = model_query(model)
    sort_keys = ['id']
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    try:
        query = db_utils.paginate_query(query, model, limit, sort_keys,
                                        marker=marker, sort_dir=sort_dir)
    except db_exc.InvalidSortKey:
        raise exception.InvalidParameterValue(
            _('The sort_key value "%(key)s" is an invalid field for sorting')
            % {'key': sort_key})
    return query.all()


class Connection(api.Connection):
    """SqlAlchemy connection."""

    def __init__(self):
        pass

    def _add_tenant_filters(self, context, query):
        if context.is_admin and context.all_tenants:
            return query

        if context.project_id:
            query = query.filter_by(project_id=context.project_id)
        else:
            query = query.filter_by(user_id=context.user_id)

        return query

    def _add_funtions_filters(self, query, filters):
        if filters is None:
            filters = {}

        # possible_filters = ["name", "node_count",
        #                     "master_count", "stack_id", "api_address",
        #                     "node_addresses", "project_id", "user_id"]
        possible_filters = ["name", "project_id", "user_id"]
        filter_names = set(filters).intersection(possible_filters)
        filter_dict = {filter_name: filters[filter_name]
                       for filter_name in filter_names}

        query = query.filter_by(**filter_dict)

        if 'status' in filters:
            query = query.filter(models.Function.status.in_(filters['status']))

        return query

    def get_function_list(self, context, filters=None, limit=None, marker=None,
                     sort_key=None, sort_dir=None):
        query = model_query(models.Function)
        query = self._add_tenant_filters(context, query)
        query = self._add_funtions_filters(query, filters)
        return _paginate_query(models.Function, limit, marker,
                               sort_key, sort_dir, query)

    def create_function(self, values):
        # ensure defaults are present for new funtions
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        function = models.Function()
        function.update(values)
        try:
            function.save()
        except db_exc.DBDuplicateEntry:
            raise exception.FunctionAlreadyExists(uuid=values['uuid'])
        return function

    def get_function_by_id(self, context, function_id):
        query = model_query(models.Function)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(id=function_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.FunctionNotFound(function=function_id)

    def get_function_by_name(self, context, function_name):
        query = model_query(models.Function)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(name=function_name)
        try:
            return query.one()
        except MultipleResultsFound:
            raise exception.Conflict('Multiple funtions exist with same name.'
                                     ' Please use the function uuid instead.')
        except NoResultFound:
            raise exception.FunctionNotFound(function=function_name)

    def get_function_by_uuid(self, context, function_uuid):
        query = model_query(models.Function)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(uuid=function_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.FunctionNotFound(function=function_uuid)

    def destroy_function(self, function_id):
        def destroy_function_resources(session, function_uuid):
            """Checks whether the function does not have resources."""
            query = model_query(models.Pod, session=session)
            query = self._add_pods_filters(query, {'function_uuid': function_uuid})
            if query.count() != 0:
                query.delete()

            query = model_query(models.Service, session=session)
            query = self._add_services_filters(query, {'function_uuid': function_uuid})
            if query.count() != 0:
                query.delete()

            query = model_query(models.ReplicationController, session=session)
            query = self._add_rcs_filters(query, {'function_uuid': function_uuid})
            if query.count() != 0:
                query.delete()

            query = model_query(models.Container, session=session)
            query = self._add_containers_filters(query, {'function_uuid': function_uuid})
            if query.count() != 0:
                query.delete()

        session = get_session()
        with session.begin():
            query = model_query(models.Function, session=session)
            query = add_identity_filter(query, function_id)

            try:
                function_ref = query.one()
            except NoResultFound:
                raise exception.FunctionNotFound(function=function_id)

            destroy_function_resources(session, function_ref['uuid'])
            query.delete()

    def update_function(self, function_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Function.")
            raise exception.InvalidParameterValue(err=msg)

        return self._do_update_function(function_id, values)

    def _do_update_function(self, function_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.Function, session=session)
            query = add_identity_filter(query, function_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.FunctionNotFound(function=function_id)

            if 'provision_state' in values:
                values['provision_updated_at'] = timeutils.utcnow()

            ref.update(values)
        return ref

    def _add_nodepool_policy_filters(self, query, filters):
        if filters is None:
            filters = {}

        possible_filters = ["name", "stack_id", "project_id", "id"]

        filter_names = set(filters).intersection(possible_filters)
        filter_dict = {filter_name: filters[filter_name]
                       for filter_name in filter_names}

        query = query.filter_by(**filter_dict)

        if 'status' in filters:
            query = query.filter(models.Function.status.in_(filters['status']))

        return query

    def get_nodepool_policy_list(self, context, filters=None, limit=None, marker=None,
                     sort_key=None, sort_dir=None):
        query = model_query(models.NodePoolPolicy)
        # query = self._add_tenant_filters(context, query)
        query = self._add_nodepool_policy_filters(query, filters)
        return _paginate_query(models.NodePoolPolicy, limit, marker,
                               sort_key, sort_dir, query)

    def create_nodepool_policy(self, values):
        # ensure defaults are present for new funtions
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        nodepool_policy = models.NodePoolPolicy()
        nodepool_policy.update(values)
        try:
            nodepool_policy.save()
        except db_exc.DBDuplicateEntry:
            raise exception.NodePoolPolicyAlreadyExists(uuid=values['id'])
        return nodepool_policy

    def create_nodepool(self, values):
        # ensure defaults are present for new funtions
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        nodepool = models.NodePool()
        nodepool.update(values)
        try:
            nodepool.save()
        except db_exc.DBDuplicateEntry:
            raise exception.NodePoolAlreadyExists(uuid=values['id'])
        return nodepool