# Copyright 2025 Ian Lewis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The main fx program entrypoint."""

import argparse
import datetime
import logging

from fx.build import build_command
from fx.mufg import MUFGProvider
from fx.update import update_command


def main() -> None:
    """Execute the main fx program entrypoint."""
    today = datetime.datetime.now(tz=datetime.UTC).date()

    logging.basicConfig()
    logger = logging.getLogger("fx")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        help="enable debug",
        action="store_true",
        default=False,
    )
    parser.set_defaults(func=lambda _args: parser.print_help(), logger=logger)

    subparsers = parser.add_subparsers(help="subcommand help")

    provider_map = {
        MUFGProvider.code: MUFGProvider,
    }
    all_providers = provider_map.values()

    def provider_code(arg: str) -> type:
        """Convert a provider code to a provider class."""
        if arg in provider_map:
            return provider_map[arg]

        msg = "invalid provider: {!r} (choose from {})"
        choices = ", ".join(sorted(repr(choice) for choice in provider_map))
        raise argparse.ArgumentTypeError(msg.format(arg, choices))

    update = subparsers.add_parser("update", help="Update currency exchange data")
    update.add_argument(
        "--provider",
        nargs="*",
        help="update these providers",
        type=provider_code,
        default=all_providers,
    )
    update.add_argument(
        "--start",
        help="update dating starting with this date",
        type=datetime.date.fromisoformat,
        default=today.strftime("%Y-%m-%d"),
    )
    update.add_argument(
        "--end",
        help="update data up to and including this date",
        type=datetime.date.fromisoformat,
        default=today.strftime("%Y-%m-%d"),
    )
    update.add_argument("--data-dir", help="data directory", type=str, default="data")
    update.add_argument(
        "--timeout",
        help="timeout for external requests in seconds",
        type=float,
        default=10.0,
    )
    update.add_argument(
        "--retry",
        help="number of retries for external equests",
        type=int,
        default=10,
    )
    # The backoff factor is multiplied by 2^n where n is the retry number
    # e.g. 0.5 will result in 0.5, 1, 2, 4, 8 seconds between retries
    update.add_argument(
        "--backoff",
        help="backoff factor for retries",
        type=int,
        default=0.5,
    )
    update.set_defaults(func=update_command, logger=logger)

    build = subparsers.add_parser("build", help="Build static API files")
    build.add_argument("--data-dir", help="data directory", type=str, default="data")
    build.add_argument(
        "--site-dir",
        help="site directory",
        type=str,
        default="_site/v1",
    )
    build.set_defaults(func=build_command, logger=logger, provider=all_providers)

    args = parser.parse_args()

    logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    args.func(args)


if __name__ == "__main__":
    main()
