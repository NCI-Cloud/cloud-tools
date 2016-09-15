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

from util import get_host_instances
from util import get_flavor
from util import get_tenant
from util import get_nova_client, get_keystone_client
from util import output_report
from util import parser_with_common_args


def parse_args():
    parser = parser_with_common_args()
    parser.add_argument("--m1", action='store_true', required=False,
                        default=False,
                        help="Show only m1 flavours")
    parser.add_argument("--pt", action='store_true', required=False,
                        default=False,
                        help="Show only PT tenants")

    return parser.parse_args()


def process_host(nc, kc, host, args):
    instances = get_host_instances(nc, host)
    for_display = []
    if args.m1:
        for instance in instances:
            f = get_flavor(nc, instance)
            if f[:2] == "m1":
                for_display.append(instance)
    elif args.pt:
        for instance in instances:
            t = get_tenant(kc, instance.tenant_id)
            if t.name[:3] == "pt-":
                for_display.append(instance)
    else:
        for_display = instances
    return for_display


def main():
    # nothing interesting here - just a list of hosts on the command line
    args = parse_args()

    nc = get_nova_client()
    kc = get_keystone_client()
    instances = []
    for host in args.hosts:
        instances.extend(process_host(nc, kc, host, args))

    output_report(nc, kc, instances)


if __name__ == '__main__':
    main()
