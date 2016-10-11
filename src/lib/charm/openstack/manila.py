# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# The manila handlers class

# bare functions are provided to the reactive handlers to perform the functions
# needed on the class.
from __future__ import absolute_import

import re
import subprocess

import charmhelpers.contrib.openstack.utils as ch_utils
import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.unitdata as unitdata
import charmhelpers.fetch

import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip

# note that manila-common is pulled in via the other packages.
PACKAGES = ['manila-api',
            'manila-data',
            'manila-scheduler',
            'manila-share',
            'python-pymysql',
            'python-apt',  # for subordinate neutron-openvswitch if needed.
            ]

MANILA_DIR = '/etc/manila/'
MANILA_CONF = MANILA_DIR + "manila.conf"
MANILA_LOGGING_CONF = MANILA_DIR + "logging.conf"
MANILA_API_PASTE_CONF = MANILA_DIR + "api-paste.ini"

# select the default release function and ssl feature
charms_openstack.charm.use_defaults('charm.default-select-release')

def strip_join(s, divider=" "):
    """Cleanup the string passed, split on whitespace and then rejoin it cleanly

    :param s: A sting to cleanup, remove non alpha chars and then represent the
        string.
    :param divider: The joining string to put the bits back together again.
    :returns: string
    """
    return divider.join(re.split(r'\s+', re.sub(r'([^\s\w-])+', '', (s or ""))))


###
# Compute some options to help with template rendering
@charms_openstack.adapters.config_property
def computed_share_backends(config):
    """Determine the backend protocols that are provided as a string.

    At the moment it just takes the 'share-backends' configuration option,
    strings not alpha chars, lowercases it, and then provides a comma separated
    list.

    :param config: the config option on which to look up config options
    :returns: string
    """
    return strip_join(config.share_backends, ' ')


@charms_openstack.adapters.config_property
def computed_share_protocols(config):
    """Return a list of protocols as a comma (no space) separated list.
    The default protocols are CIFS,NFS.

    :param config: the config option on which to look up config options
    :returns: string
    """
    return strip_join(config.share_protocols, ',').upper()


@charms_openstack.adapters.config_property
def computed_generic_driver(config):
    """Return True if the generic driver should be configured.
    :returns: boolean
    """
    hookenv.log(">>>> computed_generic_driver")
    hookenv.log("backends: {}".format(computed_share_backends(config)))
    return 'generic' in computed_share_backends(config).lower().split(' ')


@charms_openstack.adapters.config_property
def computed_generic_use_password(config):
    """Return True if the generic driver should use a password rather than an
    ssh key.
    :returns: boolean
    """
    return (bool(config.generic_driver_service_instance_password) &
            ((config.generic_driver_auth_type or '').lower()
             in ('password', 'both')))


@charms_openstack.adapters.config_property
def computed_generic_use_ssh(config):
    """Return True if the generic driver should use a password rather than an
    ssh key.
    :returns: boolean
    """
    return ((config.generic_driver_auth_type or '').lower() in ('ssh', 'both'))


@charms_openstack.adapters.config_property
def computed_generic_define_ssh(config):
    """Return True if the generic driver should define the SSH keys
    :returns: boolean
    """
    return (bool(config.generic_driver_service_ssh_key) &
            boot(config.generic_driver_service_ssh_key_public))


@charms_openstack.adapters.config_property
def computed_debug_level(config):
    """Return NONE, INFO, WARNING, DEBUG depending on the settings of
    options.debug and options.level
    :returns: string, NONE, WARNING, DEBUG
    """
    if not config.debug:
        return "NONE"
    if config.verbose:
        return "DEBUG"
    return "WARNING"


###
# Implementation of the Manila Charm classes

