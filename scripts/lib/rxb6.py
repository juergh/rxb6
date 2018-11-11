#!/usr/bin/env python3
#
# RXB6 class and helpers
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

import logging
import signal
from socket import gethostname
import sys
import time
import yaml

from lib import sensors


logging.basicConfig(level=logging.INFO, format="%(asctime)s " +
                    gethostname() + " rxb6: %(message)s",
                    datefmt="%b %d %H:%M:%S")


def average_data(data):
    """
    Average decoded sensor data
    """
    # Split the data into lists for the individual sensors
    sensor = {}
    for d in data:
        key = d["name"]
        if key not in sensor:
            sensor[key] = []
        sensor[key].append(d)

    # Calculate the averages for the individual sensors
    result = []
    for key in sorted(sensor):
        result.append({
            "timestamp": sensor[key][0]["timestamp"],
            "name": key,
            "temperature": int((sum(s["temperature"] for s in sensor[key]) /
                                len(sensor[key])) * 10 + 0.5) / 10,
            "humidity": int((sum(s["humidity"] for s in sensor[key]) /
                             len(sensor[key])) * 10 + 0.5) / 10,
        })

    return result


def decode_set(dataset):
    """
    Decode a sensor data set and return a data record

    A data set is a list of sensor records returned by the rxb6 device. Each
    sensor record is a tuple with three elements:
      1. timestamp (seconds since the epoch)
      2. pulse level (0 or 1)
      3. pulse width (in microseconds)

    The returned data record is a tuple with three elements:
      1. timestamp (seconds since the epoch)
      2. decoded data
      3. number of bits
    """
    # Pull out the widths of the individual pulses
    widths = [d[2] if len(d) == 3 else 0 for d in dataset]

    # Ignore the last pulse width if the list has an odd length
    if len(widths) % 2:
        widths = widths[:-1]

    # Sum the widths of consecutive low and high pulses to create the list of
    # bit widths
    bits = [int(widths[i]) + int(widths[i+1]) for i in range(0, len(widths), 2)]
    num_bits = len(bits)

    # Decode the individual bits
    data = 0
    for b in bits:
        data = data << 1
        if sensors.is_bit0(b):
            pass
        elif sensors.is_bit1(b):
            data = data | 1
        else:
            logging.warning("Invalid bit width (%d)", b)
            return None

    return (dataset[0][0], data, num_bits)


def _timeout_handler(_signum, _frame):
    """
    Timeout handler
    """
    # Python3 stderr is likely buffered
    sys.stderr.flush()
    raise TimeoutError


class RXB6(object):
    """
    Simple rxb6 class
    """
    def __init__(self, device, config=None):
        self.device = device
        self.config = None
        if config:
            with open(config) as fh:
                self.config = yaml.load(fh)

    def read(self, timeout=0):
        """
        Read and return sensor data sets
        """
        orig = None
        if timeout:
            # Install our timeout handler and arm the alarm
            orig = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout)

        try:
            with open(self.device) as fh:
                record = False
                data = []

                for line in fh:
                    line = line.strip()

                    if "SYNC" in line:
                        record = True
                        if data and len(data) > 2:
                            # Drop the first two elements (sync pulse)
                            yield data[2:]
                        data = []
                        continue

                    if "END" in line or "ERR" in line:
                        data = []
                        continue

                    if record:
                        # Prepend a timestamp to the line and append the record
                        # to the collected data
                        data.append([int(time.time())] + line.split(' '))

        except TimeoutError:
            pass
        finally:
            if orig:
                # Reinstall the original signal handler and cancel the alarm
                signal.signal(signal.SIGALRM, orig)
                signal.alarm(0)

    def read_record(self, timeout=0):
        """
        Read and return data records
        """
        for dataset in self.read(timeout=timeout):
            datarecord = decode_set(dataset)
            if datarecord:
                yield datarecord

    def read_decoded(self, timeout=0):
        """
        Read and return decoded data records
        """
        for datarecord in self.read_record(timeout=timeout):
            decoded = sensors.decode(datarecord, self.config)
            if decoded:
                yield decoded

    def read_average(self, timeout):
        """
        Read and return averaged data
        """
        return average_data(self.read_decoded(timeout=timeout))

    def scan(self, timeout=0):
        """
        Scan for (new) sensors
        """
        for datarecord in self.read_record(timeout=timeout):
            data = sensors.identify(datarecord)
            if data:
                for d in data:
                    yield d
