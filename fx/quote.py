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
Quote related functions.

This module defines functions for downloading, reading, writing, and managing
currency exchange quotes.
"""

import csv
import datetime
import json
import logging
from collections import defaultdict
from pathlib import Path

from dateutil.relativedelta import relativedelta
from google.protobuf.json_format import MessageToDict

from fx.quote_pb2 import Quote, QuoteList
from fx.utils import date_iterator, date_msg_to_str, money_to_str


def quote_in(q: Quote, quotes: list[Quote]) -> bool:
    """
    Check if a quote is in a list of quotes.

    It returns True if the given quote object has a matching quote in
    the given list of quotes.
    """
    return any(quote_equal(q, q2) for q2 in quotes)


def quote_equal(q1: Quote, q2: Quote) -> bool:
    """
    Check if two quotes are equal.

    quote_equal returns if two quotes are quotes from the same provider, for
    the same day, for the same currency pair.
    """
    return (
        q1.provider_code == q2.provider_code
        and q1.date.year == q2.date.year
        and q1.date.month == q2.date.month
        and q1.date.day == q2.date.day
        and q1.base_currency_code == q2.base_currency_code
        and q1.quote_currency_code == q2.quote_currency_code
    )


def download_quotes(  # noqa: PLR0913
    provider: any,
    base_currency_code: str,
    quote_currency_code: str,
    start_date: datetime.date,
    end_date: datetime.date,
    logger: logging.Logger,
) -> list[Quote]:
    """Get quotes for each day in the given date range."""
    quotes = []
    logger.info(
        "downloading %s quotes for currency pair %s/%s for %s to %s...",
        provider.code,
        base_currency_code,
        quote_currency_code,
        start_date.isoformat(),
        end_date.isoformat(),
    )
    for dt in date_iterator(start_date, end_date, relativedelta(days=1)):
        quote = provider.get_quote(base_currency_code, quote_currency_code, dt)
        if quote:
            quotes.append(quote)
    return quotes


def read_quotelist_data(proto_path: str, logger: logging.Logger) -> QuoteList:
    """Read the serialized QuoteList from the given path."""
    qlist = QuoteList()
    with Path(proto_path).open("rb") as f:
        qlist.ParseFromString(f.read())

    logger.debug(
        "read %s quotes from %s...",
        len(qlist.quotes),
        proto_path,
    )

    return qlist


def write_quotes_data(
    proto_path: str | Path,
    quotes: list[Quote],
    logger: logging.Logger,
) -> None:
    """
    Write quotes data.

    write_quotes_data serializes a list of Quote objects to the given
    path merging with the existing quotes.
    """
    logger.debug(
        "writing %s  quotes to %s...",
        len(quotes),
        proto_path,
    )

    data_path = Path(proto_path)

    data_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing_quotelist = read_quotelist_data(proto_path, logger)
    except FileNotFoundError:
        existing_quotelist = QuoteList()

    quotes.extend([q for q in existing_quotelist.quotes if not quote_in(q, quotes)])
    quotes = sorted(quotes, key=lambda q: (q.date.year, q.date.month, q.date.day))

    qlist = QuoteList()
    qlist.quotes.extend(quotes)
    with data_path.open("wb") as f:
        logger.debug(
            "writing %s quotes to %s...",
            len(qlist.quotes),
            f.name,
        )
        f.write(qlist.SerializeToString())


def write_quotes_csv(
    path: str | Path,
    quotes: list[Quote],
    logger: logging.Logger,
) -> None:
    """Write a list of Quote objects to a CSV file."""
    csv_path = Path(path)
    with csv_path.open("w") as f:
        logger.debug(
            "writing %s quotes to %s...",
            len(quotes),
            f.name,
        )
        w = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "providerCode",
                "baseCurrencyCode",
                "quoteCurrencyCode",
                "ask",
                "bid",
                "mid",
            ],
        )
        w.writeheader()
        for q in quotes:
            w.writerow(
                {
                    "date": date_msg_to_str(q.date),
                    "providerCode": q.provider_code,
                    "baseCurrencyCode": q.base_currency_code,
                    "quoteCurrencyCode": q.quote_currency_code,
                    "ask": money_to_str(q.ask),
                    "bid": money_to_str(q.bid),
                    "mid": money_to_str(q.mid),
                },
            )


def write_year_quotes_site(
    base_dir: str | Path,
    year: int,
    quotelist: QuoteList,
    logger: logging.Logger,
) -> None:
    """
    Write a year's worth of quote files to the site directory.

    write_year_quotes_site writes quote API files to the site directory for a
    year's worth of quote files.
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    json_path = base_path.joinpath(f"{year:04d}.json")
    logger.debug(
        "writing %s quotes to %s...",
        len(quotelist.quotes),
        json_path,
    )

    # Write currencies list JSON.
    with json_path.open("w") as f:
        json.dump(MessageToDict(quotelist), f)

    # Write quote list CSV.
    csv_path = base_path.joinpath(f"{year:04d}.csv")
    write_quotes_csv(csv_path, quotelist.quotes, logger)

    # Write quote list protobuf
    proto_path = base_path.joinpath(f"{year:04d}.binpb")
    with proto_path.open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(quotelist.SerializeToString())

    month_qlists = defaultdict(QuoteList)
    for q in quotelist.quotes:
        month_qlists[q.date.month].quotes.append(q)

    for month, month_qlist in month_qlists.items():
        write_month_quotes_site(
            base_path.joinpath(f"{year:04d}"),
            month,
            month_qlist,
            logger,
        )


