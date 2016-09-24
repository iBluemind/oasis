# Copyright 2015 - Yahoo! Inc.
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

"""Oasis Service Layer"""

from oslo_log import log
from oslo_service import periodic_task

from Oasis import objects
from Oasis.service import periodic


LOG = log.getLogger(__name__)


class OasisServicePeriodicTasks(periodic_task.PeriodicTasks):
    '''Oasis periodic Task class

    Any periodic task job need to be added into this class
    '''

    def __init__(self, conf, binary):
        self.magnum_service_ref = None
        self.host = conf.host
        self.binary = binary
        super(OasisServicePeriodicTasks, self).__init__(conf)

    # periodtask
    # ...


def setup(conf, binary, tg):
    pt = OasisServicePeriodicTasks(conf, binary)
    tg.add_dynamic_timer(
        pt.run_periodic_tasks,
        periodic_interval_max=conf.periodic_interval_max,
        context=None)
