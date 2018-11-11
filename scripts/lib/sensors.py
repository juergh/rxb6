#!/usr/bin/env python3
#
# Sensor decoders
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

BIT0_MIN = (0.9 * 2410)
BIT0_MAX = (1.1 * 2960)

BIT1_MIN = (0.9 * 4450)
BIT1_MAX = (1.1 * 5120)


# -----------------------------------------------------------------------------
# Helpers

def twos_complement(val, bits):
    """
    Calculate the 2's complement
    """
    if val & (1 << (bits - 1)):
        # Return negative value if sign bit is set
        val = val - (1 << bits)
    return val


def is_sensor(test_mode, channel, temperature):
    """
    Check if the data is sane
    """
    return (test_mode == 1 and channel == 2 and temperature > 15 and
            temperature < 35)


def is_bit0(width):
    """
    Return true if the pulse width falls within the Bit0 range
    """
    return (width > BIT0_MIN) and (width < BIT0_MAX)


def is_bit1(width):
    """
    Return true if the pulse width falls within the Bit1 range
    """
    return (width > BIT1_MIN) and (width < BIT1_MAX)


# -----------------------------------------------------------------------------
# Sensor decoders

def digoo_r8s(datarecord, identify=False):
    """
    Digoo R8S

    Pulse widths (usecs):
      Pulse type             Mean     Min     Max
      -------------------------------------------
      Sync pulse:            8990    8870    9090
      End pulse:                   437591
      Low pulse:              590     470     700
      High pulse (short):    2030    1940    2260
      High pulse (long):     4080    3980    4190
      -------------------------------------------
      Bit0:                  2620    2410    2960
      Bit1:                  4670    4450    4890

    Bits: DDDD RRRRRRRR B M CC TTTTTTTTTTTT HHHHHHHH Z
          4    8        1 1 2  12           8        1 == 37

    D: Device ID (1001)
    R: Random device ID (changes on reset)
    B: Battery status (0=good, 1=bad)
    M: Test mode (0=no, 1=yes)
    C: Channel (00=ch1, 01=ch2, 10=ch3)
    T: Temperature in 0.1 Celcius (2s complement)
    H: Humidity in percent
    Z: Trailer bit (0)
    """
    timestamp, data, num_bits = datarecord

    if num_bits != 37:
        return None

    sensor_id = (data >> 25) & 0xfff
    battery_status = (data >> 24) & 0x1
    test_mode = (data >> 23) & 0x1
    channel = (data >> 21) & 0x3
    temperature = twos_complement((data >> 9) & 0xfff, 12) / 10
    humidity = (data >> 1) & 0xff

    if identify:
        if ((data >> 33) & 0xf) != 9:
            return None
        if not is_sensor(test_mode, channel, temperature):
            return None

    result = {
        "timestamp": timestamp,
        "sensor": "r8s:%s:%s" % (sensor_id, channel),
        "sensor_id": sensor_id,
        "battery_status": battery_status,
        "test_mode": test_mode,
        "channel": channel,
        "temperature": temperature,
        "humidity": humidity
    }

    return result


def globaltronics_gt_wt_02(datarecord, identify=False):
    """
    Globaltronics GT-WT-02

    Pulse widths (usecs):
      Pulse type             Mean     Min     Max
      -------------------------------------------
      Sync pulse:            9010    8020    9120
      End pulse:                    16559
      Low pulse:              570     450     720
      High pulse (short):    2070    1910    2200
      High pulse (long):     4110    3990    4230
      -------------------------------------------
      Bit0:                  2640    2360    2920
      Bit1:                  4680    4440    5120

    Bits: RRRRRRRR B M CC TTTTTTTTTTTT HHHHHHH XXXXX Z
          8        1 1 2  12           7       5     1 == 37

    R: Random device ID (changes on reset)
    B: Battery status (0=good, 1=bad)
    M: Test mode (0=no, 1=yes)
    C: Channel (00=ch1, 01=ch2, 10=ch3)
    T: Temperature in 0.1 Celcius (2s complement)
    H: Humidity in percent
    X: Checksum
    Z: Trailer bit (0)
    """
    timestamp, data, num_bits = datarecord

    if num_bits != 37:
        return None

    sensor_id = (data >> 29) & 0xfff
    battery_status = (data >> 28) & 0x1
    test_mode = (data >> 27) & 0x1
    channel = (data >> 25) & 0x3
    temperature = twos_complement((data >> 13) & 0xfff, 12) / 10
    humidity = (data >> 1) & 0x7f

    if identify:
        if not is_sensor(test_mode, channel, temperature):
            return None

    result = {
        "timestamp": timestamp,
        "sensor": "gt-wt-02:%s:%s" % (sensor_id, channel),
        "sensor_id": sensor_id,
        "battery_status": battery_status,
        "test_mode": test_mode,
        "channel": channel,
        "temperature": temperature,
        "humidity": humidity
    }

    return result


SENSORS = (
    digoo_r8s,
    globaltronics_gt_wt_02
)


# -----------------------------------------------------------------------------
# Public methods

def identify(datarecord):
    """
    Identify a sensor
    """
    sensor_data = []
    for sensor_decoder in SENSORS:
        data = sensor_decoder(datarecord, identify=True)
        if data:
            sensor_data.append(data)
    return sensor_data


def decode(datarecord, sensor_config):
    """
    Decode sensor data
    """
    if not sensor_config:
        # If sensor_config is None, run the datarecord through all decoders
        # and return the list of decoded data
        sensor_data = []
        for sensor_decoder in SENSORS:
            data = sensor_decoder(datarecord)
            if data:
                sensor_data.append(data)
        return sensor_data

    for sensor_decoder in SENSORS:
        data = sensor_decoder(datarecord)
        if data:
            sensor = data["sensor"]
            if sensor in sensor_config:
                data["name"] = sensor_config[sensor]
                return data
    return None
