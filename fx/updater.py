#!/usr/bin/python
#
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

import argparse
import logging
from datetime import date

from currency import update_currencies
from quote import update_quotes


def main():
    today = date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="Start date", type=date.fromisoformat, default=today.strftime("%Y-%m-%d"))
    parser.add_argument("--end", help="End date", type=date.fromisoformat, default=today.strftime("%Y-%m-%d"))
    parser.add_argument("--out", help="Output directory", type=str, default="_site/v1")
    parser.add_argument("--debug", help="enable debug", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig()
    logger = logging.getLogger("update_jpy")
    logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    currencies = update_currencies(args.out, logger)
    update_quotes(args.out, args.start, args.end, currencies, logger)


if __name__ == "__main__":
    main()