class ManilaCharm(charms_openstack.charm.HAOpenStackCharm):
    """ManilaCharm provides the specialisation of the OpenStackCharm
    functionality to manage a manila unit.
    """

    release = 'mitaka'
    name = 'manila'
    packages = PACKAGES
    api_ports = {
        'manila-api': {
            os_ip.PUBLIC: 8786,
            os_ip.ADMIN: 8786,
            os_ip.INTERNAL: 8786,
        },
    }
    service_type = 'manila'
    # manila needs a second service type as well - there is a custom connect
    # function to set both service types.
    service_type_v2 = 'manilav2'

    default_service = 'manila-api'
    services = ['manila-api',
                'manila-scheduler',
                'manila-share',
                'manila-data']

    # Note that the hsm interface is optional - defined in config.yaml
    required_relations = ['shared-db', 'amqp', 'identity-service']

    restart_map = {
        MANILA_CONF: services,
        MANILA_API_PASTE_CONF: services,
        MANILA_LOGGING_CONF: services,
    }

    # This is the command to sync the database
    sync_cmd = ['sudo', 'manila-manage', 'db', 'sync']

    # ha_resources = ['vips', 'haproxy']

    # Custom charm configuration
    # These are the backends which this charm knows how to configure.
    valid_share_backends = ['generic',]

    def install(self):
        """Called when the charm is being installed or upgraded.

        The available configuration options need to be check AFTER the charm is
        installed to check to see whether it is blocked or can go into service.
        """
        super().install()
        # TODO: this creates the /etc/nova directory for the
        # neutron-openvswitch plugin if needed.
        subprocess.check_call(["mkdir", "-p", "/etc/nova"])
        self.assess_status()

    def custom_assess_status_check(self):
        """Verify that the configuration provided is valid and thus the service
        is ready to go.  This will return blocked if the configuraiton is not
        valid for the service.

        :returns (status: string, message: string): the status, and message if
            there is a problem. Or (None, None) if there are no issues.
        """
        config = self.config
        if not config.get('share-backends', None):
            return 'blocked', 'No share backends configured'
        backends = str(config['share-backends']).split(' ')
        invalid_backends = set(backends).difference(self.valid_share_backends)
        if invalid_backends:
            return 'blocked', 'Unknown backends: {}'.format(invalid_backends)
        default_share_backend = config.get('default-share-backend', None)
        if not default_share_backend:
            return 'blocked', "'default-share-backend' is not set"
        if default_share_backend not in backends:
            return ('blocked',
                    "'default-share-backend:{}' is not a configured backend"
                    .format(default_share_backend))
        if 'generic' in backends:
            message = self._validate_generic_driver_config()
            if message:
                return 'blocked', message
        return None, None

    def _validate_generic_driver_config(self):
        """Validate that the driver configuration is at least complete, and
        that it was valid when it used (either at configuration time or config
        changed time)

        :returns string/None: string if there is a proble, None if it is valid
        """
        config = self.config
        if not config.get('generic-driver-handles-share-servers', None):
            # Nothing to check if the driver doesn't handle share servers
            # directly.
            return None
        if not config.get('generic-driver-service-image-name', None):
            return "Missing 'generic-driver-service-image-name'"
        if not config.get('generic-driver-service-instance-user', None):
            return "Missing 'generic-driver-service-instance-user'"
        if not config.get('generic-driver-service-instance-flavor-id', None):
            return "Missing 'generic-driver-service-instance-flavor-id"
        # Need at least one of the password or the keypair
        if (not (bool(config.get(
                'generic-driver-service-instance-password', None))) and
                not (bool(config.get('generic-driver-keypair-name', None)))):
            return "Need at least one of instance password or keypair name"
        return None

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def get_database_setup(self):
        """Provide the default database credentials as a list of 3-tuples

        returns a structure of:
        [
            {'database': <database>,
             'username': <username>,
             'hostname': <hostname of this unit>
             'prefix': <the optional prefix for the database>, },
        ]

        :returns [{'database': ...}, ...]: credentials for multiple databases
        """
        return [
            dict(
                database=self.config['database'],
                username=self.config['database-user'],
                hostname=hookenv.unit_private_ip(), )
        ]

    def register_endpoints(self, keystone):
        """Custom function to register the TWO keystone endpoints that this
        charm requires.  'charm' and 'charmv2'.

        :param keystone: the keystone relation on which to setup the endpoints
        """
        # regsiter the first endpoint
        self._custom_register_endpoints(keystone, 'v1',
                                        self.service_type,
                                        self.region,
                                        self.public_url,
                                        self.internal_url,
                                        self.admin_url)
        # regsiter the second endpoint
        self._custom_register_endpoints(keystone, 'v2',
                                        self.service_type_v2,
                                        self.region,
                                        self.public_url_v2,
                                        self.internal_url_v2,
                                        self.admin_url_v2)

    @staticmethod
    def _custom_register_endpoints(keystone, prefix, service, region,
                                   public_url, internal_url, admin_url):
        """Custom function to enable registering of multiple endpoints.

        Keystone charm understands multiple endpoints if they are prefixed with
        a string_  as in 'v1_service' and 'v2_service', etc.  However, the
        keystone interface doesn't know how to do this.  Therefore, this
        function duplicates part of that functionality but enables the
        'multiple' endpoints to be set

        :param keystone: the relation that is keystone.
        :param prefix: the prefix to prepend to '_<var>'
        :param service: the service to set
        :param region: the OS region
        :param public_url: the public_url
        :param internal_url: the internal_url
        :prarm admin_url: the admin url.
        """
        relation_info = {
            '{}_service'.format(prefix): service,
            '{}_public_url'.format(prefix): public_url,
            '{}_internal_url'.format(prefix): internal_url,
            '{}_admin_url'.format(prefix): admin_url,
            '{}_region'.format(prefix): region,
        }
        keystone.set_local(**relation_info)
        keystone.set_remote(**relation_info)

    @property
    def public_url(self):
        return super().public_url + "/v1/%(tenant_id)s"

    @property
    def admin_url(self):
        return super().admin_url + "/v1/%(tenant_id)s"

    @property
    def internal_url(self):
        return super().internal_url + "/v1/%(tenant_id)s"

    @property
    def public_url_v2(self):
        return super().public_url + "/v2/%(tenant_id)s"

    @property
    def admin_url_v2(self):
        return super().admin_url + "/v2/%(tenant_id)s"

    @property
    def internal_url_v2(self):
        return super().internal_url + "/v2/%(tenant_id)s"
