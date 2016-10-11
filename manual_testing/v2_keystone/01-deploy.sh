#/bin/bash

# deploy the openstack bundle using Juju 1.x or 2.0

# This assumes that you have bootstrapped and (for Juju 2.0) switched to the
# model.
set -ex

version=$(juju --version | head -c 1)
if [ "$version" == "1" ]; then
    juju-deployer -L -c manila.yaml
elif [ "$version" == "2" ]; then
    juju deploy manila-juju-2.0.yaml
else
    echo "Can't work with version $version"
    exit 1
fi

