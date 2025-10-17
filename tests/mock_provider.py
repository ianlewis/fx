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

"""A mock currency quote provider for tests."""

import datetime
from typing import Any, ClassVar

from google.type.date_pb2 import Date
from google.type.money_pb2 import Money

from fx.quote_pb2 import Quote  # type: ignore[attr-defined]


class MockProvider:
    """A mock provider for testing."""

    code = "MOCK"
    name = "Mock Provider"

    supported_base_currencies: ClassVar[list[str]] = ["USD", "EUR"]
    supported_quote_currencies: ClassVar[list[str]] = ["JPY"]

    def __init__(self, args: Any) -> None:  # noqa: ANN401
        """Initialize the mock provider."""

    def get_quote(
        self,
        base_currency_code: str,
        quote_currency_code: str,
        quote_date: datetime.date,
    ) -> Quote | None:
        """Get a mock quote."""
        if base_currency_code not in self.supported_base_currencies:
            return None
        if quote_currency_code not in self.supported_quote_currencies:
            return None
        quote = Quote()
        quote.provider_code = self.code
        quote.base_currency_code = base_currency_code
        quote.quote_currency_code = quote_currency_code
        quote.date.CopyFrom(
            Date(
                year=quote_date.year,
                month=quote_date.month,
                day=quote_date.day,
            ),
        )
        quote.bid.CopyFrom(
            Money(
                currency_code=quote_currency_code,
                units=110,
                nanos=250000000,
            ),
        )
        quote.mid.CopyFrom(
            Money(
                currency_code=quote_currency_code,
                units=111,
                nanos=250000000,
            ),
        )
        quote.ask.CopyFrom(
            Money(
                currency_code=quote_currency_code,
                units=112,
                nanos=250000000,
            ),
        )

        return quote
