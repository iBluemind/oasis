# Copyright (c) 2015 Intel Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools

from oslo_log import log
from oslo_service import periodic_task
import six

from oasis.common import clients
from oasis.common import context
from oasis.common import exception
from oasis.common import rpc
# from oasis.conductor import monitors
from oasis.i18n import _
from oasis.i18n import _LI
from oasis.i18n import _LW
from oasis import objects


LOG = log.getLogger(__name__)


def set_context(func):
    @functools.wraps(func)
    def handler(self, ctx):
        ctx = context.make_admin_context(all_tenants=True)
        context.set_ctx(ctx)
        func(self, ctx)
        context.set_ctx(None)
    return handler


class OasisPeriodicTasks(periodic_task.PeriodicTasks):
    '''Oasis periodic Task class

    Any periodic task job need to be added into this class

    NOTE(suro-patz):
    - oslo_service.periodic_task runs tasks protected within try/catch
      block, with default raise_on_error as 'False', in run_periodic_tasks(),
      which ensures the process does not die, even if a task encounters an
      Exception.
    - The periodic tasks here does not necessarily need another
      try/catch block. The present try/catch block here helps putting
      oasis-periodic-task-specific log/error message.

    '''

    def __init__(self, conf):
        super(OasisPeriodicTasks, self).__init__(conf)
        self.notifier = rpc.get_notifier()

    # periodtask
    # ...


def setup(conf, tg):
    pt = OasisPeriodicTasks(conf)
    tg.add_dynamic_timer(
        pt.run_periodic_tasks,
        periodic_interval_max=conf.periodic_interval_max,
        context=None)
