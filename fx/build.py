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

"""Build module for generating static API site files."""

import datetime
import re
import time
from pathlib import Path
from typing import Any

from fx.currency import read_currencies_data, write_currencies_site
from fx.provider import write_providers_site
from fx.quote import (
    read_quotelist_data,
    write_latest_quote_site,
    write_year_quotes_site,
)
from fx.v1.quote_pb2 import Quote, QuoteList  # type: ignore[attr-defined]


def update_latest_quotes(
    latest_quotes: dict[tuple[str, str, str], Quote],
    provider_code: str,
    quotelist: QuoteList,
) -> None:
    """
    Update the given latest_quotes dictionary with quotes from quotelist.

    Updates the given latest_quotes dictionary with the
    quotes from the given quotelist.
    """
    for quote in quotelist.quotes:
        pair = (provider_code, quote.base_currency_code, quote.quote_currency_code)
        if pair not in latest_quotes:
            latest_quotes[pair] = quote
        else:
            existing_quote = latest_quotes[pair]
            if datetime.date(
                quote.date.year,
                quote.date.month,
                quote.date.day,
            ) > datetime.date(
                existing_quote.date.year,
                existing_quote.date.month,
                existing_quote.date.day,
            ):
                latest_quotes[pair] = quote


def build_command(args: Any) -> None:  # noqa: ANN401
    """build_command implements the fx build command."""
    args.logger.debug("running build")

    site_dir_v1 = Path(args.site_dir).joinpath("v1")

    write_providers_site(site_dir_v1, args.provider, args.logger)

    currencies_proto_path = Path(args.data_dir).joinpath("currencies.binpb")
    currencies = read_currencies_data(currencies_proto_path, args.logger)

    write_currencies_site(site_dir_v1, currencies, args.logger)

    latest_quotes: dict[tuple[str, str, str], Quote] = {}

    build_start = time.time()
    for provider in args.provider:
        provider_data_path = Path(args.data_dir).joinpath(provider.code)
        for root, _dirs, files in provider_data_path.walk():
            for filename in files:
                file_path = Path(root).joinpath(filename)
                match = re.match(
                    r"^"
                    + re.escape(str(provider_data_path))
                    + r"/([a-zA-Z]{3})/([a-zA-Z]{3})/([0-9]{4}).binpb$",
                    str(file_path),
                )
                if match:
                    base_currency_code = match.group(1)
                    quote_currency_code = match.group(2)
                    year = int(match.group(3))

                    args.logger.info(
                        "building %s/%s for %s...",
                        base_currency_code,
                        quote_currency_code,
                        year,
                    )

                    quotelist = read_quotelist_data(str(file_path), args.logger)

                    update_latest_quotes(latest_quotes, provider.code, quotelist)

                    base_dir = site_dir_v1.joinpath(
                        "provider",
                        provider.code,
                        "quote",
                        base_currency_code,
                        quote_currency_code,
                    )

                    write_year_quotes_site(base_dir, year, quotelist, args.logger)

    # Write the latest quotes for each currency pair.
    for (
        provider_code,
        base_currency_code,
        quote_currency_code,
    ), quote in latest_quotes.items():
        base_dir = site_dir_v1.joinpath(
            "provider",
            provider_code,
            "quote",
            base_currency_code,
            quote_currency_code,
        )
        write_latest_quote_site(base_dir, quote, args.logger)

    build_end = time.time()

    args.logger.info("API built in %.2f seconds", build_end - build_start)
