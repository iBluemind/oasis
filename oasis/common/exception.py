# Copyright 2013 - Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Oasis base exception handling.

Includes decorator for re-raising Oasis-type exceptions.

"""

import functools
import json
import sys

from keystoneclient import exceptions as keystone_exceptions
from oslo_config import cfg
from oslo_log import log as logging
import six

from oasis.i18n import _
from oasis.i18n import _LE


LOG = logging.getLogger(__name__)

CONF = cfg.CONF

try:
    CONF.import_opt('fatal_exception_format_errors',
                    'oslo_versionedobjects.exception')
except cfg.NoSuchOptError as e:
    # Note:work around for magnum run against master branch
    # in devstack gate job, as magnum not branched yet
    # verisonobjects kilo/master different version can
    # cause issue here. As it changed import group. So
    # add here before branch to prevent gate failure.
    # Bug: #1447873
    CONF.import_opt('fatal_exception_format_errors',
                    'oslo_versionedobjects.exception',
                    group='oslo_versionedobjects')


def wrap_keystone_exception(func):
    """Wrap keystone exceptions and throw Oasis specific exceptions."""
    @functools.wraps(func)
    def wrapped(*args, **kw):
        try:
            return func(*args, **kw)
        except keystone_exceptions.AuthorizationFailure:
            raise AuthorizationFailure(
                client=func.__name__, message="reason: %s" % sys.exc_info()[1])
        except keystone_exceptions.ClientException:
            raise AuthorizationFailure(
                client=func.__name__,
                message="unexpected keystone client error occurred: %s"
                        % sys.exc_info()[1])
    return wrapped


class OasisException(Exception):
    """Base Oasis Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs and hasattr(self, 'code'):
            self.kwargs['code'] = self.code

        if message:
            self.message = message

        try:
            self.message = self.message % kwargs
        except Exception:
            # kwargs doesn't match a variable in the message
            # log the issue and the kwargs
            LOG.exception(_LE('Exception in string format operation, '
                              'kwargs: %s') % kwargs)
            try:
                if CONF.fatal_exception_format_errors:
                    raise
            except cfg.NoSuchOptError:
                # Note: work around for Bug: #1447873
                if CONF.oslo_versionedobjects.fatal_exception_format_errors:
                    raise

        super(OasisException, self).__init__(self.message)

    def __str__(self):
        if six.PY3:
            return self.message
        return self.message.encode('utf-8')

    def __unicode__(self):
        return self.message

    def format_message(self):
        if self.__class__.__name__.endswith('_Remote'):
            return self.args[0]
        else:
            return six.text_type(self)


class ObjectNotFound(OasisException):
    message = _("The %(name)s %(id)s could not be found.")


class ResourceNotFound(ObjectNotFound):
    message = _("The %(name)s resource %(id)s could not be found.")
    code = 404


class AuthorizationFailure(OasisException):
    message = _("%(client)s connection failed. %(message)s")


class Invalid(OasisException):
    message = _("Unacceptable parameters.")
    code = 400


class InvalidUUID(Invalid):
    message = _("Expected a uuid but received %(uuid)s.")


class InvalidName(Invalid):
    message = _("Expected a name but received %(name)s.")


class InvalidDiscoveryURL(Invalid):
    message = _("Received invalid discovery URL '%(discovery_url)s' for "
                "discovery endpoint '%(discovery_endpoint)s'.")


class GetDiscoveryUrlFailed(OasisException):
    message = _("Failed to get discovery url from '%(discovery_endpoint)s'.")


class InvalidFunctionDiscoveryURL(Invalid):
    message = _("Invalid discovery URL '%(discovery_url)s'.")


class InvalidClusterSize(Invalid):
    message = _("Expected cluster size %(expect_size)d but get cluster "
                "size %(size)d from '%(discovery_url)s'.")


class GetClusterSizeFailed(OasisException):
    message = _("Failed to get the size of cluster from '%(discovery_url)s'.")


class InvalidIdentity(Invalid):
    message = _("Expected an uuid or int but received %(identity)s.")


class InvalidCsr(Invalid):
    message = _("Received invalid csr %(csr)s.")


class InvalidSubnet(Invalid):
    message = _("Received invalid subnet %(subnet)s.")


