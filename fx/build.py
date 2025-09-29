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

import datetime
import os.path
import re
import time

from fx.provider import write_providers_site
from fx.currency import read_currencies_data, write_currencies_site
from fx.quote import (
    read_quotelist_data,
    write_latest_quote_site,
    write_year_quotes_site,
)


def update_latest_quotes(latest_quotes, provider_code, quotelist):
    """
    update_latest_quotes updates the given latest_quotes dictionary with the
    quotes from the given quotelist.
    """
    for quote in quotelist.quotes:
        pair = (provider_code, quote.base_currency_code, quote.quote_currency_code)
        if pair not in latest_quotes:
            latest_quotes[pair] = quote
        else:
            existing_quote = latest_quotes[pair]
            if datetime.date(
                quote.date.year, quote.date.month, quote.date.day
            ) > datetime.date(
                existing_quote.date.year,
                existing_quote.date.month,
                existing_quote.date.day,
            ):
                latest_quotes[pair] = quote


def build_command(args):
    """
    build_command implements the fx build command.
    """
    args.logger.debug("running build")

    write_providers_site(args.site_dir, args.provider, args.logger)

    currencies_proto_path = os.path.join(args.data_dir, "currencies.binpb")
    currencies = read_currencies_data(currencies_proto_path, args.logger)

    write_currencies_site(args.site_dir, currencies, args.logger)

    latest_quotes = {}

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

                    update_latest_quotes(latest_quotes, provider.code, quotelist)

                    base_dir = os.path.join(
                        args.site_dir,
                        f"provider/{provider.code}/quote/{base_currency_code}/{quote_currency_code}",
                    )
                    write_year_quotes_site(base_dir, year, quotelist, args.logger)

    # Write the latest quotes for each currency pair.
    for (
        provider_code,
        base_currency_code,
        quote_currency_code,
    ), quote in latest_quotes.items():
        base_dir = os.path.join(
            args.site_dir,
            f"provider/{provider_code}/quote/{base_currency_code}/{quote_currency_code}",
        )
        write_latest_quote_site(base_dir, quote, args.logger)

    build_end = time.time()

    args.logger.info(f"API built in {build_end - build_start:.2f} seconds")
