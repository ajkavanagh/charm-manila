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
# The barbican handlers class

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

PACKAGES = ['barbican-common', 'barbican-api', 'barbican-worker',
            'python-mysqldb']
BARBICAN_DIR = '/etc/barbican/'
BARBICAN_CONF = BARBICAN_DIR + "barbican.conf"
BARBICAN_API_PASTE_CONF = BARBICAN_DIR + "barbican-api-paste.ini"
BARBICAN_WSGI_CONF = '/etc/apache2/conf-available/barbican-api.conf'

OPENSTACK_RELEASE_KEY = 'barbican-charm.openstack-release-version'

# select the default release function and ssl feature
charms_openstack.charm.use_defaults('charm.default-select-release')

# TODO: this should be on the charm class
charms_openstack.charm.use_features('ssl')


###
# Implementation of the Barbican Charm classes

# Add some properties to the configuration for templates/code to use with the
# charm instance.  The config_validator is called when the configuration is
# loaded, and the properties are to add those names to the config object.

@charms_openstack.adapters.config_validator
def validate_keystone_api_version(config):
    if config.keystone_api_version not in ['2', '3', 'none']:
        raise ValueError(
            "Unsupported keystone-api-version ({}). It should be 2 or 3"
            .format(config.keystone_api_version))


@charms_openstack.adapters.config_property
def barbican_api_keystone_pipeline(config):
    if config.keystone_api_version == "2":
        return 'cors keystone_authtoken context apiapp'
    else:
        return 'cors keystone_v3_authtoken context apiapp'


@charms_openstack.adapters.config_property
def barbican_api_pipeline(config):
    return {
        "2": "cors keystone_authtoken context apiapp",
        "3": "cors keystone_v3_authtoken context apiapp",
        "none": "cors unauthenticated-context apiapp"
    }[config.keystone_api_version]


@charms_openstack.adapters.config_property
def barbican_api_keystone_audit_pipeline(config):
    if config.keystone_api_version == "2":
        return 'keystone_authtoken context audit apiapp'
    else:
        return 'keystone_v3_authtoken context audit apiapp'


# Adapt the barbican-hsm-plugin relation for use in rendering the config
# for Barbican.  Note that the HSM relation is optional, so we have a class
# variable 'exists' that we can test in the template to see if we should
# render HSM parameters into the template.

@charms_openstack.adapters.adapter_property('hsm')
def library_path(hsm):
    """Provide a library_path property to the template if it exists"""
    try:
        return hsm.relation.plugin_data['library_path']
    except:
        return ''

@charms_openstack.adapters.adapter_property('hsm')
def login(hsm):
    """Provide a login property to the template if it exists"""
    try:
        return hsm.relation.plugin_data['login']
    except:
        return ''

@charms_openstack.adapters.adapter_property('hsm')
def slot_id(hsm):
    """Provide a slot_id property to the template if it exists"""
    try:
        return hsm.relation.plugin_data['slot_id']
    except:
        return ''


# class BarbicanAdapters(charms_openstack.adapters.OpenStackAPIRelationAdapters):
    # """
    # Adapters class for the Barbican charm.

    # This plumbs in the BarbicanConfigurationAdapter as the ConfigurationAdapter
    # to provide additional properties.
    # """

    # relation_adapters = {
        # 'hsm': HSMAdapter,
    # }

    # def __init__(self, relations):
        # super(BarbicanAdapters, self).__init__(
            # relations,
            # options_instance=BarbicanConfigurationAdapter(
                # port_map=BarbicanCharm.api_ports))


class BarbicanCharm(charms_openstack.charm.HAOpenStackCharm):
    """BarbicanCharm provides the specialisation of the OpenStackCharm
    functionality to manage a barbican unit.
    """

    release = 'mitaka'
    name = 'barbican'
    packages = PACKAGES
    api_ports = {
        'barbican-worker': {
            os_ip.PUBLIC: 9311,
            os_ip.ADMIN: 9312,
            os_ip.INTERNAL: 9311,
        }
    }
    service_type = 'barbican'
    default_service = 'barbican-worker'
    services = ['apache2', 'barbican-worker']

    # Note that the hsm interface is optional - defined in config.yaml
    required_relations = ['shared-db', 'amqp', 'identity-service']

    # TODO: plumb in the condition for the optional relation becoming required
    conditional_relations = {
        'hsm': lambda self: self.config.require_hsm_plugin,
    }

    restart_map = {
        BARBICAN_CONF: services,
        BARBICAN_API_PASTE_CONF: services,
        BARBICAN_WSGI_CONF: services,
    }

    # TODO: how do we make this adapter_class automagic?
    adapters_class = BarbicanAdapters

    ha_resources = ['vips', 'haproxy']

    def install(self):
        """Customise the installation, configure the source and then call the
        parent install() method to install the packages
        """
        # DEBUG - until seed random change lands into xenial cloud archive
        # BUG #1599550 - barbican + softhsm2 + libssl1.0.0:
        #  pkcs11:_generate_random() fails
        # WARNING: This charm can't be released into stable until the bug is
        # fixed.
        charmhelpers.fetch.add_source("ppa:ajkavanagh/barbican")
        self.configure_source()
        # and do the actual install
        super(BarbicanCharm, self).install()

    # def states_to_check(self, required_relations=None):
        # """Override the default states_to_check() for the assess_status
        # functionality so that, if we have to have an HSM relation, then enforce
        # it on the assess_status() call.

        # If param required_relations is not None then it overrides the
        # instance/class variable self.required_relations.

        # :param required_relations: [list of state names]
        # :returns: [states{} as per parent method]
        # """
        # if required_relations is None:
            # required_relations = self.required_relations
        # if hookenv.config('require-hsm-plugin'):
            # required_relations.append('hsm')
        # return super(BarbicanCharm, self).states_to_check(
            # required_relations=required_relations)
