#!/usr/bin/env python
#
# The approach we use here is as follows:
# * get a list of hypervisors that we're interested in
# * get the list of instances in state shutoff on the hypervisors
# * get the most recent in the list of instance_actions for each instance
# * if the last instance_action is a stop and it was more than six months
#   ago, add the instance to the list for expiry and add the owning tenant
#   to the list for notification
# * finally, collect the list of tenant managers for each notifying tenant
#   and spit out a list of instances owned by that tenant.
#
# Should be fairly simple . . .

import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pprint

from keystoneclient.v3.client import Client as keystone_client
from novaclient.client import Client as nova_client
from novaclient.v2.contrib import instance_action

# some of this is ripped straight out of the NeCTAR expiry handling tool
ACTION_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def get_nova_credentials():
    d = {}
    d['version'] = '2'
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    return d


def get_keystone_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL'].replace('v2.0', 'v3')
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d


def get_keystone_client():
    creds = get_keystone_credentials()
    kc = keystone_client(**creds)
    return kc


def get_nova_client():
    creds = get_nova_credentials()
    nc = nova_client(**creds)
    return nc


def get_host_instances(nc, host):
    search_options = {'host': host, 'all_tenants': 1, 'status': 'SHUTOFF'}
    instances = nc.servers.list(search_opts=search_options)
    return instances


def get_last_action(nc, instance):
    last_actions = instance_action.InstanceActionManager(nc).list(instance.id)
    return last_actions[0]


def find_tenant_manager_role(kc):
    roles = kc.roles.list()
    for r in roles:
        if r.name == "TenantManager":
            return r.id


def get_tenant_managers(kc, tenant_id):
    role_assignments = kc.role_assignments.list(project=tenant_id)
    tm_role = find_tenant_manager_role(kc)
    tenant_manager_ids = []
    for ra in role_assignments:
        if ra.role['id'] == tm_role:
            tenant_manager_ids.append(ra.user['id'])
    if len(tenant_manager_ids) == 0:
        print "Tenant %s has no managers!" % (tenant_id)
    tenant_managers = []
    for tm in tenant_manager_ids:
        user = kc.users.get(tm)
        tenant_managers.append(user)
    return tenant_managers


def get_tenant(kc, tenant_id):
    tenant = kc.projects.get(tenant_id)
    return tenant


def get_flavor(nc, instance):
    flavor = nc.flavors.get(instance.flavor['id'])
    return flavor.name


def is_instance_to_be_expired(nc, instance):
    six_months_ago = datetime.now() - relativedelta(days=180)
    last_action = get_last_action(nc, instance)
    if last_action.action != 'stop':
        return False
    action_date = datetime.strptime(last_action.start_time, ACTION_DATE_FORMAT)
    if action_date < six_months_ago:
        return True
    return False


def process_host(nc, host):
    instances = get_host_instances(nc, host)
    for_expiry = []
    for instance in instances:
        if is_instance_to_be_expired(nc, instance):
            for_expiry.append(instance)
    return for_expiry


def main():
    # nothing interesting here - just a list of hosts on the command line
    if len(sys.argv) <= 1:
        print "Usage: %s <host> [<host>....]" % (sys.argv[0])
        sys.exit(1)

    nc = get_nova_client()
    kc = get_keystone_client()
    instances = []
    for host in sys.argv[1:]:
        instances.extend(process_host(nc, host))

    results = {}
    for instance in instances:
        if instance.tenant_id in results:
            results[instance.tenant_id]['instances'].append(instance)
        else:
            results[instance.tenant_id] = {
                'tenant': get_tenant(kc, instance.tenant_id),
                'managers': get_tenant_managers(kc, instance.tenant_id),
                'instances': [instance],
            }

    for result in results.values():
        print "Tenant %s:" % (result['tenant'].name)
        print "  Managers:"
        for manager in result['managers']:
            print "    Manager email: %s" % (manager.email)
        print "  Instances:"
        for instance in result['instances']:
            flavor = get_flavor(nc, instance)
            print "    %s (uuid %s, flavor %s)" % (instance.name, instance.id, flavor)


if __name__ == '__main__':
    main()
