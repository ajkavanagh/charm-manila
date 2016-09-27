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
            'python-pymysql']

MANILA_DIR = '/etc/manila/'
MANILA_CONF = MANILA_DIR + "manila.conf"
MANILA_LOGGING_CONF = MANILA_DIR + "logging.conf"
MANILA_API_PASTE_CONF = MANILA_DIR + "api-paste.ini"

# select the default release function and ssl feature
charms_openstack.charm.use_defaults('charm.default-select-release')


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
        return super().public_url + "/v1/"

    @property
    def admin_url(self):
        return super().admin_url + "/v1/"

    @property
    def internal_url(self):
        return super().internal_url + "/v1/"

    @property
    def public_url_v2(self):
        return super().public_url + "/v2/"

    @property
    def admin_url_v2(self):
        return super().admin_url + "/v2/"

    @property
    def internal_url_v2(self):
        return super().internal_url + "/v2/"
