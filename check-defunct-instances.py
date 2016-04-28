#!/usr/bin/env python
#
# Take a list of instance UUIDs and check their status. If the last activity
# recorded for them is more than six months ago mark them as defunct.

import sys
from util import get_nova_client, get_keystone_client
from util import get_instance, is_instance_to_be_expired
from util import output_report
from util import parse_common_args


def main():

    args = parse_common_args()

    nc = get_nova_client()
    kc = get_keystone_client()
    instances = []
    for uuid in args.hosts:
        instance = get_instance(nc, uuid)
        if instance is None:
            print "Instance %s not found" % (uuid)
        else:
            if is_instance_to_be_expired(nc, instance, days=args.days):
                instances.append(instance)

    output_report(nc, kc, instances)


if __name__ == '__main__':
    main()
