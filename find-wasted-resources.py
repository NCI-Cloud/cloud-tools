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

import sys
from util import get_host_instances, is_instance_to_be_expired
from util import get_nova_client, get_keystone_client
from util import output_report


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

    output_report(nc, kc, instances)


if __name__ == '__main__':
    main()
