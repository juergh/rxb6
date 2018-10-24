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
                        choices=["raw", "record", "decoded", "averaged"],
                        help="Print 'raw, 'record', 'decoded' or 'averaged' "
                        " data")
    parser.add_argument("-d", "--duration", type=int, default=90,
                        help="Duration in seconds for averaging data. "
                        "Defaults to '90' if not set.")
    parser.add_argument("-b", "--binary", action="store_true",
                        help="Display the record data in binary format.")

    args = parser.parse_args()

    if args.choice == "raw":
        for data in rxb6.RXB6("/dev/rxb6").read():
            print("%s: %s" % (time.asctime(time.localtime()), data))

    elif args.choice == "record":
        for data in rxb6.RXB6("/dev/rxb6").read_record():
            if args.binary:
                print("%s: %s %s %s" % (time.asctime(time.localtime()), data[0],
                                        format(data[1], "0%db" % data[2]),
                                        data[2]))
            else:
                print("%s: %s" % (time.asctime(time.localtime()), data))

    elif args.choice == "decoded":
        for data in rxb6.RXB6("/dev/rxb6").read_decoded():
            print("%s: %s" % (time.asctime(time.localtime()), data))

    else:
        while True:
            for data in rxb6.RXB6("/dev/rxb6").read_average(args.duration):
                print("%s: %s" % (time.asctime(time.localtime()), data))
