#!/usr/bin/python

import subprocess
import yaml
import os
import sys

from neutronclient.v2_0 import client as ne_client
from novaclient import client as no_client
from keystoneclient.v2_0 import client as ks_client
from keystoneclient.auth import identity
from keystoneclient import session

if __name__ == '__main__':
    # use session based authentication
    ep = os.environ['OS_AUTH_URL']
    if not ep.endswith('v2.0'):
        ep = "{}/v2.0".format(ep)
    auth = identity.v2.Password(username=os.environ['OS_USERNAME'],
                                password=os.environ['OS_PASSWORD'],
                                tenant_name=os.environ['OS_TENANT_NAME'],
                                auth_url=ep)
    sess = session.Session(auth=auth)
    keystone = ks_client.Client(session=sess)
    keystone.auth_ref = auth.get_access(sess)

    neutron_ep = keystone.service_catalog.url_for(
            service_type='network', endpoint_type='publicURL')
    neutron = ne_client.Client(session=sess)
    # neutron = ne_client.Client(username=os.environ['OS_USERNAME'],
                               # password=os.environ['OS_PASSWORD'],
                               # tenant_name=os.environ['OS_TENANT_NAME'],
                               # auth_url=os.environ['OS_AUTH_URL'],
                               # region_name=os.environ['OS_REGION_NAME'])
    nova_ep = keystone.service_catalog.url_for(
        service_type='compute', endpoint_type='publicURL')
    nova = no_client.Client('2', session=sess)
    # nova = no_client.Client('2',
                            # os.environ['OS_USERNAME'],
                            # os.environ['OS_PASSWORD'],
                            # os.environ['OS_TENANT_NAME'],
                            # os.environ['OS_AUTH_URL'],
                            # os.environ['OS_REGION_NAME'])

    net_id = os.environ.get('NET_ID')
    if net_id:
        # Use OSCI / Jenkins environment variable if defined.
        print('Using NET_ID environment variable: {}'.format(net_id))
    else:
        # Preserve existing default behavior (eg. manual testing)
        net_name = os.environ['OS_USERNAME'] + '_admin_net'
        print('Using default network name: {}'.format(net_name))
        try:
            network = neutron.list_networks(name=net_name)['networks'][0]
            net_id = network['id']
        except IndexError:
            print('Unable to find local network {}'.format(net_name))
            raise ValueError('Unable to find local network {}'.format(net_name))

    service = sys.argv[1]

    service_config = yaml.load(
        subprocess.check_output(['juju', 'status', service])
    )

    uuids = []
    for machine in service_config['machines']:
        uuids.append(service_config['machines'][machine]['instance-id'])

    ext_port = []
    if len(sys.argv) >= 3:
        ext_port = [sys.argv[2]]

    if len(uuids) > 0:
        for uuid in uuids:
            print("Attaching interface to instance {}".format(uuid))
            server = nova.servers.get(uuid)
            result = server.interface_attach(port_id=None,
                                             net_id=net_id,
                                             fixed_ip=None).to_dict()
            ext_port.append("br-ex:{}".format(result['mac_addr']))

    ports = " ".join(ext_port)
    if ports:
        print("Setting ext-port configuration on {} to {}".format(service, ports))
        subprocess.check_call(['juju', 'set', service, 'data-port={}'.format(ports)])
    else:
        print("Nothing to do with ext-port configuration")

