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

"""
SQLAlchemy models for container service
"""

import json

from oslo_config import cfg
from oslo_utils import uuidutils
from oslo_db.sqlalchemy import models
import six.moves.urllib.parse as urlparse
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy import schema
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator, TEXT
from oasis.common import config


def table_args():
    # config.parse_args(["/etc/oasis/oasis.conf",])
    engine_name = urlparse.urlparse(cfg.CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JsonEncodedType(TypeDecorator):
    """Abstract base type serialized as json-encoded string in db."""
    type = None
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            # Save default value according to current type to keep the
            # interface the consistent.
            value = self.type()
        elif not isinstance(value, self.type):
            raise TypeError("%s supposes to store %s objects, but %s given"
                            % (self.__class__.__name__,
                               self.type.__name__,
                               type(value).__name__))
        serialized_value = json.dumps(value)
        return serialized_value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONEncodedDict(JsonEncodedType):
    """Represents dict serialized as json-encoded string in db."""
    type = dict


class JSONEncodedList(JsonEncodedType):
    """Represents list serialized as json-encoded string in db."""
    type = list


class OasisBase(models.TimestampMixin,
                 models.ModelBase):

    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    def save(self, session=None):
        import oasis.db.sqlalchemy.api as db_api

        if session is None:
            session = db_api.get_session()

        super(OasisBase, self).save(session)

Base = declarative_base(cls=OasisBase)
UUID4 = uuidutils.generate_uuid


class TimestampMixin(object):
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Function(Base, TimestampMixin):
    """Represents a Function."""

    __tablename__ = 'function'
    __table_args__ = (
        table_args()
    )
    id = Column('id', String(36), primary_key=True, default=lambda: UUID4())
    project_id = Column(String(255))
    user_id = Column(String(255))
    stack_id = Column(String(255))
    status = Column(String(20))
    status_reason = Column(Text)
    name = Column(String(255))
    body = Column(Text)
    trust_id = Column(String(255))
    trustee_username = Column(String(255))
    trustee_user_id = Column(String(255))
    trustee_password = Column(String(255))


class Policy(Base, TimestampMixin):
    """Represents a Policy."""

    __tablename__ = 'policy'
    __table_args__ = (
        table_args()
    )
    id = Column('id', String(36), primary_key=True, default=lambda: UUID4())
    project_id = Column(String(255))
    user_id = Column(String(255))
    name = Column(String(255))
    total_vm_count = Column(Integer())
    vm_count_per_user = Column(Integer())


class Node(Base, TimestampMixin):
    """Represents a Node."""

    __tablename__ = 'node'
    __table_args__ = (
        table_args()
    )
    id = Column('id', String(36), primary_key=True, default=lambda: UUID4())
    project_id = Column(String(255))
    user_id = Column(String(255))
    stack_id = Column(String(255))
    name = Column(String(255))
    nodepool_id = Column(String(36))
    status = Column(String(20))
    memory = Column(String(255))


class NodePool(Base, TimestampMixin):
    """Represents a NodePool."""

    __tablename__ = 'nodepool'
    __table_args__ = (
        table_args()
    )
    id = Column('id', String(36), primary_key=True, default=lambda: UUID4())
    project_id = Column(String(255))
    user_id = Column(String(255))
    stack_id = Column(String(255))
    host = Column(String(255))
    name = Column(String(255))
    status = Column(String(255))


class Gateway(Base, TimestampMixin):
    """Represents a Gateway."""

    __tablename__ = 'gateway'
    __table_args__ = (
        table_args()
    )
    id = Column('id', String(36), primary_key=True, default=lambda: UUID4())
    project_id = Column(String(255))
    user_id = Column(String(255))
    stack_id = Column(String(255))
    name = Column(String(255))
    ip = Column(String(36))
    ports = Column(JSONEncodedList)


