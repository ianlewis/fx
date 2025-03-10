import os
import json
import os.path
import logging
import shutil
from datetime import datetime, date
from urllib import request
import xml.etree.ElementTree as ET 

from google.protobuf.json_format import MessageToJson
from google.type.date_pb2 import Date

from fx.quote_pb2 import Currency

ISO_DOWNLOAD_XML="https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml"
ISO_DOWNLOAD_HISTORIC_XML="https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-three.xml"


def write_currencies(base_path, currencies, logger):
    currency_path = os.path.join(base_path, "currency")

    logger.debug(f'deleting {currency_path}...')
    shutil.rmtree(currency_path, ignore_errors=True)

    os.makedirs(currency_path, exist_ok=True)
    for code, c in currencies.items():
        with open(os.path.join(currency_path, f'{code}.json'), 'w') as f:
            logger.debug(f'writing {f.name}...')
            f.write(MessageToJson(c))


def get_currencies(logger):
    resp = request.urlopen(ISO_DOWNLOAD_XML)

    currencies = {}
    with resp as f:
        root = ET.fromstring(resp.read())
        ccytbl = root.find("CcyTbl")
        for ccyntry in ccytbl.findall("CcyNtry"):
            code = ccyntry.findtext("Ccy")
            if code in currencies:
                currencies[code].countries.append(ccyntry.findtext("CtryNm"))
            else:
                logger.debug(f'Registered currency: {code}')

                try:
                    minor_units = int(ccyntry.findtext("CcyNm"))
                except ValueError:
                    minor_units = 0

                currencies[code] = Currency(
                    alphabetic_code = code,
                    numeric_code = ccyntry.findtext("CcyNbr"),
                    name = ccyntry.findtext("CcyNm"),
                    minor_units = minor_units,
                    countries = [ccyntry.findtext("CtryNm")],
                )

    resp = request.urlopen(ISO_DOWNLOAD_HISTORIC_XML)

    with resp as f:
        root = ET.fromstring(resp.read())
        ccytbl = root.find("HstrcCcyTbl")
        for ccyntry in ccytbl.findall("HstrcCcyNtry"):
            code = ccyntry.findtext("Ccy") 
            if code in currencies:
                currencies[code].countries.append(ccyntry.findtext("CtryNm"))
            else:
                logger.debug(f'Registered historical currency: {code}')
                try:
                    wdate = datetime.strptime(ccyntry.findtext("WthdrwlDt"), "%Y-%m").date()
                except ValueError as e:
                    logger.warning("invalid WthdrwlDt: %s", e)
                    continue

                currencies[code] = Currency(
                    alphabetic_code = code,
                    numeric_code = ccyntry.findtext("CcyNbr"),
                    name = ccyntry.findtext("CcyNm"),
                    minor_units = 0,
                    withdrawal_date = Date(
                        year=wdate.year,
                        month=wdate.month,
                    )
                )

    return currencies


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger("update_jpy")
    logger.setLevel(logging.DEBUG)

    currencies = get_currencies(logger)
    write_currencies("_site", currencies, logger)
