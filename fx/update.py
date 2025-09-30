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

"""
The Update Command.

This module defines the update command which is used to update the local data store
with currency and quote data from the specified providers.
"""

from datetime import date
from pathlib import Path

from dateutil.relativedelta import relativedelta

from fx.currency import download_currencies, write_currencies_data
from fx.quote import download_quotes, write_quotes_data
from fx.utils import date_iterator


def update_command(args: any) -> None:
    """
    Update the local currency and quote data.

    This comand downloads currency and quote data given the command line arguments
    and stores them in the specified data directory.
    """
    args.logger.debug("running update")

    Path.mkdir(args.data_dir, exist_ok=True)

    data_path = Path(args.data_dir)

    # Update currencies
    # Data is stored in data/currencies.binpb
    currencies_proto_path = data_path.joinpath("currencies.binpb")
    write_currencies_data(currencies_proto_path, download_currencies(args), args.logger)

    # Update quotes

    # Process the date range by year
    for Provider in args.provider:  # noqa: N806 // Provider is a class
        provider = Provider(args)
        for year_start in date_iterator(
            date(args.start.year, 1, 1),
            args.end,
            relativedelta(years=1),
        ):
            for base_currency_code in provider.supported_base_currencies:
                for quote_currency_code in provider.supported_quote_currencies:
                    start_date = year_start
                    if args.start.year == year_start.year:
                        start_date = args.start

                    end_date = date(year_start.year, 12, 31)
                    if args.end.year == year_start.year:
                        end_date = args.end

                    quotes = download_quotes(
                        provider,
                        base_currency_code,
                        quote_currency_code,
                        start_date,
                        end_date,
                        args.logger,
                    )

                    # Data will be stored in files of the form:
                    #   data/MUFG/USD/JPY/2025.binpb
                    quotes_proto_path = data_path.joinpath(
                        provider.code,
                        base_currency_code,
                        quote_currency_code,
                        f"{year_start.year}.binpb",
                    )
                    write_quotes_data(quotes_proto_path, quotes, args.logger)
