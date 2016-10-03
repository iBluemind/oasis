#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""API for interfacing with Oasis Backend."""
from oslo_config import cfg
from oasis.common import rpc_service


class API(rpc_service.API):
    def __init__(self, transport=None, topic=None, context=None):
        self.context = context
        if topic is None:
            cfg.CONF.import_opt('topic', 'oasis.conductor.config',
                                group='conductor')
        super(API, self).__init__(transport, topic=cfg.CONF.conductor.topic)

    def nodepool_create(self, nodepool, nodepool_create_timeout):
        return self._call('nodepool_create', nodepool=nodepool,
                          nodepool_create_timeout=nodepool_create_timeout,
                          context=self.context)

    def nodepool_delete(self, nodepool_id):
        return self._call('nodepool_delete', nodepool_id=nodepool_id,
                          context=self.context)

    def nodepool_update(self, nodepool_id):
        return self._call('nodepool_update', nodepool_id=nodepool_id,
                          context=self.context)


class ListenerAPI(rpc_service.API):
    def __init__(self, context=None, topic=None, server=None, timeout=None):
        self.context = context
        super(ListenerAPI, self).__init__(topic=topic, server=server, timeout=timeout)

    def ping_conductor(self):
        return self._call('ping_conductor', context=self.context)
