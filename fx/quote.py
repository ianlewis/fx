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


from collections import defaultdict
import csv
import json
import os
import os.path

from dateutil.relativedelta import relativedelta
from google.protobuf.json_format import MessageToDict

from quote_pb2 import QuoteList
from utils import dateIterator, date_msg_to_str, money_to_str


def quote_in(q, quotes):
    """
    quote_in returns True if the given quote object has a matching quote in
    the given list of quotes.
    """
    for q2 in quotes:
        if quote_equal(q, q2):
            return True
    return False


def quote_equal(q1, q2):
    """
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


def download_quotes(provider, base_currency_code, quote_currency_code, start_date, end_date, logger):
    """
    download_quotes gets quotes for each day in the given date range.
    """
    quotes = []
    logger.info(f"downloading {provider.code} quotes for currency pair {base_currency_code}/{quote_currency_code} for {start_date.isoformat()} to {end_date.isoformat()}...")
    for dt in dateIterator(start_date, end_date, relativedelta(days=1)):
        quote = provider.get_quote(base_currency_code, quote_currency_code, dt)
        if quote:
            quotes.append(quote)
    return quotes


def read_quotelist_data(proto_path, logger):
    """
    read_quotelist_data loads the serialized list of Quote objects and
    returns the list.
    """

    qlist = QuoteList()
    with open(proto_path, "rb") as f:
        qlist.ParseFromString(f.read())

    logger.debug(f"read {len(qlist.quotes)} quotes from {proto_path}...")

    return qlist


def write_quotes_data(proto_path, quotes, logger):
    """
    write_quotes_data serializes a list of Quote objects to the given
    path merging with the existing quotes.
    """
    logger.debug(f"writing {len(quotes)} quotes to {proto_path}...")

    os.makedirs(os.path.dirname(proto_path), exist_ok=True)

    try:
        existing_quotelist = read_quotelist_data(proto_path, logger)
    except FileNotFoundError:
        existing_quotelist = QuoteList()

    quotes.extend([q for q in existing_quotelist.quotes if not quote_in(q, quotes)])
    quotes = sorted(quotes, key=lambda q: (q.date.year, q.date.month, q.date.day))

    qlist = QuoteList()
    qlist.quotes.extend(quotes)
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {len(qlist.quotes)} quotes to {f.name}...")
        f.write(qlist.SerializeToString())


def write_quotes_csv(path, quotes, logger):
    with open(path, "w") as f:
        logger.debug(f"writing {len(quotes)} quotes to {f.name}...")
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
                }
            )


def write_year_quotes_site(base_dir, year, quotelist, logger):
    """
    write_year_quotes_site writes quote API files to the site directory for a
    year's worth of quote files.
    """
    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, f"{year:04d}.json")
    logger.debug(f"writing {len(quotelist.quotes)} quotes to {json_path}...")

    # write currencies list JSON.
    with open(json_path, "w") as f:
        json.dump(MessageToDict(quotelist), f)

    # write quote list CSV.
    csv_path = os.path.join(base_dir, f"{year:04d}.csv")
    write_quotes_csv(csv_path, quotelist.quotes, logger)

    # Write quote list proto
    proto_path = os.path.join(base_dir, f"{year:04d}.binpb")
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(quotelist.SerializeToString())

    month_qlists = defaultdict(QuoteList)
    for q in quotelist.quotes:
        month_qlists[q.date.month].quotes.append(q)

    for month, month_qlist in month_qlists.items():
        write_month_quotes_site(os.path.join(base_dir, f"{year:04d}"), month, month_qlist, logger)


def write_month_quotes_site(base_dir, month, quotelist, logger):
    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, f"{month:02d}.json")
    logger.debug(f"writing {len(quotelist.quotes)} quotes to {json_path}...")

    # write currencies list JSON.
    with open(json_path, "w") as f:
        json.dump(MessageToDict(quotelist), f)

    # write quote list CSV.
    csv_path = os.path.join(base_dir, f"{month:02d}.csv")
    write_quotes_csv(csv_path, quotelist.quotes, logger)

    # Write quote list proto
    proto_path = os.path.join(base_dir, f"{month:02d}.binpb")
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(quotelist.SerializeToString())

    for q in quotelist.quotes:
        write_day_quote_site(os.path.join(base_dir, f"{month:02d}"), q, logger)


def write_day_quote_site(base_dir, quote, logger):
    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, f"{quote.date.day:02d}.json")
    logger.debug(f"writing {json_path}...")

    # write currencies list JSON.
    with open(json_path, "w") as f:
        json.dump(MessageToDict(quote), f)

    # write quote list CSV.
    csv_path = os.path.join(base_dir, f"{quote.date.day:02d}.csv")
    write_quotes_csv(csv_path, [quote], logger)

    # Write quote list proto
    proto_path = os.path.join(base_dir, f"{quote.date.day:02d}.binpb")
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(quote.SerializeToString())
