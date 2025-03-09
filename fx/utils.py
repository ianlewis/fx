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

from datetime import date

from dateutil.relativedelta import relativedelta
from google.type.money_pb2 import Money
from google.protobuf.json_format import MessageToDict


def dateIterator(from_date=None, to_date=None, delta=relativedelta(days=1)):
    from_date = from_date or date.today()
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date = from_date + delta
    return


def date_msg_to_str(d):
    return date_dict_to_str(MessageToDict(d))


def date_dict_to_str(d):
    year = d.get("year")
    month = d.get("month")
    day = d.get("day")

    if not year:
        return None

    if day:
        if not month:
            raise ValueError(f"invalid date dict: {d}")
        return "{:04d}/{:02d}/{:02d}".format(year, month, day)

    if month:
        return "{:04d}/{:02d}".format(year, month)

    return "{:04d}".format(year)


def str_to_money(code, s):
    parts = s.split(".")
    if len(parts) > 2:
        raise ValueError(f"invalid number: {s}")

    units = int(parts[0])
    nanos = 0

    if len(parts) > 1:
        nanos_str = parts[1] + "0" * (9 - len(parts[1]))
        if len(nanos_str) > 9:
            nanos_str = nanos_str[:9]

        nanos = int(nanos_str)
        if nanos < 0:
            raise ValueError(f"invalid number: {s}")

    # If units is negative (or zero) nanos must also be negative (or zero).
    if units < 0:
        nanos = -1 * nanos

    return Money(
        currency_code=code,
        units=units,
        nanos=nanos,
    )


def money_dict_to_str(d):
    if not d:
        return None

    n = str(d.get("units", 0))

    # nanos might have been negative but is always positive in the string
    # representation.
    nanos = d.get("nanos", 0)
    if nanos < 0:
        nanos = -1 * nanos

    n += ".{:09d}".format(nanos).rstrip("0")

    return n


def money_to_str(m):
    if not m:
        return None
    return money_dict_to_str(MessageToDict(m))
