#!/usr/bin/env python3
#
# Print raw decoded data
#

import time

from lib import rxb6


for data in rxb6.RXB6("/dev/rxb6").read_decoded():
    print("%s: %s" %(time.asctime(time.localtime()), data))
