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

"""Currency module for downloading and processing ISO 4217 currency data."""

import csv
import datetime
import json
import logging
from pathlib import Path
from typing import Any

import urllib3
from defusedxml import ElementTree
from google.protobuf.json_format import MessageToDict
from google.type.date_pb2 import Date

from fx.currency_pb2 import Currency, CurrencyList
from fx.utils import date_msg_to_str

ISO_DOWNLOAD_XML = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml"
ISO_DOWNLOAD_HISTORIC_XML = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-three.xml"


# TODO(#100): Refactor to reduce complexity
def download_currencies(args: Any) -> CurrencyList:  # noqa: ANN401, C901
    """
    Download and parse the ISO 4217 currency list.

    Downloads and parses the ISO 4217 currency list and
    returns a list of unique Currency entries.
    """
    args.logger.debug("downloading currencies...")
    args.logger.debug("GET %s", ISO_DOWNLOAD_XML)

    http = urllib3.PoolManager(
        retries=urllib3.Retry(connect=args.retry, read=args.retry, redirect=2),
        timeout=urllib3.Timeout(connect=args.timeout, read=args.timeout),
    )

    resp = http.request("GET", ISO_DOWNLOAD_XML)

    currencies = {}
    root = ElementTree.fromstring(resp.data)
    ccytbl = root.find("CcyTbl")
    for ccyntry in ccytbl.findall("CcyNtry"):
        code = ccyntry.findtext("Ccy")

        if code is None:
            continue

        country_name = ccyntry.findtext("CtryNm")
        numeric_code = ccyntry.findtext("CcyNbr")
        currency_name = ccyntry.findtext("CcyNm")

        args.logger.debug(currency_name)
        try:
            minor_units = int(ccyntry.findtext("CcyMnrUnts"))
        except (ValueError, TypeError):
            minor_units = 0

        if code in currencies:
            currencies[code].countries.append(country_name)

            if currencies[code].numeric_code != numeric_code:
                msg = f"Numeric code mismatch for {code}"
                raise ValueError(msg)
            if currencies[code].name != currency_name:
                msg = f"Name mismatch for {code}"
                raise ValueError(msg)
            if currencies[code].minor_units != minor_units:
                msg = f"Minor units mismatch for {code}"
                raise ValueError(msg)
        else:
            args.logger.debug("Registered currency: %s", code)

            currencies[code] = Currency(
                alphabetic_code=code,
                numeric_code=numeric_code,
                name=currency_name,
                minor_units=minor_units,
                countries=[ccyntry.findtext("CtryNm")],
            )

    args.logger.debug("GET %s", ISO_DOWNLOAD_HISTORIC_XML)
    resp = http.request("GET", ISO_DOWNLOAD_HISTORIC_XML)

    root = ElementTree.fromstring(resp.data)
    ccytbl = root.find("HstrcCcyTbl")
    for ccyntry in ccytbl.findall("HstrcCcyNtry"):
        code = ccyntry.findtext("Ccy")
        if code in currencies:
            currencies[code].countries.append(ccyntry.findtext("CtryNm"))
        else:
            args.logger.debug("Registered historical currency: %s", code)
            try:
                wdate = (
                    datetime.datetime.strptime(ccyntry.findtext("WthdrwlDt"), "%Y-%m")
                    .replace(tzinfo=datetime.UTC)
                    .date()
                )
            except ValueError as e:
                args.logger.warning("invalid WthdrwlDt: %s", e)
                continue

            currencies[code] = Currency(
                alphabetic_code=code,
                numeric_code=ccyntry.findtext("CcyNbr"),
                name=ccyntry.findtext("CcyNm"),
                minor_units=0,
                withdrawal_date=Date(
                    year=wdate.year,
                    month=wdate.month,
                ),
            )

    return currencies.values()


