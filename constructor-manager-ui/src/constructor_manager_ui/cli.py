"""Constuctor manager CLI."""

import argparse

from constructor_manager_ui.main import main


def run():
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
    parser.add_argument("--dev", "-d", action="store_true")
    args = parser.parse_args()
    main(args)


if __name__ == "__main__":
    run()
