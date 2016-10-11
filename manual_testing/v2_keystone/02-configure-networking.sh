#/bin/bash

# stolen/heavily influenced from openstack-charm-testing

# Set up the network, projects and users after we've deployed the charms
# assumes that overcloud is in ./novarc and undercloud (serverstack) is in
# ~/novarc

set -ex

source ./vars.sh

# Accept network type as first parameter, assume gre if unspecified
net_type=${1:-"gre"}

# add extra port to overcloud neutron-gateway and configure charm to use it
# note that we have to source the UNDERCLOUD so that the script uses the
# network that we are connected to.
source $UNDERCLOUD
./post-deploy-config.py neutron-gateway

# now everything is with the OVERCLOUD
source $OVERCLOUD

## Now set up the networks so we can test shares.
./neutron-ext-net.py --network-type flat -g $GATEWAY -c $CIDR_EXT \
  -f $FIP_RANGE ext_net
./neutron-tenant-net.py --network-type $net_type -t admin -r provider-router \
  -N $NAMESERVER private $CIDR_PRIV

 # finally we want to set up a wide open the security group so we can reach the
 # instances
./sec_groups.sh
