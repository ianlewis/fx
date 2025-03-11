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
from collections import defaultdict
import csv
import json
import os
import os.path
from datetime import date
import shutil

from dateutil.relativedelta import relativedelta
from google.protobuf.json_format import MessageToDict

from money import dict_to_str


def dateIterator(from_date=None, to_date=None, delta=relativedelta(days=1)):
    from_date = from_date or date.today()
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date = from_date + delta
    return


def write_quotes_csv(f, quote_dicts):
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
    for q in quote_dicts:
        w.writerow(
            {
                "date": "{:04d}/{:02d}/{:02d}".format(q["date"]["year"], q["date"]["month"], q["date"]["day"]),
                "providerCode": q["providerCode"],
                "baseCurrencyCode": q["baseCurrencyCode"],
                "quoteCurrencyCode": q["quoteCurrencyCode"],
                "ask": dict_to_str(q.get("ask")),
                "bid": dict_to_str(q.get("bid")),
                "mid": dict_to_str(q.get("mid")),
            }
        )


def update_day_quote(quote, base_dir, logger):
    date_path = os.path.join(
        base_dir,
        "provider",
        quote.provider_code,
        "quote",
        quote.base_currency_code,
        quote.quote_currency_code,
        "{:04d}".format(quote.date.year),
        "{:02d}".format(quote.date.month),
    )

    update_quote(quote, date_path, "{:02d}".format(quote.date.day), logger)


def update_quote(quote, base_dir, name, logger):
    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, f"{name}.json")
    csv_path = os.path.join(base_dir, f"{name}.csv")

    quote_dict = MessageToDict(quote)

    with open(json_path, "w") as f:
        json.dump(quote_dict, f)

    with open(csv_path, "w") as f:
        write_quotes_csv(f, [quote_dict])


def update_quotes(base_dir, start_date, end_date, providers, currencies, logger):
    update_day_quotes(base_dir, start_date, end_date, providers, logger)

    for provider in providers:
        base_dir = os.path.join(
            base_dir,
            "provider",
            provider.code,
            "quote",
        )
        update_month_quotes(base_dir, logger)
        update_year_quotes(base_dir, logger)
        update_latest_quotes(base_dir, logger)


def update_day_quotes(base_dir, start_date, end_date, providers, logger):
    for dt in dateIterator(start_date, end_date, relativedelta(days=1)):
        logger.info(f"Updating quotes for {dt.isoformat()}...")
        for provider in providers:
            for base_currency_code in provider.supported_base_currencies():
                for quote_currency_code in provider.supported_quote_currencies():
                    quote = provider.get_quote(base_currency_code, quote_currency_code, dt)
                    if quote:
                        update_day_quote(quote, base_dir, logger)


def update_month_quotes(base_dir, logger):
    logger.debug("Updating month quotes...")

    quotes = defaultdict(list)
    for root, dirs, files in os.walk(base_dir):
        if re.match(r"^" + re.escape(base_dir) + r"/[a-zA-Z]{3}/[a-zA-Z]{3}/[0-9]{4}/[0-9]{1,2}$", root):
            for filename in files:
                if os.path.splitext(filename)[1] == ".json":
                    with open(os.path.join(root, filename)) as f:
                        quotes[root].append(json.load(f))

    for root, month_quotes in quotes.items():
        # sort month_quotes by date
        month_quotes = sorted(month_quotes, key=lambda q: (q["date"]["year"], q["date"]["month"], q["date"]["day"]))
        year_dir, month_str = os.path.split(root)
        with open(os.path.join(year_dir, f"{month_str}.json"), "w") as f:
            json.dump(month_quotes, f)

        with open(os.path.join(year_dir, f"{month_str}.csv"), "w") as f:
            write_quotes_csv(f, month_quotes)


def update_year_quotes(base_dir, logger):
    logger.debug("Updating year quotes...")

    quotes = defaultdict(list)
    for root, dirs, files in os.walk(base_dir):
        if re.match(r"^" + re.escape(base_dir) + r"/[a-zA-Z]{3}/[a-zA-Z]{3}/[0-9]{4}$", root):
            for filename in files:
                if os.path.splitext(filename)[1] == ".json":
                    with open(os.path.join(root, filename)) as f:
                        quotes[root].extend(json.load(f))

    for root, year_quotes in quotes.items():
        year_quotes = sorted(year_quotes, key=lambda q: (q["date"]["year"], q["date"]["month"], q["date"]["day"]))
        parent_dir, year_str = os.path.split(root)
        with open(os.path.join(parent_dir, f"{year_str}.json"), "w") as f:
            json.dump(year_quotes, f)

        with open(os.path.join(parent_dir, f"{year_str}.csv"), "w") as f:
            write_quotes_csv(f, year_quotes)


def update_latest_quotes(base_dir, logger):
    latest = {}

    logger.debug("Updating latest quotes...")

    for root, dirs, files in os.walk(base_dir):
        match = re.match(r"^" + re.escape(base_dir) + r"/([a-zA-Z]{3})/([a-zA-Z]{3})/([0-9]{4})/([0-9]{1,2})$", root)
        if match:
            base_currency_code = match.group(1)
            quote_currency_code = match.group(2)

            try:
                year = int(match.group(3))
                month = int(match.group(4))
                for filename in files:
                    parts = os.path.splitext(filename)
                    day = int(parts[0])
                    if parts[1] == ".json":
                        quote_date = date(year, month, day)
                        cur_pair = (base_currency_code, quote_currency_code)
                        if cur_pair not in latest or latest[cur_pair]["date"] < quote_date:
                            latest[cur_pair] = {
                                "date": quote_date,
                                "json_path": os.path.join(root, filename),
                                "csv_path": os.path.join(root, parts[0] + ".csv"),
                            }
            except ValueError as e:
                logger.debug("looking for latest quote: %s", e)

    for base_currency_code, quote_currency_code in latest:
        json_path = latest[(base_currency_code, quote_currency_code)]["json_path"]
        csv_path = latest[(base_currency_code, quote_currency_code)]["csv_path"]

        logger.debug(f"latest quote for {base_currency_code}/{quote_currency_code} is {json_path}")

        pair_path = os.path.join(base_dir, base_currency_code, quote_currency_code)
        shutil.copyfile(json_path, os.path.join(pair_path, "latest.json"))
        shutil.copyfile(csv_path, os.path.join(pair_path, "latest.csv"))
