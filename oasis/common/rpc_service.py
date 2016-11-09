# Copyright 2014 - Rackspace Hosting
#
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

"""Common RPC service and API tools for Oasis."""

import eventlet
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_service import service

from oasis.common import rpc
from oasis.objects import base as objects_base
# from oasis.service import periodic
# from oasis.servicegroup import oasis_service_periodic as servicegroup


# NOTE(paulczar):
# Ubuntu 14.04 forces librabbitmq when kombu is used
# Unfortunately it forces a version that has a crash
# bug.  Calling eventlet.monkey_patch() tells kombu
# to use libamqp instead.
eventlet.monkey_patch()

# NOTE(asalkeld):
# The oasis.openstack.common.rpc entries are for compatibility
# with devstack rpc_backend configuration values.
TRANSPORT_ALIASES = {
    'oasis.openstack.common.rpc.impl_kombu': 'rabbit',
    'oasis.openstack.common.rpc.impl_qpid': 'qpid',
    'oasis.openstack.common.rpc.impl_zmq': 'zmq',
}

# periodic_opts = [
#     cfg.BoolOpt('periodic_enable',
#                 default=True,
#                 help='Enable periodic tasks.'),
#     cfg.IntOpt('periodic_interval_max',
#                default=60,
#                help='Max interval size between periodic tasks execution in '
#                     'seconds.'),
# ]
#
# CONF = cfg.CONF
# CONF.register_opts(periodic_opts)


class Service(service.Service):

    def __init__(self, topic, server, handlers, binary):
        super(Service, self).__init__()
        serializer = rpc.RequestContextSerializer(
            objects_base.OasisObjectSerializer())
        transport = messaging.get_transport(cfg.CONF,
                                            aliases=TRANSPORT_ALIASES)
        # TODO(asalkeld) add support for version='x.y'
        target = messaging.Target(topic=topic, server=server)
        self._server = messaging.get_rpc_server(transport, target, handlers,
                                                serializer=serializer)
        self.binary = binary

    def start(self):
        # NOTE(suro-patz): The parent class has created a threadgroup, already
        # if CONF.periodic_enable:
        #     periodic.setup(CONF, self.tg)
        # servicegroup.setup(CONF, self.binary, self.tg)
        self._server.start()

    def stop(self):
        if self._server:
            self._server.stop()
            self._server.wait()
        super(Service, self).stop()

    @classmethod
    def create(cls, topic, server, handlers, binary):
        service_obj = cls(topic, server, handlers, binary)
        return service_obj


class API(object):
    def __init__(self, transport=None, topic=None, server=None,
                 timeout=None):
        self.transport = transport
        self.topic = topic
        self.server = server
        self.timeout = timeout

        self.serializer = rpc.RequestContextSerializer(
            objects_base.OasisObjectSerializer())
        if self.transport is None:
            exmods = rpc.get_allowed_exmods()
            self.transport = messaging.get_transport(cfg.CONF,
                                                allowed_remote_exmods=exmods,
                                                aliases=TRANSPORT_ALIASES)
        if self.topic is None:
            self.topic = ''
        target = messaging.Target(topic=self.topic, server=self.server)
        self._client = messaging.RPCClient(self.transport, target,
                                           serializer=self.serializer,
                                           timeout=self.timeout)

    def _call(self, method, context, *args, **kwargs):
        return self._client.call(context, method, *args, **kwargs)

    def _cast(self, method, context, *args, **kwargs):
        self._client.cast(context, method, *args, **kwargs)

    def change_client(self, topic):
        target = messaging.Target(topic=topic, server=self.server)
        self._client = messaging.RPCClient(self.transport, target,
                                           serializer=self.serializer,
                                           timeout=self.timeout)

    def echo(self, message):
        self._cast('echo', message=message)

