# Keystone v3  Manual testing

If you want to play around with the barbican charm, or just test that it is
working, then the following will be usefull.  Note, that this can be used as a
jumping off point for testing other HSM charms (as they are written).  This has
also been retained to show how the v3 keystone credentials should be set up for
Barbican.

Note that Barbican will only allow creation of a secret if the user is either
the 'admin' user or has a role of 'creator'.


# Steps

## 1. Build the charm

```bash
tox -e build -- -s xenial
```

This will build a xenial series charm.

## 2. Bootstrap and deploy the environment

We'll use the juju-deployer bundle to deploy a suitable testing environment.

```bash
cd manual_testing/v3_keystone
ln -s ../../build/xenial xenial
juju bootstrap
cd ../../build && juju-deployer -L -c barbican.yaml
```

Note, if you're building for another series, change the link about -- it's so
that juju-deployer can access the local charm.

## 3. Configure a user and project for the barbican use

```bash
source novarc
./keystone_setup.sh
```

## 4. Create a secret to check that it works.

```bash
./secret-store.py
```

## 5. Profit

Now you can investigate other features of barbican!
