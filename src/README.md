# Overview

This charm provides the Manila shared file service for an OpenStack Cloud.

# Usage

Manila relies on services from the mysql/percona, rabbitmq-server, keystone
charms, and a storage backend charm:

Create a manila.yaml document similar to:
TODO:
series: xenial
services:
  pxc:
    charm: ./xenial/percona-cluster
    num_units: 1
    options:
      max-connections: 20000
      dataset-size: 256M
  rmq:
    charm: ./xenial/rabbitmq-server
    num_units: 1
  pxc-proposed:
    charm: ./xenial/percona-cluster
    num_units: 1
    options:
      max-connections: 20000
      dataset-size: 256M
      source: proposed
  rmq-proposed:
    charm: ./xenial/rabbitmq-server
    num_units: 1
    options:
      source: proposed
  keystone-newton:
    charm: ./xenial/keystone
    options:
      admin-password: openstack
      admin-token: ubuntutesting
      openstack-origin: cloud:xenial-newton
  cinder-newton:
    charm: ./xenial/cinder
    options:
      openstack-origin: cloud:xenial-newton
  keystone-newton-proposed:
    charm: ./xenial/keystone
    options:
      admin-password: openstack
      admin-token: ubuntutesting
      openstack-origin: cloud:xenial-newton/proposed
  cinder-newton-proposed:
    charm: ./xenial/cinder
    options:
      openstack-origin: cloud:xenial-newton/proposed
  keystone-newton-staging:
    charm: ./xenial/keystone
    options:
      admin-password: openstack
      admin-token: ubuntutesting
      openstack-origin: ppa:ubuntu-cloud-archive/newton-staging
  cinder-newton-staging:
    charm: ./xenial/cinder
    options:
      openstack-origin: ppa:ubuntu-cloud-archive/newton-staging

and then

    juju deploy manila.yaml

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-barbican/+filebug).

For general questions please refer to the OpenStack [Charm Guide](https://github.com/openstack/charm-guide).
