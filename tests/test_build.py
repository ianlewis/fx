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

"""Tests for the build command."""

import argparse
import logging
import tempfile
import unittest
from pathlib import Path

from fx.build import build_command
from fx.v1.quote_pb2 import QuoteList  # type: ignore[attr-defined]
from tests.mock_provider import MockProvider


def _write_test_data(data_dir_path: Path) -> None:
    """Write test data."""
    quotes = QuoteList()
    quote = quotes.quotes.add()
    quote.provider_code = "MOCK"
    quote.base_currency_code = "USD"
    quote.quote_currency_code = "JPY"
    quote.date.year = 2023
    quote.date.month = 1
    quote.date.day = 1
    quote.ask.units = 131
    quote.ask.nanos = 500000000
    quote.bid.units = 129
    quote.bid.nanos = 500000000
    quote.mid.units = 130
    quote.mid.nanos = 0

    quote = quotes.quotes.add()
    quote.provider_code = "MOCK"
    quote.base_currency_code = "USD"
    quote.quote_currency_code = "JPY"
    quote.date.year = 2023
    quote.date.month = 1
    quote.date.day = 2
    quote.ask.units = 141
    quote.ask.nanos = 500000000
    quote.bid.units = 139
    quote.bid.nanos = 500000000
    quote.mid.units = 140
    quote.mid.nanos = 0

    quote_file_path = data_dir_path.joinpath("MOCK", "USD", "JPY", "2023.binpb")
    quote_file_path.parent.mkdir(parents=True, exist_ok=True)
    with quote_file_path.open("wb") as f:
        f.write(quotes.SerializeToString())


class TestBuildCommand(unittest.TestCase):
    """Tests for the build command."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.temp_data_dir = tempfile.TemporaryDirectory()
        self.temp_site_dir = tempfile.TemporaryDirectory()
        _write_test_data(Path(self.temp_data_dir.name))

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.temp_data_dir.cleanup()
        self.temp_site_dir.cleanup()

    def test_build_command(self) -> None:
        """Test the build command."""
        build_command(
            args=argparse.Namespace(
                logger=logging.getLogger("TestBuildCommand"),
                data_dir=self.temp_data_dir.name,
                site_dir=self.temp_site_dir.name,
                provider=[MockProvider],
            ),
        )

        formats = ["json", "csv", "binpb"]

        # Provider
        for ext in formats:
            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    f"MOCK.{ext}",
                )
                .exists(),
            )

        # latest Quotes
        for ext in formats:
            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    "MOCK",
                    "quote",
                    "USD",
                    "JPY",
                    f"latest.{ext}",
                )
                .exists(),
            )

        # Historical Quotes for 2023
        for ext in formats:
            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    "MOCK",
                    "quote",
                    "USD",
                    "JPY",
                    f"2023.{ext}",
                )
                .exists(),
            )

        # Monthly Quotes for 2023-01
        for ext in formats:
            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    "MOCK",
                    "quote",
                    "USD",
                    "JPY",
                    "2023",
                    f"01.{ext}",
                )
                .exists(),
            )

        # Daily Quotes for 2023-01-01
        for ext in formats:
            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    "MOCK",
                    "quote",
                    "USD",
                    "JPY",
                    "2023",
                    "01",
                    f"01.{ext}",
                )
                .exists(),
            )

            self.assertTrue(
                Path(self.temp_site_dir.name)
                .joinpath(
                    "v1",
                    "provider",
                    "MOCK",
                    "quote",
                    "USD",
                    "JPY",
                    "2023",
                    "01",
                    f"02.{ext}",
                )
                .exists(),
            )
