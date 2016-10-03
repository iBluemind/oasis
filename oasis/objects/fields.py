#    Copyright 2015 Intel Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_versionedobjects import fields


class NodePoolStatus(fields.Enum):
    CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
    CREATE_FAILED = 'CREATE_FAILED'
    CREATE_COMPLETE = 'CREATE_COMPLETE'
    UPDATE_IN_PROGRESS = 'UPDATE_IN_PROGRESS'
    UPDATE_FAILED = 'UPDATE_FAILED'
    UPDATE_COMPLETE = 'UPDATE_COMPLETE'
    DELETE_IN_PROGRESS = 'DELETE_IN_PROGRESS'
    DELETE_FAILED = 'DELETE_FAILED'
    DELETE_COMPLETE = 'DELETE_COMPLETE'
    RESUME_COMPLETE = 'RESUME_COMPLETE'
    RESTORE_COMPLETE = 'RESTORE_COMPLETE'
    ROLLBACK_COMPLETE = 'ROLLBACK_COMPLETE'
    SNAPSHOT_COMPLETE = 'SNAPSHOT_COMPLETE'
    CHECK_COMPLETE = 'CHECK_COMPLETE'
    ADOPT_COMPLETE = 'ADOPT_COMPLETE'

    ALL = (CREATE_IN_PROGRESS, CREATE_FAILED, CREATE_COMPLETE,
           UPDATE_IN_PROGRESS, UPDATE_FAILED, UPDATE_COMPLETE,
           DELETE_IN_PROGRESS, DELETE_FAILED, DELETE_COMPLETE,
           RESUME_COMPLETE, RESTORE_COMPLETE, ROLLBACK_COMPLETE,
           SNAPSHOT_COMPLETE, CHECK_COMPLETE, ADOPT_COMPLETE)

    def __init__(self):
        super(NodePoolStatus, self).__init__(valid_values=NodePoolStatus.ALL)


class FunctionStatus(fields.Enum):
    ALL = (
        ERROR, RUNNING, STOPPED, PAUSED, UNKNOWN,
    ) = (
        'Error', 'Running', 'Stopped', 'Paused', 'Unknown',
    )

    def __init__(self):
        super(FunctionStatus, self).__init__(
            valid_values=FunctionStatus.ALL)


class ListOfDictsField(fields.AutoTypedField):
    AUTO_TYPE = fields.List(fields.Dict(fields.FieldType()))


class NodePoolStatusField(fields.BaseEnumField):
    AUTO_TYPE = NodePoolStatus()

