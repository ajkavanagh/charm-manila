# Keystone v2  Manual testing

If you want to play around with the manila charm, or just test that it is
working, then the following will be usefull.

# Steps

## 1. Build the charm

```bash
tox -e build
```


## 2. Bootstrap and deploy the environment

We'll use the juju-deployer bundle to deploy a suitable testing environment.

```bash
cd manual_testing/v2_keystone
ln -s ../../build/xenial xenial
juju bootstrap
juju-deployer -L -c manila.yaml
```

Note, if you're building for another series, change the link about -- it's so
that juju-deployer can access the local charm.

## 3. Configure a user and project for the barbican use

```bash
source novarc
./keystone_setup.sh
```

## 4. Create a container, and a fileshare and test that the container can access it.


## 5. Profit

Now you can investigate other features of manila!
