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

# this is just for the reactive handlers and calls into the charm.
from __future__ import absolute_import

import charms.reactive
import charms_openstack.charm

import charmhelpers.core.hookenv as hookenv

# This charm's library contains all of the handler code associated with
# manila -- we need to import it to get the definitions for the charm.
import charm.openstack.manila  # noqa


# Use the charms.openstack defaults for common states and hooks
charms_openstack.charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    # 'identity-service.connected',
    'identity-service.available',  # enables SSL support
    'config.changed',
    'update-status')



@charms.reactive.when('identity-service.connected')
def register_endpoints(keystone):
    with charms_openstack.charm.provide_charm_instance() as manila_charm:
        manila_charm.register_endpoints(keystone)
        manila_charm.assess_status()


@charms.reactive.when('shared-db.available')
@charms.reactive.when('manila.config.rendered')
def maybe_do_syncdb(shared_db):
    """Sync the database when the shared-db becomes available.  Note that the
    charms.openstack.OpenStackCharm.db_sync() default method checks that only
    the leader does the sync.  As manila uses alembic to do the database
    migration, it doesn't matter if it's done more than once, so we don't have
    to gate it in the charm.
    """
    with charms_openstack.charm.provide_charm_instance() as manila_charm:
        manila_charm.db_sync()


@charms.reactive.when('shared-db.available')
@charms.reactive.when('identity-service.available')
@charms.reactive.when('amqp.available')
def render_stuff(*args):
    """Render the configuration for Manila when all the interfaces are
    available.
    """
    hookenv.log(">>>>>>>rendering interfaces with {}".format(args))
    with charms_openstack.charm.provide_charm_instance() as manila_charm:
        manila_charm.render_with_interfaces(args)
        manila_charm.assess_status()
        charms.reactive.set_state('manila.config.rendered')
