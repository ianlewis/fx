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

from bs4 import BeautifulSoup
from google.type.date_pb2 import Date
import urllib3

from quote_pb2 import Quote
from utils import str_to_money


class MUFGProvider:
    code = "MUFG"
    name = "MUFG Bank, Ltd."

    supported_base_currencies = [
        "USD",
        "EUR",
        "CAD",
        "GBP",
        "CHF",
        "DKK",
        "NOK",
        "SEK",
        "AUD",
        "NZD",
        "HKD",
        "MYR",
        "SGD",
        "SAR",
        "AED",
        "CNY",
        "THB",
        "INR",
        "PKR",
        "KWD",
        "QAR",
        "IDR",
        "MXN",
        "KRW",
        "PHP",
        "ZAR",
        "CZK",
        "RUB",
        "HUF",
        "PLN",
        "TRY",
    ]
    supported_quote_currencies = ["JPY"]

    def __init__(self, args):
        self.logger = args.logger
        self.timeout = args.timeout
        self.retries = args.retry
        self._cache = {}

    def get_quote(self, base_currency_code, quote_currency_code, quote_date):
        if (quote_currency_code, quote_date) not in self._cache:
            self._cache[(quote_currency_code, quote_date)] = self._get_quotes_by_date(quote_currency_code, quote_date)

        for q in self._cache[(quote_currency_code, quote_date)]:
            if q.base_currency_code == base_currency_code:
                return q

        return None

    def _get_quotes_by_date(self, quote_currency, quote_date):
        jpy_code = "JPY"

        if quote_currency != jpy_code:
            raise ValueError(f'currency "{quote_currency}" not supported')

        url = f'https://murc-kawasesouba.jp/fx/past_3month_result.php?y={quote_date.strftime("%Y")}&m={quote_date.strftime("%m")}&d={quote_date.strftime("%d")}'
        self.logger.debug(f"GET {url}")

        http = urllib3.PoolManager(
            # backoff_factor=0.2 creates retries at 0.0s, 0.4s, 0.8s, 1.6s, ...
            retries=urllib3.Retry(connect=self.retries, read=self.retries, backoff_factor=0.2, redirect=2),
            timeout=urllib3.Timeout(connect=self.timeout, read=self.timeout),
        )

        resp = http.request("GET", url)

        quotes = []
        body = resp.data
        try:
            # NOTE: Some pages say they are EUC-JP but they are actually
            #       SHIFT-JIS so we can't always rely on BeautifulSoup to
            #       detect the character set.
            body = body.decode("shift-jis")
        except UnicodeDecodeError as e:
            # The decoding error is logged at debug level since it's "expected".
            self.logger.debug("%s %s", quote_date, e)

        soup = BeautifulSoup(body, "html.parser")
        table = soup.select_one("table.data-table5")

        if not table:
            # This most likely means that there are no quotes for this day.
            return quotes

        # NOTE: The HTML on this page is invalid. It contains </tr> but no
        #       opening <tr> tag for table rows after the first row. Thus we
        #       don't select for <tr> tags but go directly to the <td> tag.

        kwargs = {}
        for i, cell in enumerate(table.select("td")):
            match i % 6:
                case 0:
                    # Base currency name is ignored.
                    kwargs = {
                        "provider_code": self.code,
                        "date": Date(
                            year=quote_date.year,
                            month=quote_date.month,
                            day=quote_date.day,
                        ),
                        "quote_currency_code": "JPY",
                    }
                    pass
                case 1:
                    # Japanese name is ignored
                    pass
                case 2:
                    try:
                        kwargs["base_currency_code"] = cell.get_text(strip=True)
                    except KeyError as e:
                        self.logger.debug(f"tts: {type(e).__name__}: {e}")
                        pass
                case 3:
                    try:
                        kwargs["ask"] = str_to_money(jpy_code, cell.get_text(strip=True))
                    except ValueError as e:
                        self.logger.debug(f"tts: {type(e).__name__}: {e}")
                        pass
                case 4:
                    try:
                        kwargs["bid"] = str_to_money(jpy_code, cell.get_text(strip=True))
                    except ValueError as e:
                        self.logger.debug(f"ttb: {type(e).__name__}: {e}")
                        pass
                case 5:
                    try:
                        kwargs["mid"] = str_to_money(jpy_code, cell.get_text(strip=True))
                    except ValueError as e:
                        self.logger.debug(f"ttm: {type(e).__name__}: {e}")
                        pass

                    if kwargs.get("base_currency_code") and (kwargs.get("ask") or kwargs.get("bid") or kwargs.get("mid")):
                        quotes.append(Quote(**kwargs))

        return quotes
