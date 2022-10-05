"""Command line interface to constructor updater."""

import argparse


# conda-lock
# constructor-installation-manager
# constructor-updater
# Todo lo hacemos con el constructor installation mamanger y eventualmente napari llamará a ese UI para hacer
# el manejo de los plugins
def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description="Constructor application updater.")
    parser.add_argument(
        "action",  # check, download, update, remove, clean
        help="conda package name",
    )
    parser.add_argument(
        "-cv",
        "--current-version",
        dest="current_version",
        help="Current application version",
    )
    parser.add_argument(
        "--package",
        dest="package_name",
        help="conda package name",
    )
    parser.add_argument(
        "--channel",
        dest="channel",
        help="conda channel",
        default="conda-forge",
    )
    parser.add_argument(
        "-p",
        "--plugins",
        nargs="*",
        help="Channel and Plugin to install",
    )
    args = parser.parse_args()
    print(args)


# parent_parser = argparse.ArgumentParser(add_help=False)
# parent_parser.add_argument('--user', '-u',
#                     default=getpass.getuser(),
#                     help='username')
# parent_parser.add_argument('--debug', default=False, required=False,
#                         action='store_true', dest="debug", help='debug flag')
# main_parser = argparse.ArgumentParser()
# service_subparsers = main_parser.add_subparsers(title="service",
#                     dest="service_command")
# service_parser = service_subparsers.add_parser("first", help="first",
#                     parents=[parent_parser])
# action_subparser = service_parser.add_subparsers(title="action",
#                     dest="action_command")
# action_parser = action_subparser.add_parser("second", help="second",
#                     parents=[parent_parser])

# args = main_parser.parse_args()


if __name__ == "__main__":
    main()
