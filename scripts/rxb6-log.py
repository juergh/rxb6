#!/usr/bin/env python3
#
# Collect RXB6 sensor data and log it to a database
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

import argparse
import os
import sqlite3
import sys

from lib.rxb6 import RXB6


def create_db(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE data (timestamp INTEGER, name TEXT, "
                    "temperature REAL, humidity REAL)")
        con.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="The sensor config file to use.")
    parser.add_argument("db", help="The database file to write the data to.")

    args = parser.parse_args()

    # Read data for 90 seconds and average it
    data = RXB6("/dev/rxb6", config=args.config).read_average(90)
    if not data:
        return 1

    # Create the database if it doesn't exist
    if not os.path.exists(args.db):
        create_db(args.db)

    # Write the data to the database
    with sqlite3.connect(args.db) as con:
        cur = con.cursor()
        for d in data:
            cur.execute("INSERT INTO data (timestamp, name, temperature, "
                        "humidity) VALUES (:timestamp, :name, :temperature, "
                        ":humidity)", d)
        con.commit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