def write_month_quotes_site(
    base_dir: str | Path,
    month: int,
    quotelist: QuoteList,
    logger: logging.Logger,
) -> None:
    """
    Write a month's worth of quote files to the site directory.

    write_month_quotes_site writes quote API files to the site directory for a
    month's worth of quote files.
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    json_path = base_path.joinpath(f"{month:02d}.json")
    logger.debug(
        "writing %s quotes to %s...",
        len(quotelist.quotes),
        json_path,
    )

    # write currencies list JSON.
    with json_path.open("w") as f:
        json.dump(MessageToDict(quotelist), f)

    # write quote list CSV.
    csv_path = base_path.joinpath(f"{month:02d}.csv")
    write_quotes_csv(csv_path, quotelist.quotes, logger)

    # Write quote list proto
    proto_path = base_path.joinpath(f"{month:02d}.binpb")
    with proto_path.open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(quotelist.SerializeToString())

    for q in quotelist.quotes:
        write_day_quote_site(base_path.joinpath(f"{month:02d}"), q, logger)


def write_day_quote_site(
    base_dir: str | Path,
    quote: Quote,
    logger: logging.Logger,
) -> None:
    """Write a day's worth of quote files to the site directory."""
    _write_quote_site(base_dir, f"{quote.date.day:02d}", quote, logger)


def write_latest_quote_site(
    base_dir: str | Path,
    quote: Quote,
    logger: logging.Logger,
) -> None:
    """Write the latest quote files to the site directory."""
    _write_quote_site(base_dir, "latest", quote, logger)


def _write_quote_site(
    base_dir: str | Path,
    file_name: str,
    quote: Quote,
    logger: logging.Logger,
) -> None:
    """Write a quote file to the site directory."""
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    json_path = base_path.joinpath(f"{file_name}.json")
    logger.debug("writing %s...", json_path)

    # write currencies list JSON.
    with json_path.open("w") as f:
        json.dump(MessageToDict(quote), f)

    # write quote list CSV.
    csv_path = base_path.joinpath(f"{file_name}.csv")
    write_quotes_csv(csv_path, [quote], logger)

    # Write quote list proto
    proto_path = base_path.joinpath(f"{file_name}.binpb")
    with proto_path.open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(quote.SerializeToString())
