#!/usr/bin/env python
#
# Take a list of instance UUIDs and check their status. If the last activity
# recorded for them is more than six months ago mark them as defunct.

import sys
from util import get_nova_client, get_keystone_client
from util import get_instance, is_instance_to_be_expired
from util import output_report


def main():
    if len(sys.argv) <= 1:
        print "Usage: %s <instance uuid> [<instance uuid>...}" % (sys.argv[0])
        sys.exit(1)

    nc = get_nova_client()
    kc = get_keystone_client()
    instances = []
    for uuid in sys.argv[1:]:
        instance = get_instance(nc, uuid)
        if instance is None:
            print "Instance %s not found" % (uuid)
        else:
            if is_instance_to_be_expired(nc, instance, days=190):
                instances.append(instance)

    output_report(nc, kc, instances)


if __name__ == '__main__':
    main()
