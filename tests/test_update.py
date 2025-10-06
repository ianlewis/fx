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

import argparse
import datetime
import logging
import tempfile
import unittest
from pathlib import Path

import urllib3

from fx.update import update_command
from tests.mock_provider import MockProvider


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

        logger = logging.getLogger("TestUpdateCommand")
        logger.addHandler(logging.NullHandler())

        update_command(
            argparse.Namespace(
                logger=logger,
                data_dir=self.temp_dir.name,
                start=datetime.date(2024, 1, 1),
                end=datetime.date(2024, 1, 1),
                provider=[MockProvider],
                timeout=10,
                retry=0,
                backoff=0,
            ),
        )

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
