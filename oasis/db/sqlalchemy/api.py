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

import pecan

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
    if utils.is_uuid_like(value):
        return query.filter_by(id=value)
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
        possible_filters = ["name", "project_id", "user_id", "desc", "body", "endpoint_id", "nodepool_id"]
        filter_names = set(filters).intersection(possible_filters)
        filter_dict = {filter_name: filters[filter_name]
                       for filter_name in filter_names}

        query = query.filter_by(**filter_dict)

        # if 'status' in filters:
        #     query = query.filter(models.Function.status.in_(filters['status']))

        return query

################# EndPoint APIs ##################
    def get_endpoint_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.Endpoint)
        query = self._add_tenant_filters(context, query)
        # query = self._add_funtions_filters(query, filters)
        return _paginate_query(models.Endpoint, limit, marker,
                               sort_key, sort_dir, query)

    def create_endpoint(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        endpoint = models.Endpoint()
        endpoint.update(values)
        try:
            endpoint.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return endpoint

    def get_endpoint_by_id(self, context, endpoint_id):
        query = model_query(models.Endpoint)
        # query = self._add_tenant_filters(context, query)
        query = query.filter_by(id=endpoint_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.EndpointNotFound(endpoint=endpoint_id)

    def get_endpoint_by_name(self, context, endpoint_name):
        query = model_query(models.Endpoint)
        # query = self._add_tenant_filters(context, query)
        query = query.filter_by(name=endpoint_name)
        try:
            return query.one()
        except MultipleResultsFound:
            raise exception.Conflict('Multiple endpoints exist with same name.'
                                     ' Please use the endpoint uuid instead.')
        except NoResultFound:
            raise exception.EndpointNotFound(function=endpoint_name)

    def get_nodepool_policy_by_name(self, context, policy_name):
        query = model_query(models.NodePoolPolicy)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(name=policy_name)
        try:
            return query.one()
        except MultipleResultsFound:
            raise exception.Conflict('Multiple policy exist with same name.'
                                     ' Please use the endpoint uuid instead.')
        except NoResultFound:
            raise exception.NodePoolPolicyNotFound(function=policy_name)

############## HttpApis APIs #############
    def _add_httpapis_filters(self, query, filters):
        if filters is None:
            filters = {}
        query = query.filter_by(**{'endpoint_id': filters['endpoint_id']})

        return query

    def get_httpapi_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.HttpApi)
        query = self._add_httpapis_filters(query, filters)
        return _paginate_query(models.HttpApi, limit, marker,
                               sort_key, sort_dir, query)

    def get_httpapi_by_id(self, context, endpoint_id):
        query = model_query(models.HttpApi)

        try:
            if pecan.request.method == 'GET':
                query = query.filter_by(endpoint_id=endpoint_id)
                return query.all()
            elif pecan.request.method == 'DELETE':
                query = query.filter_by(id=endpoint_id)
                return query.one()
        except MultipleResultsFound:
            raise exception.HttpApiAlreadyExists(httpapi=endpoint_id)
        except NoResultFound:
            raise exception.HttpApiNotFound(httpapi=endpoint_id)

    def destroy_httpapi(self, httpapi_id):

        session = get_session()
        with session.begin():
            query = model_query(models.HttpApi, session=session)
            query = add_identity_filter(query, httpapi_id)
            query.delete()

    def create_httpapi(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        httpapi = models.HttpApi()
        httpapi.update(values)
        try:
            httpapi.save()
        except db_exc.DBDuplicateEntry:
            raise exception.HttpApiAlreadyExists(uuid=values['uuid'])
        return httpapi

##############Request APIs #############
    def create_request(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        request = models.Request()
        request.update(values)
        try:
            request.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return request

    def get_request_by_id(self, context, httpapi_id):
        query = model_query(models.Request)
        try:
            if pecan.request.method == 'DELETE':
                query = query.filter_by(id=httpapi_id)

                return query.one()
            else:
                query = query.filter_by(http_api_id=httpapi_id)
                return query.one()
        except MultipleResultsFound:
            raise exception.HttpApiAlreadyExists(http_api_id=httpapi_id)
        except NoResultFound:
            raise exception.HttpApiNotFound(http_api_id=httpapi_id)

################ Request Header APIs ###############
    def _add_request_header_filters(self, query, filters):
        if filters is None:
            filters = {}
        query = query.filter_by(**{'request_id': filters['request_id']})

        return query

    def create_request_header(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        request_header = models.RequestHeader()
        request_header.update(values)
        try:
            request_header.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return request_header

    def get_request_header_by_id(self, context, request_id):
        """Return a httpapi."""
        query = model_query(models.RequestHeader)

        try:
            if pecan.request.method == 'GET':
                print 'ddddddd'
                print request_id
                print 'ddddddd'
                query = query.filter_by(request_id=request_id)
                return query.all()
            elif pecan.request.method == 'DELETE':
                query = query.filter_by(id=request_id)
                return query.one()
        except MultipleResultsFound:
            raise exception.HttpApiAlreadyExists(request_id=request_id)
        except NoResultFound:
            raise exception.HttpApiNotFound(request_id=request_id)

    def destroy_request_header(self, header_id):
        """Delete request_header"""

        session = get_session()
        with session.begin():
            query = model_query(models.RequestHeader, session=session)
            query = add_identity_filter(query, header_id)
            query.delete()

    def get_request_header_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.RequestHeader)
        query = self._add_request_header_filters(query, filters)
        return _paginate_query(models.RequestHeader, limit, marker,
                               sort_key, sort_dir, query)

    def create_response(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        response = models.Response()
        response.update(values)
        try:
            response.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return response

    def create_response_code(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        response_code = models.ResponseStatusCode()
        response_code.update(values)
        try:
            response_code.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return response_code

    def create_response_message(self, values):
        # ensure defaults are present for new endpoint
        if not values.get('id'):
            values['id'] = utils.generate_uuid()

        response_message = models.ResponseErrorMessage()
        response_message.update(values)
        try:
            response_message.save()
        except db_exc.DBDuplicateEntry:
            raise exception.EndpointAlreadyExists(uuid=values['uuid'])
        return response_message

    def get_response_message_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.ResponseErrorMessage)
        return _paginate_query(models.ResponseErrorMessage, limit, marker,
                               sort_key, sort_dir, query)

    def get_response_code_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.ResponseStatusCode)
        return _paginate_query(models.ResponseStatusCode, limit, marker,
                               sort_key, sort_dir, query)

    def get_function_list(self, context, filters=None, limit=None, marker=None,
                     sort_key=None, sort_dir=None):
        query = model_query(models.Function)
        # query = self._add_tenant_filters(context, query)
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
        # query = self._add_tenant_filters(context, query)
        query = query.filter_by(id=function_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.FunctionNotFound(function=function_id)

    def get_function_by_name(self, context, function_name):
        query = model_query(models.Function)
        # query = self._add_tenant_filters(context, query)
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
        # query = self._add_tenant_filters(context, query)
        query = query.filter_by(uuid=function_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.FunctionNotFound(function=function_uuid)

    def destroy_function(self, function_id):
        def destroy_function_resources(session, function_id):
            """Checks whether the function does not have resources."""
            # query = model_query(models.Function, session=session)
            # query = self._add_funtions_filters(query, {'id': function_id})
            # if query.count() != 0:
            #     query.delete()

        session = get_session()
        with session.begin():
            query = model_query(models.Function, session=session)
            query = add_identity_filter(query, function_id)

            try:
                function_ref = query.one()
            except NoResultFound:
                raise exception.FunctionNotFound(function=function_id)

            destroy_function_resources(session, function_ref['id'])
            query.delete()

    def update_function(self, function_id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'id' in values:
            msg = _("Cannot overwrite ID for an existing Function.")
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

            if 'state' in values:
                values['updated_at'] = timeutils.utcnow()

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
        query = self._add_tenant_filters(context, query)
        query = self._add_nodepool_policy_filters(query, filters)
        return _paginate_query(models.NodePoolPolicy, limit, marker,
                               sort_key, sort_dir, query)

    def get_nodepool_policy_by_id(self, context, nodepool_policy_id):
        query = model_query(models.NodePoolPolicy)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(id=nodepool_policy_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.NodePoolPolicyNotFound(nodepool_policy=nodepool_policy_id)

    def get_nodepool_policy_by_name(self, context, policy_name):
        query = model_query(models.NodePoolPolicy)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(name=policy_name)
        try:
            return query.one()
        except MultipleResultsFound:
            raise exception.Conflict('Multiple policy exist with same name.'
                                     ' Please use the endpoint uuid instead.')
        except NoResultFound:
            raise exception.NodePoolPolicyNotFound(function=policy_name)

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

    def _do_update_nodepool_policy(self, nodepool_policy_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.NodePoolPolicy, session=session)
            query = add_identity_filter(query, nodepool_policy_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.NodePoolPolicyNotFound(function=nodepool_policy_id)

            values['updated_at'] = timeutils.utcnow()

            ref.update(values)
        return ref

    def update_nodepool_policy(self, id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'id' in values:
            msg = _("Cannot overwrite ID for an existing Policy.")
            raise exception.InvalidParameterValue(err=msg)

        return self._do_update_nodepool_policy(id, values)

    def destroy_nodepool_policy(self, id):
        # def destroy_function_resources(session, function_id):
        #     """Checks whether the function does not have resources."""
            # query = model_query(models.Function, session=session)
            # query = self._add_funtions_filters(query, {'id': function_id})
            # if query.count() != 0:
            #     query.delete()

        session = get_session()
        with session.begin():
            query = model_query(models.NodePoolPolicy, session=session)
            query = add_identity_filter(query, id)

            try:
                function_ref = query.one()
            except NoResultFound:
                raise exception.NodePoolPolicyNotFound(nodepool_policy=id)

            # destroy_function_resources(session, function_ref['id'])
            query.delete()

    def _add_nodepool_filters(self, query, filters):
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

    def get_nodepool_list(self, context, filters=None, limit=None, marker=None,
                     sort_key=None, sort_dir=None):
        query = model_query(models.NodePool)
        query = self._add_tenant_filters(context, query)
        # query = self._add_nodepool_filters(query, filters)
        return _paginate_query(models.NodePool, limit, marker,
                               sort_key, sort_dir, query)

    def get_nodepool_by_id(self, context, nodepool_id):
        query = model_query(models.NodePool)
        query = self._add_tenant_filters(context, query)
        query = query.filter_by(id=nodepool_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.NodePoolNotFound(nodepool=nodepool_id)

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

    def destroy_nodepool(self, id):
        # def destroy_function_resources(session, id):
        #     """Checks whether the function does not have resources."""
            # query = model_query(models.Function, session=session)
            # query = self._add_funtions_filters(query, {'id': function_id})
            # if query.count() != 0:
            #     query.delete()

        session = get_session()
        with session.begin():
            query = model_query(models.NodePool, session=session)
            query = add_identity_filter(query, id)

            try:
                function_ref = query.one()
            except NoResultFound:
                raise exception.FunctionNotFound(function=id)

            # destroy_function_resources(session, function_ref['id'])
            query.delete()

    def update_nodepool(self, id, values):
        # NOTE(dtantsur): this can lead to very strange errors
        if 'id' in values:
            msg = _("Cannot overwrite ID for an existing Function.")
            raise exception.InvalidParameterValue(err=msg)

        return self._do_update_nodepool(id, values)

    def _do_update_nodepool(self, nodepool_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.NodePool, session=session)
            query = add_identity_filter(query, nodepool_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.NodePoolNotFound(function=nodepool_id)

            values['updated_at'] = timeutils.utcnow()

            ref.update(values)
        return ref

    def destory_nodepool(self, id):
        def destroy_function_resources(session, id):
            """Checks whether the function does not have resources."""
            # query = model_query(models.Function, session=session)
            # query = self._add_funtions_filters(query, {'id': function_id})
            # if query.count() != 0:
            #     query.delete()

        session = get_session()
        with session.begin():
            query = model_query(models.NodePool, session=session)
            query = add_identity_filter(query, id)

            try:
                function_ref = query.one()
            except NoResultFound:
                raise exception.NodePoolNotFound(function=id)

            # destroy_function_resources(session, function_ref['id'])
            query.delete()
