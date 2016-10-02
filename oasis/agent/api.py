from oasis.common import rpc_service

from oslo_config import cfg


class AgentAPI(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            cfg.CONF.import_opt('topic', 'oasis.agent.config',
                                group='agent')
        super(AgentAPI, self).__init__(transport, context,
                                  topic=cfg.CONF.agent.topic)

    # Function Operations
    def function_create(self, function):
        # mock data
        function_id='test'
        body='test'
        rule='/'
        return self._call('function_create',
                          function_id=function_id, body=body, rule=rule)

    def function_update(self, function):
        return self._call('function_update', function=function)

    def function_delete(self, function):
        return self._call('function_delete', function=function)

    # Endpoint Operations


class ListenerAPI(rpc_service.API):
    def __init__(self, context=None, topic=None, server=None, timeout=None):
        super(ListenerAPI, self).__init__(context=context, topic=topic,
                                          server=server, timeout=timeout)

    def ping_conductor(self):
        return self._call('ping_conductor')


