#!/usr/bin/env python3
#
# Print RXB6 data
#

import argparse
import time

from lib import rxb6

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("choice",
                        choices=["raw", "filtered", "decoded", "averaged"],
                        help="Print 'raw, 'decoded' or 'averaged' data")
    parser.add_argument("-d", "--duration", type=int, default=90,
                        help="Duration in seconds for averaging data. "
                        "Defaults to '90' if not set.")

    args = parser.parse_args()

    if args.choice == "raw":
        with open("/dev/rxb6", "r") as fh:
            for line in fh:
                data = line.strip()
                print("%s: %s" % (time.asctime(time.localtime()), data))

    elif args.choice == "filtered":
        for data in rxb6.RXB6("/dev/rxb6").read():
            print("%s: %s" % (time.asctime(time.localtime()), data))

    elif args.choice == "decoded":
        for data in rxb6.RXB6("/dev/rxb6").read_decoded():
            print("%s: %s" % (time.asctime(time.localtime()), data))

    else:
        while True:
            for data in rxb6.RXB6("/dev/rxb6").read_averaged(args.duration):
                print("%s: %s" % (time.asctime(time.localtime()), data))
