#/bin/bash

# Configure the manila specific parts of shares; the type and other basic info.

source ./vars.sh
source $OVERCLOUD

set -ex

# see if the type list has been set up
types=($(manila type-list | head -n -1 | tail -n +4 | awk '{print $4}'))
if ! elementIn "default_share_type" ${types[@]}; then
  manila type-create default_share_type True
fi

# get the share network - if not available then try to set it up.
share_networks=($(manila share-network-list | head -n -1 | tail -n +4 | awk '{print $4}'))
if ! elementIn "test_share_network" ${share_networks[@]}; then
  # create the share network
  net=$(openstack network list -c ID -c Name -c Subnets -f value | grep private)
  net_id=$(echo $net | awk '{print $1}' | tr -d '\n')
  subnet_id=$(echo $net | awk '{print $3}' | tr -d '\n')
  manila share-network-create --name test_share_network \
      --neutron-net-id $net_id \
      --neutron-subnet-id $subnet_id
fi

# now configure the rest of the manila config items to enable the generic
# driver
flavor_id=$(openstack flavor list -c ID -c Name -f value | grep manila-service-flavor | awk '{ print $1 }')
version=$(juju --version | head -c 1)
if [ "$version" == "1" ]; then
    juju_command="manila set"
elif [ "$version" == "2" ]; then
    juju_command="config manila"
else
    echo "Can't work with version $version"
    exit 1
fi
juju $juju_command \
    generic-driver-service-instance-flavor-id=$flavor_id \
    share-backends=generic \
    generic-driver-handles-share-servers=true \
    default-share-backend=generic \
    generic-driver-service-instance-password=manila \
    generic-driver-auth-type=password
