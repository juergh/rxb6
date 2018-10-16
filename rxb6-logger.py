#!/usr/bin/env python3
#
# Collect data and log it to a database
#

import argparse
import os
import sqlite3
import sys

from lib import rxb6


def create_db(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE data (timestamp INTEGER, sensor TEXT, "
                    "temperature REAL, humidity REAL)")
        con.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="The database file to write the data to.")

    args = parser.parse_args()

    # Read data for 90 seconds and average it
    data = rxb6.average(rxb6.RXB6("/dev/rxb6").read_decoded(timeout=90))
    if not data:
        print("Error: No data")
        return 1

    # Create the database if it doesn't exist
    if not os.path.exists(args.db):
        create_db(args.db)

    # Write the data to the database
    with sqlite3.connect(args.db) as con:
        cur = con.cursor()
        for d in data:
            cur.execute("INSERT INTO data (timestamp, sensor, temperature, "
                        "humidity) VALUES (:timestamp, :sensor, :temperature, "
                        ":humidity)", d)
        con.commit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