def read_currencies_data(
    proto_path: str | Path,
    logger: logging.Logger,
) -> dict[str, Currency]:
    """
    Load serialized Currency objects.

    Loads the serialized list of Currency objects and
    returns a dictionary whose key is the ISO 4217 alphabetic code and whose
    values are the corresponding Currency objects.
    """
    logger.debug("loading currencies from %s...", proto_path)

    clist = CurrencyList()
    with Path(proto_path).open("rb") as f:
        clist.ParseFromString(f.read())

    cmap = {}
    for c in clist.currencies:
        cmap[c.alphabetic_code] = c
    return cmap


def write_currencies_data(
    proto_path: str | Path,
    currencies: list[Currency],
    logger: logging.Logger,
) -> None:
    """
    Serialize Currency objects to file.

    Serializes a list of Currency objects to the given
    path overwriting the existing list of currencies.
    """
    logger.debug("writing %d currencies to %s...", len(currencies), proto_path)

    Path(proto_path).parent.mkdir(parents=True, exist_ok=True)

    clist = CurrencyList()
    clist.currencies.extend(currencies)
    with Path(proto_path).open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(clist.SerializeToString())


def write_currencies_site(
    base_dir: str | Path,
    currencies_dict: dict[str, Currency],
    logger: logging.Logger,
) -> None:
    """
    Write currency API files to the site directory.

    Args:
        base_dir: Base directory for output files
        currencies_dict: Dictionary of currencies as read from `read_currencies_data`
        logger: Logger instance

    """
    clist = CurrencyList()
    clist.currencies.extend(currencies_dict.values())

    base_path = Path(base_dir)

    base_path.mkdir(parents=True, exist_ok=True)

    json_path = base_path.joinpath("currency.json")
    logger.debug("writing %d currencies to %s...", len(clist.currencies), json_path)

    # write currencies list JSON.
    with json_path.open("w") as f:
        json.dump(MessageToDict(clist), f)

    # write currencies list CSV.
    csv_path = base_path.joinpath("currency.csv")
    logger.debug("writing %d currencies to %s...", len(clist.currencies), csv_path)
    csv_fields = [
        "alphabeticCode",
        "numericCode",
        "name",
        "minorUnits",
        "countries",
        "withdrawalDate",
    ]

    with csv_path.open("w") as f:
        if len(clist.currencies) > 0:
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            for c in clist.currencies:
                w.writerow(
                    {
                        "alphabeticCode": c.alphabetic_code,
                        "numericCode": c.numeric_code or "",
                        "name": c.name,
                        "minorUnits": c.minor_units,
                        "countries": ",".join(c.countries),
                        "withdrawalDate": date_msg_to_str(c.withdrawal_date) or "",
                    },
                )

    # Write currencies list proto
    proto_path = base_path.joinpath("currency.binpb")
    with proto_path.open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(clist.SerializeToString())

    # Write individual currencies
    currency_path = base_path.joinpath("currency")
    currency_path.mkdir(parents=True, exist_ok=True)

    for c in clist.currencies:
        # Write currency json
        c_json_path = currency_path.joinpath(f"{c.alphabetic_code}.json")
        with c_json_path.open("w") as f:
            logger.debug("writing %s...", f.name)
            json.dump(MessageToDict(c), f)

        # Write currency csv
        c_csv_path = currency_path.joinpath(f"{c.alphabetic_code}.csv")
        with c_csv_path.open("w") as f:
            logger.debug("writing %s...", f.name)
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            w.writerow(
                {
                    "alphabeticCode": c.alphabetic_code,
                    "numericCode": c.numeric_code or "",
                    "name": c.name,
                    "minorUnits": c.minor_units,
                    "countries": ",".join(c.countries),
                    "withdrawalDate": date_msg_to_str(c.withdrawal_date) or "",
                },
            )

        # Write currency proto
        c_proto_path = currency_path.joinpath(f"{c.alphabetic_code}.binpb")
        with c_proto_path.open("wb") as f:
            logger.debug("writing %s...", f.name)
            f.write(c.SerializeToString())
