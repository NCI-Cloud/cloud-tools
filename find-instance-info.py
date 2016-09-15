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
    parser.add_argument("--m2", action='store_true', required=False,
                        default=False,
                        help="Show only m2 flavours")
    parser.add_argument("--regular", action='store_true', required=False,
                        default=False,
                        help="Show only full tenants")
    parser.add_argument("--show-all-categories", action='store_true',
                        required=False,
                        default=False,
                        help=(
                            "Output all categories of instance, grouped by"
                            "project"
                        ))

    return parser.parse_args()


def process_host(nc, kc, host):
    instances = get_host_instances(nc, host)

    # categorisation functions
    # Note: these are here so that they can access nc and kc. If they
    # ever move into a class or similar they can become normal methods
    def is_m1(instance):
        f = get_flavor(nc, instance)
        if f[:2] == "m1":
            return True
        return False

    def is_m2(instance):
        f = get_flavor(nc, instance)
        if f[:2] == "m2":
            return True
        return False

    def is_pt(instance):
        t = get_tenant(kc, instance.tenant_id)
        if t.name[:3] == "pt-":
            return True
        return False

    def is_regular(instance):
        if not is_pt(instance):
            return True
        return False

    categories = {
        'm1': is_m1,
        'm2': is_m2,
        'pt': is_pt,
        'regular': is_regular,
    }

    groupings = {}

    for instance in instances:
        for category in categories.keys():
            if categories[category](instance):
                if category not in groupings:
                    groupings[category] = []
                groupings[category].append(instance)

    return groupings


def main():
    # nothing interesting here - just a list of hosts on the command line
    args = parse_args()

    nc = get_nova_client()
    kc = get_keystone_client()
    groupings = {}
    for host in args.hosts:
        new_groupings = process_host(nc, kc, host)
        for category in new_groupings.keys():
            if category not in groupings:
                groupings[category] = []
            groupings[category].extend(new_groupings[category])

    categories = groupings.keys()
    categories.sort()
    for category in categories:
        if getattr(args, "show_all_categories") or getattr(args, category):
            print("Category %s" % (category))
            output_report(nc, kc, groupings[category])


if __name__ == '__main__':
    main()
