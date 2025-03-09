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

import csv
from datetime import datetime
import json
import os
import os.path
from urllib import request
import xml.etree.ElementTree as ET

from google.protobuf.json_format import MessageToDict
from google.type.date_pb2 import Date

from currency_pb2 import Currency, CurrencyList
from utils import date_msg_to_str

ISO_DOWNLOAD_XML = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml"
ISO_DOWNLOAD_HISTORIC_XML = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-three.xml"


def download_currencies(logger):
    """
    download_currencies downloads and parses the ISO 4217 currency list and
    returns a list of unique Currency entries.
    """

    logger.debug("downloading currencies...")

    logger.debug(f"GET {ISO_DOWNLOAD_XML}")
    resp = request.urlopen(ISO_DOWNLOAD_XML)

    currencies = {}
    with resp as f:
        root = ET.fromstring(f.read())
        ccytbl = root.find("CcyTbl")
        for ccyntry in ccytbl.findall("CcyNtry"):
            code = ccyntry.findtext("Ccy")

            if code is None:
                continue

            country_name = ccyntry.findtext("CtryNm")
            numeric_code = ccyntry.findtext("CcyNbr")
            currency_name = ccyntry.findtext("CcyNm")

            logger.debug(currency_name)
            try:
                minor_units = int(ccyntry.findtext("CcyMnrUnts"))
            except (ValueError, TypeError):
                minor_units = 0

            if code in currencies:
                currencies[code].countries.append(country_name)

                assert currencies[code].numeric_code == numeric_code
                assert currencies[code].name == currency_name
                assert currencies[code].minor_units == minor_units
            else:
                logger.debug(f"Registered currency: {code}")

                currencies[code] = Currency(
                    alphabetic_code=code,
                    numeric_code=numeric_code,
                    name=currency_name,
                    minor_units=minor_units,
                    countries=[ccyntry.findtext("CtryNm")],
                )

    logger.debug(f"GET {ISO_DOWNLOAD_HISTORIC_XML}")
    resp = request.urlopen(ISO_DOWNLOAD_HISTORIC_XML)

    with resp as f:
        root = ET.fromstring(f.read())
        ccytbl = root.find("HstrcCcyTbl")
        for ccyntry in ccytbl.findall("HstrcCcyNtry"):
            code = ccyntry.findtext("Ccy")
            if code in currencies:
                currencies[code].countries.append(ccyntry.findtext("CtryNm"))
            else:
                logger.debug(f"Registered historical currency: {code}")
                try:
                    wdate = datetime.strptime(ccyntry.findtext("WthdrwlDt"), "%Y-%m").date()
                except ValueError as e:
                    logger.warning("invalid WthdrwlDt: %s", e)
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


def read_currencies_data(proto_path, logger):
    """
    read_currencies_data loads the serialized list of Currency objects and
    returns a dictionary whose key is the ISO 4217 alphabetic code and whose
    values are the corresponding Currency objects.
    """

    logger.debug(f"loading currencies from {proto_path}...")

    clist = CurrencyList()
    with open(proto_path, "rb") as f:
        clist.ParseFromString(f.read())

    cmap = {}
    for c in clist.currencies:
        cmap[c.alphabetic_code] = c
    return cmap


def write_currencies_data(proto_path, currencies, logger):
    """
    write_currencies_data serializes a list of Currency objects to the given
    path overwriting the existing list of currencies.
    """

    logger.debug(f"writing {len(currencies)} currencies to {proto_path}...")

    os.makedirs(os.path.dirname(proto_path), exist_ok=True)

    clist = CurrencyList()
    clist.currencies.extend(currencies)
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(clist.SerializeToString())


def write_currencies_site(base_dir, currencies_dict, logger):
    """
    write_currencies_site writes currency API files to the site directory.

    currencies_dict - dictionary of currencies as read from `read_currencies_data`
    """
    clist = CurrencyList()
    clist.currencies.extend(currencies_dict.values())

    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, "currency.json")
    logger.debug(f"writing {len(clist.currencies)} currencies to {json_path}...")

    # write currencies list JSON.
    with open(json_path, "w") as f:
        json.dump(MessageToDict(clist), f)

    # write currencies list CSV.
    csv_path = os.path.join(base_dir, "currency.csv")
    logger.debug(f"writing {len(clist.currencies)} currencies to {csv_path}...")
    csv_fields = [
        "alphabeticCode",
        "numericCode",
        "name",
        "minorUnits",
        "countries",
        "withdrawalDate",
    ]

    with open(csv_path, "w") as f:
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
                    }
                )

    # Write currencies list proto
    proto_path = os.path.join(base_dir, "currency.binpb")
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(clist.SerializeToString())

    # Write individual currencies
    currency_dir = os.path.join(base_dir, "currency")
    os.makedirs(currency_dir, exist_ok=True)

    for c in clist.currencies:
        # Write currency json
        c_json_path = os.path.join(currency_dir, f"{c.alphabetic_code}.json")
        with open(c_json_path, "w") as f:
            logger.debug(f"writing {f.name}...")
            json.dump(MessageToDict(c), f)

        # Write currency csv
        c_csv_path = os.path.join(currency_dir, f"{c.alphabetic_code}.csv")
        with open(c_csv_path, "w") as f:
            logger.debug(f"writing {f.name}...")
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
                }
            )

        # Write currency proto
        c_proto_path = os.path.join(currency_dir, f"{c.alphabetic_code}.binpb")
        with open(c_proto_path, "wb") as f:
            logger.debug(f"writing {f.name}...")
            f.write(c.SerializeToString())
