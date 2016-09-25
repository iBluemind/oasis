from oasis.common import rpc_service

from oslo_config import cfg

class API(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            cfg.CONF.import_opt('topic', 'oasis.agent.config',
                                group='agent')
        super(API, self).__init__(transport, context,
                                  topic=cfg.CONF.conductor.topic)

    # Function Operations
    def function_create(self, function):
        return self._call('function_create', function=function)

    # Endpoint Operations
    def endpoint_create(self, function, node_pool):
        pass



class ListenerAPI(rpc_service.API):
    def __init__(self, context=None, topic=None, server=None, timeout=None):
        super(ListenerAPI, self).__init__(context=context, topic=topic,
                                          server=server, timeout=timeout)

    def ping_conductor(self):
        return self._call('ping_conductor')
