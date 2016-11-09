from oasis.common import rpc_service

from oslo_config import cfg


class AgentAPI(rpc_service.API):
    def __init__(self, transport=None, topic=None, context=None):
        self.context = context
        if topic is None:
            cfg.CONF.import_opt('topic', 'oasis.agent.config',
                                group='agent')
        super(AgentAPI, self).__init__(transport,
                                  topic=cfg.CONF.agent.topic)

    # Function Operations
    def function_create(self, function_id, rule, body, methods):
        return self._call('function_create',
                          function_id=function_id, rule=rule, body=body, methods=methods, context=self.context)

    def function_update(self, function_id, rule, body, methods):
        return self._call('function_update',
                          function_id=function_id, rule=rule, body=body, methods=methods, context=self.context)

    def function_delete(self, function_id):
        return self._call('function_delete', function_id=function_id, context=self.context)


class ListenerAPI(rpc_service.API):
    def __init__(self, context=None, topic=None, server=None, timeout=None):
        self.context = context
        super(ListenerAPI, self).__init__(topic=topic, server=server, timeout=timeout)

    def ping_conductor(self):
        return self._call('ping_conductor', context=self.context)


