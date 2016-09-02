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

from __future__ import absolute_import
from __future__ import print_function

import unittest

import mock

import charm.openstack.manila as manila


class Helper(unittest.TestCase):

    def setUp(self):
        self._patches = {}
        self._patches_start = {}
        # patch out the select_release to always return 'mitaka'
        self.patch(manila.unitdata, 'kv')
        _getter = mock.MagicMock()
        _getter.get.return_value = manila.ManilaCharm.release
        self.kv.return_value = _getter

    def tearDown(self):
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch(self, obj, attr, return_value=None, **kwargs):
        mocked = mock.patch.object(obj, attr, **kwargs)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)


class TestOpenStackManila(Helper):

    def test_install(self):
        self.patch(manila.ManilaCharm, 'set_config_defined_certs_and_keys')
        self.patch(manila.ManilaCharm.singleton, 'install')
        manila.install()
        self.install.assert_called_once_with()

    def test_setup_endpoint(self):
        self.patch(manila.ManilaCharm, 'set_config_defined_certs_and_keys')
        self.patch(manila.ManilaCharm, 'service_type',
                   new_callable=mock.PropertyMock)
        self.patch(manila.ManilaCharm, 'region',
                   new_callable=mock.PropertyMock)
        self.patch(manila.ManilaCharm, 'public_url',
                   new_callable=mock.PropertyMock)
        self.patch(manila.ManilaCharm, 'internal_url',
                   new_callable=mock.PropertyMock)
        self.patch(manila.ManilaCharm, 'admin_url',
                   new_callable=mock.PropertyMock)
        self.service_type.return_value = 'type1'
        self.region.return_value = 'region1'
        self.public_url.return_value = 'public_url'
        self.internal_url.return_value = 'internal_url'
        self.admin_url.return_value = 'admin_url'
        keystone = mock.MagicMock()
        manila.setup_endpoint(keystone)
        keystone.register_endpoints.assert_called_once_with(
            'type1', 'region1', 'public_url', 'internal_url', 'admin_url')

    def test_render_configs(self):
        self.patch(manila.ManilaCharm, 'set_config_defined_certs_and_keys')
        self.patch(manila.ManilaCharm.singleton, 'render_with_interfaces')
        manila.render_configs('interfaces-list')
        self.render_with_interfaces.assert_called_once_with(
            'interfaces-list')


class TestManilaCharm(Helper):

    pass
