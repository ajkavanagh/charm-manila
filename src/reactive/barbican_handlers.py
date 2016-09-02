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

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm as charm

# This charm's library contains all of the handler code associated with
# barbican
import charm.openstack.barbican as barbican


charm.use_defaults(
    'charm.installed',
    'amqp',
    'shared-db',
    'identity-service',
    'config.changed',
    'update-status')


# TODO actually make this what we want
@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
@charm.optional_interface('hsm.available')
def render_stuff(*args):
    """Render the configuration for Barbican when all the interfaces are
    available.

    Note that the HSM interface is optional (hence the @when_any) and thus is
    only used if it is available.
    """
    charm.default_render_configs(*args)
