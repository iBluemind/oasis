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

from oasis.api import hooks

# Pecan Application Configurations
app = {
    'root': 'oasis.api.controllers.root.RootController',
    'modules': ['oasis.api'],
    'debug': False,
    'hooks': [
        hooks.ContextHook(),
        hooks.RPCHook(),
        hooks.NoExceptionTracebackHook(),
    ],
    'acl_public_routes': [
        '/',
        '/v1',
    ],
}

# Custom Configurations must be in Python dictionary format::
#
# foo = {'bar':'baz'}
#
# All configurations are accessible at::
# pecan.conf
