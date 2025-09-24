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

import re
import os.path
import time

from provider import write_providers_site
from currency import read_currencies_data, write_currencies_site
from quote import read_quotelist_data, write_year_quotes_site


def build_command(args):
    """
    build_command implements the fx build command.
    """
    args.logger.debug("running build")

    write_providers_site(args.site_dir, args.provider, args.logger)

    currencies_proto_path = os.path.join(args.data_dir, "currencies.binpb")
    currencies = read_currencies_data(currencies_proto_path, args.logger)

    write_currencies_site(args.site_dir, currencies, args.logger)

    build_start = time.time()
    for provider in args.provider:
        provider_data_dir = os.path.join(args.data_dir, provider.code)
        for root, dirs, files in os.walk(provider_data_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                match = re.match(
                    r"^"
                    + re.escape(provider_data_dir)
                    + r"/([a-zA-Z]{3})/([a-zA-Z]{3})/([0-9]{4}).binpb$",
                    file_path,
                )
                if match:
                    base_currency_code = match.group(1)
                    quote_currency_code = match.group(2)
                    year = int(match.group(3))

                    args.logger.info(
                        f"building {base_currency_code}/{quote_currency_code} for {year}..."
                    )

                    quotelist = read_quotelist_data(file_path, args.logger)

                    base_dir = os.path.join(
                        args.site_dir,
                        f"provider/{provider.code}/quote/{base_currency_code}/{quote_currency_code}",
                    )
                    write_year_quotes_site(base_dir, year, quotelist, args.logger)
    build_end = time.time()

    args.logger.info(f"API built in {build_end - build_start:.2f} seconds")
