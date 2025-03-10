from urllib import request

from bs4 import BeautifulSoup

from fx.quote_pb2 import Quote, Provider
from google.type.date_pb2 import Date

from fx.money import str_to_money


class MUFGProvider:
    code = "MUFG"
    name = "MUFG Bank, Ltd."

    def __init__(self, logger, currencies):
        self.logger = logger
        self.currencies = currencies
        self._cache = {}

    def supported_quote_currencies(self):
        return ["JPY"]

    def supported_base_currencies(self):
        return [
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

    def get_quote(self, base_currency_code, quote_currency_code, quote_date):
        if (quote_currency_code, quote_date) not in self._cache:
            self._cache[(quote_currency_code, quote_date)] = self._get_quotes_by_date(quote_currency_code, quote_date)

        for q in self._cache[(quote_currency_code, quote_date)]:
            if q.base_currency.alphabetic_code == base_currency_code:
                return q

        return None

    def _get_quotes_by_date(self, quote_currency, quote_date):
        jpy_code = "JPY"

        if quote_currency != jpy_code:
            raise ValueError(f'currency "{quote_currency}" not supported')

        url = f'https://murc-kawasesouba.jp/fx/past_3month_result.php?y={quote_date.strftime("%Y")}&m={quote_date.strftime("%m")}&d={quote_date.strftime("%d")}'
        self.logger.debug(f'GET: {url}')
        resp = request.urlopen(url)

        quotes = []
        with resp as f:
            body = f.read()
            try:
                # NOTE: Some pages say they are EUC-JP but they are actually SHIFT-JIS.
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
            kwargs = {
                "provider": Provider(
                    code=self.code,
                    name=self.name,
                ),
                "date": Date(
                    year=quote_date.year,
                    month=quote_date.month,
                    day=quote_date.day,
                ),
                "quote_currency": self.currencies["JPY"],
            }

            for i, cell in enumerate(table.select("td")):
                match i % 6:
                    case 0:
                        # Base currency name is ignored.
                        pass
                    case 1:
                        # Japanese name is ignored
                        pass
                    case 2:
                        kwargs["base_currency"] = self.currencies[cell.get_text(strip=True)]
                    case 3:

                        try:
                            kwargs["tts"] = str_to_money(jpy_code, cell.get_text(strip=True))
                        except ValueError as e:
                            self.logger.debug(f'tts: {type(e).__name__}: {e}')
                            pass
                    case 4:
                        try:
                            kwargs["ttb"] = str_to_money(jpy_code, cell.get_text(strip=True))
                        except ValueError as e:
                            self.logger.debug(f'ttb: {type(e).__name__}: {e}')
                            pass
                    case 5:
                        try:
                            kwargs["ttm"] = str_to_money(jpy_code, cell.get_text(strip=True))
                        except ValueError as e:
                            self.logger.debug(f'ttm: {type(e).__name__}: {e}')
                            pass

                        if kwargs.get("tts") or kwargs.get("ttb") or kwargs.get("ttm"):
                            quotes.append(Quote(**kwargs))

        return quotes
