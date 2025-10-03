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

"""Tests for the update command."""

import datetime
import logging
import tempfile
import unittest
from pathlib import Path
from typing import Any, ClassVar

import urllib3
from google.type.date_pb2 import Date
from google.type.money_pb2 import Money

from fx.quote_pb2 import Quote
from fx.update import update_command


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


class TestUpdateCommand(unittest.TestCase):
    """Tests for the update_command function."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.temp_dir.cleanup()

    @unittest.mock.patch("urllib3.PoolManager")
    def test_update_command(self, mock_pool_manager: urllib3.PoolManager) -> None:
        """Test the update_command function."""

        class Args:
            logger = logging.getLogger("TestUpdateCommand")
            data_dir = self.temp_dir.name
            start = datetime.date(2024, 1, 1)
            end = datetime.date(2024, 1, 1)
            provider: ClassVar[list[any]] = [MockProvider]
            timeout = 10
            retry = 0
            backoff = 0

        args = Args()
        args.logger.addHandler(logging.NullHandler())

        mock_currencies_response = unittest.mock.Mock()
        mock_currencies_response.status = 200
        mock_currencies_response.data = (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            b'<ISO_4217 Pblshd="2025-05-12">'
            b"    <CcyTbl>"
            b"        <CcyNtry>"
            b"            <CtryNm>UNITED STATES OF AMERICA (THE)</CtryNm>"
            b"            <CcyNm>US Dollar</CcyNm>"
            b"            <Ccy>USD</Ccy>"
            b"            <CcyNbr>840</CcyNbr>"
            b"            <CcyMnrUnts>2</CcyMnrUnts>"
            b"        </CcyNtry>"
            b"        <CcyNtry>"
            b"            <CtryNm>JAPAN</CtryNm>"
            b"            <CcyNm>Yen</CcyNm>"
            b"            <Ccy>JPY</Ccy>"
            b"            <CcyNbr>392</CcyNbr>"
            b"            <CcyMnrUnts>0</CcyMnrUnts>"
            b"        </CcyNtry>"
            b"    </CcyTbl>"
            b"</ISO_4217>"
        )

        mock_historic_response = unittest.mock.Mock()
        mock_historic_response.status = 200
        mock_historic_response.data = (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            b'<ISO_4217 Pblshd="2025-03-31">'
            b"<HstrcCcyTbl></HstrcCcyTbl>"
            b"</ISO_4217>"
        )

        mock_pool_manager.return_value.request.side_effect = [
            mock_currencies_response,
            mock_historic_response,
        ]

        update_command(args)

        self.assertTrue(Path(self.temp_dir.name).joinpath("currencies.binpb").is_file())

        self.assertTrue(
            Path(self.temp_dir.name)
            .joinpath("MOCK", "USD", "JPY", "2024.binpb")
            .is_file(),
        )

        self.assertTrue(
            Path(self.temp_dir.name)
            .joinpath("MOCK", "EUR", "JPY", "2024.binpb")
            .is_file(),
        )
