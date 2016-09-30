#!/bin/bash

# stolen/heavily influenced from openstack-charm-testing

# Set up the network, projects and users after we've deployed the charms
# assumes that overcloud is in ./novarc and undercloud (serverstack) is in
# ~/novarc

set -ex

OVERCLOUD=./novarc
UNDERCLOUD=~/novarc

# Set serverstack defaults, if not already set.
[[ -z "$GATEWAY" ]] && export GATEWAY="10.5.0.1"
[[ -z "$CIDR_EXT" ]] && export CIDR_EXT="10.5.0.0/16"
[[ -z "$FIP_RANGE" ]] && export FIP_RANGE="10.5.150.0:10.5.200.254"
[[ -z "$NAMESERVER" ]] && export NAMESERVER="10.245.160.2"
[[ -z "$CIDR_PRIV" ]] && export CIDR_PRIV="192.168.21.0/24"
[[ -z "$SWIFT_IP" ]] && export SWIFT_IP="10.245.161.162"

# Accept network type as first parameter, assume gre if unspecified
net_type=${1:-"gre"}

# add extra port to overcloud neutron-gateway and configure charm to use it
# note that we have to source the UNDERCLOUD so that the script uses the network
# that we are connected to.
source ~/novarc
./post-deploy-config.py neutron-gateway

# now everything is with the OVERCLOUD
source ./novarc

# handy function to test if an array contains a value $1 in ${2[@]}
# returns $? as 1 if the element does exist
elementIn () {
  local e
  for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
  return 1
}

# we need cirros and manila-service-image -- if not, we'll have to add them.
glance_image_list=($(openstack image list -c Name -f value))

# fetch cirros if it doesn't exist!
if ! elementIn "cirros" ${glance_image_list[@]};
then
  [ -f ~/images/cirros-0.3.4-x86_64-disk.img ] || {
    wget -O ~/images/cirros-0.3.4-x86_64-disk.img \
      http://$SWIFT_IP:80/swift/v1/images/cirros-0.3.4-x86_64-disk.img
  }
  glance --os-image-api-version 1 image-create --name="cirros" \
    --is-public=true --progress --container-format=bare \
    --disk-format=qcow2 < ~/images/cirros-0.3.4-x86_64-disk.img
fi

# fetch the manila-service-image if it doesn't exist (this is big)
if ! elementIn "manila-service-image" ${glance_image_list[@]};
then
  [ -f ~/images/manila-service-image-master.qcow2 ] || {
    wget -O ~/images/manila-service-image-master.qcow2 \
      http://tarballs.openstack.org/manila-image-elements/images/manila-service-image-master.qcow2
  }
  glance --os-image-api-version 1 image-create --name="manila-service-image" \
    --is-public=true --progress --container-format=bare \
    --disk-format=qcow2 < ~/images/manila-service-image-master.qcow2
fi


## Now set up the networks so we can test shares.
source $OVERCLOUD
./neutron-ext-net.py --network-type flat -g $GATEWAY -c $CIDR_EXT \
  -f $FIP_RANGE ext_net
./neutron-tenant-net.py --network-type $net_type -t admin -r provider-router \
  -N $NAMESERVER private $CIDR_PRIV


# Create demo/testing users, tenants and flavor
openstack project create --or-show demo
openstack user create --or-show --project demo --password pass --email demo@dev.null demo
openstack role create --or-show Member
roles=($(openstack role list --user demo --project demo -c Name -f value))
if ! elementIn "Member" ${roles[@]}; then
  openstack role add --user demo --project demo Member
fi

# ensure that a keypair is setup for the user
keypairs=($(openstack keypair list -c Name -f value))
if ! elementIn "demo-user" ${keypairs[@]}; then
  [ -f ./demo-user-rsa ] && rm -f ./demo-user-rsa
  openstack keypair create demo-user > ./demo-user-rsa
  chmod 400 ./demo-user-rsa
fi
 
# get list of running servers
server_list=($(openstack server list -c Name -f value))
if ! elementIn "cirros-test1" ${server_list[@]}; then
  # and create two test vms for share testing
  # see if the two servers exist -- if either exists, tear it down.
  openstack server create --flavor m1.cirros --image cirros --key-name demo-user \
    --security-group default --nic net-id=686d654c-87ac-4e19-8616-cdb351bcaa52  \
    cirros-test1
fi
if ! elementIn "cirros-test2" ${server_list[@]}; then
  # and create two test vms for share testing
  # see if the two servers exist -- if either exists, tear it down.
  openstack server create --flavor m1.cirros --image cirros --key-name demo-user \
    --security-group default --nic net-id=686d654c-87ac-4e19-8616-cdb351bcaa52  \
    cirros-test2
fi

#vim: set ts=2 et:
