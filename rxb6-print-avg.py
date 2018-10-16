#!/usr/bin/env python3
#
# Collect and average data for 90 seconds and print the results
#

import time

from lib import rxb6

while True:
    data = rxb6.average(rxb6.RXB6("/dev/rxb6").read_decoded(timeout=90))
    for key in sorted(data):
        print("%s: %s" % (time.asctime(time.localtime()), data[key]))
