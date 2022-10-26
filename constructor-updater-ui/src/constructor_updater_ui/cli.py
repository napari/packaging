"""Constuctor updater UI CLI."""

import argparse

from constructor_updater_ui.main import main


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=str)
    args = parser.parse_args()
    main(args.package)


if __name__ == "__main__":
    run()
