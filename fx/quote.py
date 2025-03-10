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
import logging
import os
import os.path
from datetime import date

from dateutil.relativedelta import relativedelta
from google.protobuf.json_format import MessageToDict

from fx.currency import get_currencies, write_currencies
from fx.mufg import MUFGProvider
from fx.money import dict_to_str


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
            "baseCurrencyName",
            "baseCurrencyCode",
            "baseCurrencyNum",
            "quoteCurrencyName",
            "quoteCurrencyCode",
            "quoteCurrencyNum",
            "tts",
            "ttb",
            "ttm",
        ],
    )
    w.writeheader()
    for q in quote_dicts:
        w.writerow(
            {
                "date": date(q["date"]["year"], q["date"]["month"], q["date"]["day"]).isoformat(),
                "baseCurrencyName": q["baseCurrency"]["name"],
                "baseCurrencyCode": q["baseCurrency"]["alphabeticCode"],
                "baseCurrencyNum": q["baseCurrency"]["numericCode"],
                "quoteCurrencyName": q["quoteCurrency"]["name"],
                "quoteCurrencyCode": q["quoteCurrency"]["alphabeticCode"],
                "quoteCurrencyNum": q["quoteCurrency"]["numericCode"],
                "tts": dict_to_str(q["tts"]),
                "ttb": dict_to_str(q["ttb"]),
                "ttm": dict_to_str(q["ttm"]),
            }
        )


def update_quote(quote, base_path, logger):
    if not quote:
        return

    date_path = os.path.join(
        base_path,
        "quote",
        quote.provider.code,
        quote.base_currency.alphabetic_code,
        quote.quote_currency.alphabetic_code,
        str(quote.date.year),
        str(quote.date.month),
    )

    json_path = os.path.join(date_path, f'{str(quote.date.day)}.json')
    csv_path = os.path.join(date_path, f'{str(quote.date.day)}.csv')

    os.makedirs(date_path, exist_ok=True)

    # Get existing quotes if they already exist and merge with them.
    try:
        with open(json_path) as f:
            formatted_date = date(quote.date.year, quote.date.month, quote.date.day).isoformat()
            logger.debug(f'{formatted_date}: appending quote {quote.base_currency.alphabetic_code}/{quote.quote_currency.alphabetic_code}')
            quotes = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        quotes = []

    quote_dict = MessageToDict(quote)
    quotes = [q for q in quotes if q != quote_dict]
    quotes.append(quote_dict)

    with open(json_path, "w") as f:
        json.dump(quotes, f)

    with open(csv_path, "w") as f:
        write_quotes_csv(f, quotes)


def update_quotes(base_dir, start_date, end_date, currencies, logger):
    providers = [MUFGProvider(logger, currencies)]
    update_day_quotes(base_dir, start_date, end_date, providers, logger)

    for provider in providers:
        base_dir = os.path.join(
            base_dir,
            "quote",
            provider.code,
        )
        update_month_quotes(base_dir, logger)
        update_year_quotes(base_dir, logger)



def update_day_quotes(base_dir, start_date, end_date, providers, logger):
    for dt in dateIterator(start_date, end_date, relativedelta(days=1)):
        logger.debug(dt)

        for provider in providers:
            for base_currency in provider.supported_base_currencies():
                for quote_currency in provider.supported_quote_currencies():
                    try:
                        update_quote(provider.get_quote(base_currency, quote_currency, dt), base_dir, logger)
                    except Exception as e:
                        logger.warning(f'{dt} {type(e).__name__}: {e}')


def update_month_quotes(base_dir, logger):
    quotes = defaultdict(list)
    for root, dirs, files in os.walk(base_dir):
        if re.match(base_dir + r'/[a-zA-Z]{3}/[a-zA-Z]{3}/[0-9]{4}/[0-9]{1,2}$', root):
            for filename in files:
                if os.path.splitext(filename)[1] == '.json':
                    with open(os.path.join(root, filename)) as f:
                        day_quotes = json.load(f)
                        quotes[root].extend(day_quotes)

    for root, month_quotes in quotes.items():
        # sort month_quotes by date
        month_quotes = sorted(month_quotes, key=lambda q: (q["date"]["year"], q["date"]["month"], q["date"]["day"]))
        year_dir, month_str = os.path.split(root)
        with open(os.path.join(year_dir, f'{month_str}.json'), 'w') as f:
            json.dump(month_quotes, f)

        with open(os.path.join(year_dir, f'{month_str}.csv'), 'w') as f:
            write_quotes_csv(f, month_quotes)


def update_year_quotes(base_dir, logger):
    quotes = defaultdict(list)
    for root, dirs, files in os.walk(base_dir):
        if re.match(base_dir + r'/[a-zA-Z]{3}/[a-zA-Z]{3}/[0-9]{4}$', root):
            for filename in files:
                if os.path.splitext(filename)[1] == '.json':
                    with open(os.path.join(root, filename)) as f:
                        day_quotes = json.load(f)
                        quotes[root].extend(day_quotes)

    for root, year_quotes in quotes.items():
        # TODO: sort year_quotes by date
        year_quotes = sorted(year_quotes, key=lambda q: (q["date"]["year"], q["date"]["month"], q["date"]["day"]))
        parent_dir, year_str = os.path.split(root)
        with open(os.path.join(parent_dir, f'{year_str}.json'), 'w') as f:
            json.dump(year_quotes, f)

        with open(os.path.join(parent_dir, f'{year_str}.csv'), 'w') as f:
            write_quotes_csv(f, year_quotes)


