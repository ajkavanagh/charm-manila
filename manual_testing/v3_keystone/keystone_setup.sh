#!/bin/bash

set -ex

# Create demo/testing users, tenants and flavor
openstack project create demo
openstack user create --project demo --password pass --email demo@dev.null demo
# Note that this user CAN'T delete the secret.  Only the admin user can do
# that.
openstack role create Creator
openstack role add --user demo --project demo Creator
