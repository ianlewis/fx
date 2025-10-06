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

import argparse
import datetime
import logging
import unittest
from unittest import mock

from fx.mufg import MUFGProvider


class _MockResponse:
    def __init__(self, data: bytes) -> None:
        self.data = data


class TestMUFGProvider(unittest.TestCase):
    """Tests for MUFGProvider."""

    def test_get_quote(self) -> None:
        """Test the get_quote provider method."""
        with mock.patch.object(MUFGProvider, "_request") as mocked_request:
            mocked_request.return_value = _MockResponse(
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
            )

            provider = MUFGProvider(
                argparse.Namespace(
                    logger=logging.getLogger("fx"),
                    timeout=10,
                    retry=0,
                    backoff=0,
                ),
            )

            quote = provider.get_quote("USD", "JPY", datetime.date(2024, 6, 20))

        if quote is None:
            self.fail("quote is None")

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
        with mock.patch.object(MUFGProvider, "_request") as mocked_request:
            mocked_request.return_value = _MockResponse(
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
            )

            provider = MUFGProvider(
                argparse.Namespace(
                    logger=logging.getLogger("fx"),
                    timeout=10,
                    retry=0,
                    backoff=0,
                ),
            )

            quote = provider.get_quote("XYZ", "JPY", datetime.date(2024, 6, 20))

        if quote is None:
            self.fail("quote is None")

        self.assertIsNone(quote)
