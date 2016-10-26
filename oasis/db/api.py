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
"""
Base classes for storage engines
"""

import abc

from oslo_config import cfg
from oslo_db import api as db_api
import six


_BACKEND_MAPPING = {'sqlalchemy': 'oasis.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF, backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def get_instance():
    """Return a DB API instance."""
    return IMPL


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    """Base class for storage system connections."""

    @abc.abstractmethod
    def __init__(self):
        """Constructor."""

    @abc.abstractmethod
    def get_endpoint_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        """Get matching endpoints.

        Return a list of the specified columns for all bays that match the
        specified filters.

        :param context: The security context
        :param filters: Filters to apply. Defaults to None.

        :param limit: Maximum number of bays to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        :returns: A list of tuples of the specified columns.
        """

    @abc.abstractmethod
    def create_endpoint(self, values):
        """Create a new endpoint.
        """

    @abc.abstractmethod
    def get_endpoint_by_id(self, context, endpoint_id):
        """Return a endpoint.

        :param context: The security context
        :param endpoint_id: The id of a endpoint.
        :returns: A endpoint.
        """

    @abc.abstractmethod
    def get_endpoint_by_name(self, context, endpoint_id):
        """Return a endpoint.

        :param context: The security context
        :param endpoint_id: The id of a endpoint.
        :returns: A endpoint.
        """

    @abc.abstractmethod
    def create_httpapi(self, values):
        """Create a new httpapi."""

    @abc.abstractmethod
    def get_httpapi_list(self, context):
        """Get matching http apis."""

    @abc.abstractmethod
    def create_request(self, values):
        """Create a new Request."""

    @abc.abstractmethod
    def create_request_header(self, values):
        """Create a new Request Header."""

    @abc.abstractmethod
    def get_request_header_list(self, context):
        """Get matching http apis."""

    @abc.abstractmethod
    def create_response(self, values):
        """Create a new Response."""

    @abc.abstractmethod
    def create_response_code(self, values):
        """Create a new Response Code."""

    @abc.abstractmethod
    def get_response_code_list(self, context):
        """Get matching response codes."""

    @abc.abstractmethod
    def get_response_message_list(self, context):
        """Get matching response messages."""

    @abc.abstractmethod
    def create_response_message(self, values):
        """Create a new Response Message."""

    @abc.abstractmethod
    def get_function_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        """Get matching functions.

        Return a list of the specified columns for all bays that match the
        specified filters.

        :param context: The security context
        :param filters: Filters to apply. Defaults to None.

        :param limit: Maximum number of bays to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        :returns: A list of tuples of the specified columns.
        """

    @abc.abstractmethod
    def create_function(self, values):
        """Create a new function.

        :param values: A dict containing several items used to identify
                       and track the bay, and several dicts which are passed
                       into the Drivers when managing this bay. For example:

                       ::

                        {
                         'uuid': utils.generate_uuid(),
                         'name': 'example',
                         'type': 'virt'
                        }
        :returns: A bay.
        """

    @abc.abstractmethod
    def get_function_by_id(self, context, function_id):
        """Return a function.

        :param context: The security context
        :param function_id: The id of a function.
        :returns: A function.
        """

    @abc.abstractmethod
    def get_function_by_name(self, context, function_name):
        """Return a function.

        :param context: The security context
        :param function_name: The name of a function.
        :returns: A function.
        """

    @abc.abstractmethod
    def destroy_function(self, function_id):
        """Destroy a function and all associated interfaces.

        :param function_id: The id or uuid of a function.
        """

    @abc.abstractmethod
    def update_function(self, function_id, values):
        """Update properties of a bay.

        :param function_id: The id or uuid of a function.
        :returns: A function.
        :raises: BayNotFound
        """

    @abc.abstractmethod
    def create_nodepool_policy(self, values):
        """Create a new nodepool policy."""

    @abc.abstractmethod
    def update_nodepool_policy(self, id, values):
        """Update nodepool policy"""

    @abc.abstractmethod
    def destroy_nodepool_policy(self, id):
        """Delete nodepool policy"""

    @abc.abstractmethod
    def get_nodepool_policy_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        """Get matching Nodepool Policies"""

    @abc.abstractmethod
    def get_nodepool_policy_by_id(self, context, function_id):
        """Return a policy."""

    @abc.abstractmethod
    def get_nodepool_list(self, context, filters=None, limit=None,
                     marker=None, sort_key=None, sort_dir=None):
        """Get matching Nodepools"""

    @abc.abstractmethod
    def get_nodepool_by_id(self, context, function_id):
        """Return a nodepool."""

    @abc.abstractmethod
    def create_nodepool(self, values):
        """Create a new nodepool."""

    @abc.abstractmethod
    def update_nodepool(self, id, values):
        """Update nodepool"""

    @abc.abstractmethod
    def destory_nodepool(self, id):
        """Delete nodepool"""
