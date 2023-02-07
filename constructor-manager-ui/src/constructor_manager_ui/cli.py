"""Constuctor manager CLI."""

import argparse


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=str)

    parser.add_argument(
        "--current-version",
        "-cv",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--build-string",
        help="increase output verbosity",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--plugins-url",
        "-pu",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--channel",
        "-c",
        action="append",
        default=None,
    )
    parser.add_argument(
        "--log",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument("--dev", "-d", action="store_true")
    return parser
