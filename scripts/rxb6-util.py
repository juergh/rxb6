#!/usr/bin/env python3
#
# RXB6 utility
#

import argparse
import sqlite3
import sys

from lib import rxb6


def _dec(name, *args, **kwargs):
    """
    Decorator for subcommand arguments and help text
    """
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault(name, []).insert(0, (args, kwargs))
        return func
    return _decorator


def add_help(*args, **kwargs):
    return _dec("help", *args, **kwargs)


def add_arg(*args, **kwargs):
    return _dec("arg", *args, **kwargs)


@add_help("dump a database")
@add_arg("db", help="path to the database")
def do_dump(args):
    """
    Dump a database
    """
    with sqlite3.connect(args.db) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM data")
        for row in cur.fetchall():
            print(row)


@add_help("print sensor data")
@add_arg("type", choices=("raw", "record", "decoded", "average"),
         help="print the specified data")
@add_arg("-c", "--config", help="sensor configuration file (required for "
         "'decoded' and 'average').")
@add_arg("-d", "--duration", type=int, default=90, help="sampling duration in "
         "seconds (only used for 'average'). Defaults to 90 if not set.")
@add_arg("-b", "--binary", action="store_true", help="print the data in "
         "binary format (only used for 'record').")
def do_print(args):
    _rxb6 = rxb6.RXB6("/dev/rxb6", config=args.config)
    if args.type == "raw":
        for data in _rxb6.read():
            rxb6.logger.info(data)

    elif args.type == "record":
        for data in _rxb6.read_record():
            if args.binary:
                rxb6.logger.info("%s %s %s", data[0],
                                 format(data[1], "0%db" % data[2]), data[2])
            else:
                rxb6.logger.info(data)

    elif args.type == "decoded":
        for data in _rxb6.read_decoded():
            rxb6.logger.info(data)

    else:
        while True:
            for data in _rxb6.read_average(args.duration):
                rxb6.logger.info(data)


def add_subcommand_parsers(subparser):
    """
    Add parsers for the subcommands
    """
    module = sys.modules[__name__]

    # Walk through the 'do_' functions
    for attr in (a for a in dir(module) if a.startswith("do_")):
        cmd_name = attr[3:].replace('_', '-')
        cmd_cb = getattr(module, attr)
        cmd_desc = cmd_cb.__doc__ or ""
        cmd_help = getattr(cmd_cb, "help", [])
        cmd_args = getattr(cmd_cb, "arg", [])

        parser = subparser.add_parser(cmd_name, help=cmd_help[0][0][0],
                                      description=cmd_desc, add_help=False)
        parser.add_argument("-h", "--help", action="help")
        for (args, kwargs) in cmd_args:
            parser.add_argument(*args, **kwargs)
        parser.set_defaults(func=cmd_cb)


if __name__ == "__main__":
    # Create the parser and add the subparsers for the subcommands
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title="commands")
    add_subcommand_parsers(subparser)

    # Parse the arguments and call the subcommand
    args = parser.parse_args()
    command = getattr(args, "func", None)
    if not command:
        parser.print_usage()
        sys.exit(2)
    command(args)
