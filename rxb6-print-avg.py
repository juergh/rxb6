#!/usr/bin/env python3
#
# Collect and average data for 90 seconds and print the results
#

import time

from lib import rxb6


while True:
    # Read data for 90 seconds
    data = [d for d in rxb6.RXB6("/dev/rxb6").read_decoded(timeout=90)]

    # Split the data into lists for the individual sensors
    sensor = {}
    for d in data:
        key = "%s:%s" % (d["sensor"], d["channel"])
        if key not in sensor:
            sensor[key] = []
        sensor[key].append(d)

    # Calculate the averages for the individual sensors and print the data
    for key in sorted(sensor):
        temperature = sum(s["temperature"] for s in sensor[key]) / len(sensor[key])
        humidity = sum(s["humidity"] for s in sensor[key]) / len(sensor[key])

        print("%s: sensor %s, temperature %.1f, humidity %.1f" %
              (time.asctime(time.localtime()), key, temperature, humidity))
