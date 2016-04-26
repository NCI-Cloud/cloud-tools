# cloud-tools
Assorted tools created at NCI for managing our OpenStack cloud

Currently in this repository:

find-wasted-resources.py: find instances that have been stopped for longer than
six months and output enough information to manually contact the owners.
check-defunct-instances.py: given a list of instance UUIDs, check to see if
they're still defunct or not. If so, then output the same format report.
