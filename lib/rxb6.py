#!/usr/bin/env python3
#
# RXB6 class and helpers
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

import signal
import sys
import time

BIT0_MIN = 2000
BIT0_MAX = 3500

BIT1_MIN = 4000
BIT1_MAX = 5500


def decode(dataset):
    """
    Decode a dataset
    """
    # We only care about the 3rd column which contains the widths of the
    # individual high and low pulses
    widths = [d[2] if len(d) == 3 else 0 for d in dataset]

    # Ignore the last pulse width if the list has an odd length
    if len(widths) % 2:
        widths = widths[:-1]

    # Sum the widths of consecutive low and high pulses to create the list of
    # bit widths
    bits = [int(widths[i]) + int(widths[i+1]) for i in range(0, len(widths), 2)]
    num_bits = len(bits)

    if num_bits < 36:
        print("Error: Not enough bits (%d)" % num_bits)
        return None

    # Decode the individual bits
    data = 0
    for b in bits:
        data = data << 1
        if b > BIT0_MIN and b < BIT0_MAX:
            pass
        elif b > BIT1_MIN and b < BIT1_MAX:
            data = data | 1
        else:
            print("Error: Invalid bit width (%d)" % b)
            return None

    # And finally pull the sensor data out
    sensor = (data >> (num_bits - 12)) & 0xfff
    test = (data >> (num_bits - 14)) & 0x1
    channel = ((data >> (num_bits - 16)) & 0x3) + 1
    temperature = ((data >> (num_bits - 28)) & 0xfff) / 10
    humidity = (data >> (num_bits - 36)) & 0xff

    result = {
        "timestamp": int(time.time()),
        "sensor": sensor,
        "test": test,
        "channel": channel,
        "temperature": temperature,
        "humidity": humidity,
    }

    return result


def _timeout_handler(_signum, _frame):
    """
    Timeout handler
    """
    # Python3 stderr is likely buffered
    sys.stderr.flush()
    raise TimeoutError


class RXB6(object):
    """
    Simple RXB6 class
    """
    def __init__(self, device):
        self.device = device

    def read(self, timeout=0):
        """
        Read and return raw data from the device
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
                        if data and len(data) > 1:
                            # Drop the first element (sync pulse)
                            yield data[1:]
                        data = []
                        continue

                    if "END" in line or "ERR" in line:
                        data = []
                        continue

                    if record:
                        data.append(line.split(' '))

        except TimeoutError:
            pass
        finally:
            if orig:
                # Reinstall the original signal handler and cancel the alarm
                signal.signal(signal.SIGALRM, orig)
                signal.alarm(0)

    def read_decoded(self, timeout=0):
        """
        Read and return decode data from the device
        """
        for data in self.read(timeout=timeout):
            yield decode(data)