class HTTPNotFound(ResourceNotFound):
    pass


class Conflict(OasisException):
    message = _('Conflict.')
    code = 409


class ApiVersionsIntersect(OasisException):
    message = _("Version of %(name)s %(min_ver)s %(max_ver)s intersects "
                "with another versions.")


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    message = _("%(err)s")


class PatchError(Invalid):
    message = _("Couldn't apply patch '%(patch)s'. Reason: %(reason)s")


class NotAuthorized(OasisException):
    message = _("Not authorized.")
    code = 403


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class InvalidMAC(Invalid):
    message = _("Expected a MAC address but received %(mac)s.")


class ConfigInvalid(OasisException):
    message = _("Invalid configuration file. %(error_msg)s")


class SSHConnectFailed(OasisException):
    message = _("Failed to establish SSH connection to host %(host)s.")


class FileSystemNotSupported(OasisException):
    message = _("Failed to create a file system. "
                "File system %(fs)s is not supported.")

class FunctionNotFound(ResourceNotFound):
    message = _("Function %(bay)s could not be found.")


class FunctionAlreadyExists(Conflict):
    message = _("A bay with UUID %(uuid)s already exists.")


class NotSupported(OasisException):
    message = _("%(operation)s is not supported.")
    code = 400


class FunctionTypeNotSupported(OasisException):
    message = _("Function type (%(server_type)s, %(os)s, %(coe)s)"
                " not supported.")


class FunctionTypeNotEnabled(OasisException):
    message = _("Function type (%(server_type)s, %(os)s, %(coe)s)"
                " not enabled.")


class RequiredParameterNotProvided(OasisException):
    message = _("Required parameter %(heat_param)s not provided.")


class Urllib2InvalidScheme(OasisException):
    message = _("The urllib2 URL %(url)s has an invalid scheme.")


class OperationInProgress(Invalid):
    message = _("Function %(bay_name)s already has an operation in progress.")


class ImageNotFound(ResourceNotFound):
    """The code here changed to 400 according to the latest document."""
    message = _("Image %(image_id)s could not be found.")
    code = 400


class ImageNotAuthorized(OasisException):
    message = _("Not authorized for image %(image_id)s.")


class OSDistroFieldNotFound(ResourceNotFound):
    """The code here changed to 400 according to the latest document."""
    message = _("Image %(image_id)s doesn't contain os_distro field.")
    code = 400


class KeyPairNotFound(ResourceNotFound):
    message = _("Unable to find keypair %(keypair)s.")


class UnsupportedK8sQuantityFormat(OasisException):
    message = _("Unsupported quantity format for k8s bay.")


class UnsupportedDockerQuantityFormat(OasisException):
    message = _("Unsupported quantity format for Swarm bay.")


class FlavorNotFound(ResourceNotFound):
    """The code here changed to 400 according to the latest document."""
    message = _("Unable to find flavor %(flavor)s.")
    code = 400


class ExternalNetworkNotFound(ResourceNotFound):
    """The code here changed to 400 according to the latest document."""
    """"Ensure the network is not private."""
    message = _("Unable to find external network %(network)s.")
    code = 400


class TrustCreateFailed(OasisException):
    message = _("Failed to create trust for trustee %(trustee_user_id)s.")


class TrustDeleteFailed(OasisException):
    message = _("Failed to delete trust %(trust_id)s.")


class TrusteeCreateFailed(OasisException):
    message = _("Failed to create trustee %(username)s "
                "in domain %(domain_id)s")


class TrusteeDeleteFailed(OasisException):
    message = _("Failed to delete trustee %(trustee_id)s")


class QuotaAlreadyExists(Conflict):
    message = _("Quota for project %(project_id)s already exists "
                "for resource %(resource)s.")


class RegionsListFailed(OasisException):
    message = _("Failed to list regions.")


class NodePoolPolicyAlreadyExists(Conflict):
    message = _("A nodepool policy with UUID %(uuid)s already exists.")


class NodePoolAlreadyExists(Conflict):
    message = _("A nodepool with UUID %(uuid)s already exists.")


class NodePoolNotFound(ResourceNotFound):
    message = _("NodePool %(nodepool)s could not be found.")
