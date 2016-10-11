TODO
====

It's necessary for the manila charm to be able to install itself as one of a
number of roles:

 1. The manila-api: this provides the API to the rest of OpenStack.  Until this
    is HA aware, only ONE manila-api can be provisioned.  Also, it may not make
    sense to provision more than one manila-api server per OpenStack
    installation.
 2. The manila-scheduler: TODO

It's necessary to have the ability to configure a share backend independently
of the main charm.  This means that plugin charms will be used to configure
each backend.

Essentially, a plugin needs to be able to configure:

 - it's section in the manila.conf along with any network plugin's that it
     needs (assuming that it's a share that manages it's own share-instance).
