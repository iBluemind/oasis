from oasis.common import rpc_service

from oslo_config import cfg
from oasis.common import context

class AgentAPI(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):

        if topic is None:
            cfg.CONF.import_opt('topic', 'oasis.agent.config',
                                group='agent')
        super(AgentAPI, self).__init__(transport, context,
                                  topic=cfg.CONF.agent.topic)

    # Function Operations
    def function_create(self, function):
        return self._call('function_create', function=function)

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


headers = {}
user_name = headers.get('X-User-Name')
user_id = headers.get('X-User-Id')
project = headers.get('X-Project-Name')
project_id = headers.get('X-Project-Id')
domain_id = headers.get('X-User-Domain-Id')
domain_name = headers.get('X-User-Domain-Name')
auth_token = headers.get('X-Auth-Token')
roles = headers.get('X-Roles', '').split(',')
auth_token_info = None

auth_url = None

# auth_url = CONF.keystone_authtoken.auth_uri

context = context.make_context(
    auth_token=auth_token,
    auth_url=auth_url,
    auth_token_info=auth_token_info,
    user_name=user_name,
    user_id=user_id,
    project_name=project,
    project_id=project_id,
    domain_id=domain_id,
    domain_name=domain_name,
    roles=roles)
api = AgentAPI(context=context)
