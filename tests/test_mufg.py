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

"""Tests for MUFGProvider."""

import datetime
import logging
import unittest
from unittest import mock

from fx.mufg import MUFGProvider


class TestMUFGProvider(unittest.TestCase):
    """Tests for MUFGProvider."""

    def setUp(self) -> None:
        """Set up the test case."""

        class Args:
            logger = logging.getLogger("fx")
            timeout = 10
            retry = 0
            backoff = 0

        self.provider = MUFGProvider(Args())

        class MockResponse:
            def __init__(self, data: bytes) -> None:
                self.data = data

        self.provider._request = mock.MagicMock(  # noqa: SLF001
            return_value=MockResponse(
                """
            <html>
                <head><title>Test</title></head>
                <body>
                    <table class="data-table5">
                        <tr>

                            <th>Quote Currency</th>
                            <th>Base Currency Name</th>
                            <th>Base Currency</th>
                            <th>Buying Rate</th>
                            <th>Selling Rate</th>
                            <th>Middle Rate</th>
                        </tr>
                        <tr>
                            <td>JPY</td>
                            <td>米国ドル</td>
                            <td>USD</td>
                            <td>109.25</td>
                            <td>111.25</td>
                            <td>110.25</td>
                        </tr>
                    </table>
                </body>
            </html>
        """.encode("euc-jp"),
            ),
        )

    def test_get_quote(self) -> None:
        """Test the get_quote provider method."""
        quote = self.provider.get_quote("USD", "JPY", datetime.date(2024, 6, 20))
        self.assertEqual(quote.date.year, 2024)
        self.assertEqual(quote.date.month, 6)
        self.assertEqual(quote.date.day, 20)
        self.assertEqual(quote.base_currency_code, "USD")
        self.assertEqual(quote.quote_currency_code, "JPY")
        self.assertEqual(quote.ask.units, 109)
        self.assertEqual(quote.ask.nanos, 250000000)
        self.assertEqual(quote.bid.units, 111)
        self.assertEqual(quote.bid.nanos, 250000000)
        self.assertEqual(quote.mid.units, 110)
        self.assertEqual(quote.mid.nanos, 250000000)

    def test_get_quotes_none(self) -> None:
        """Test the get_quote provider method with no data."""
        quote = self.provider.get_quote("XYZ", "JPY", datetime.date(2024, 6, 20))
        self.assertIsNone(quote)
