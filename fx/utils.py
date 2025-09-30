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

"""Utilities used throughout fx."""

from collections.abc import Iterator
from datetime import date

from dateutil.relativedelta import relativedelta
from google.protobuf.json_format import MessageToDict
from google.type.money_pb2 import Money


def date_iterator(
    from_date: date | None = None,
    to_date: date | None = None,
    delta: relativedelta | None = None,
) -> Iterator[date]:
    """
    Generate dates from `from_date` to `to_date` with step `delta`.

    If `from_date` is None, today is used. If `to_date` is None, the iterator is
    infinite. Both `from_date` and `to_date` are inclusive.

    If `delta` is None, a delta of one day is used.
    """
    if delta is None:
        delta = relativedelta(days=1)
    # Timezone aware is not necessary here.
    from_date = from_date or date.today()  # noqa: DTZ011
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date = from_date + delta


def date_msg_to_str(d: dict) -> str | None:
    """Convert a Date protobuf message to a string."""
    return date_dict_to_str(MessageToDict(d))


def date_dict_to_str(d: dict) -> str | None:
    """Convert a Date protobuf message dict to a string."""
    year = d.get("year")
    month = d.get("month")
    day = d.get("day")

    if not year:
        return None

    if day:
        if not month:
            msg = f"invalid date dict: {d}"
            raise ValueError(msg)
        return f"{year:04d}/{month:02d}/{day:02d}"

    if month:
        return f"{year:04d}/{month:02d}"

    return f"{year:04d}"


def str_to_money(code: str, s: str) -> Money:
    """
    Convert a string to a Money protobuf message.

    `code` is the ISO 4217 currency code, e.g. "USD".

    The string `s` should be a decimal representation of the amount, e.g. "123.45". If
    the string is invalid a ValueError is raised.
    """
    parts = s.split(".")
    max_parts = 2
    if len(parts) > max_parts:
        msg = f"invalid number: {s}"
        raise ValueError(msg)

    units = int(parts[0])
    nanos = 0

    if len(parts) > 1:
        nanos_str = parts[1] + "0" * (9 - len(parts[1]))
        max_nanos_decimals = 9
        if len(nanos_str) > max_nanos_decimals:
            nanos_str = nanos_str[:max_nanos_decimals]

        nanos = int(nanos_str)
        if nanos < 0:
            msg = f"invalid number: {s}"
            raise ValueError(msg)

    # If units is negative (or zero) nanos must also be negative (or zero).
    if units < 0:
        nanos = -1 * nanos

    return Money(
        currency_code=code,
        units=units,
        nanos=nanos,
    )


def money_dict_to_str(d: dict) -> str | None:
    """
    Convert a Money protobuf message dict to a string.

    The string is a decimal representation of the amount, e.g. "123.45".
    """
    if not d:
        return None

    n = str(d.get("units", 0))

    # nanos might have been negative but is always positive in the string
    # representation.
    nanos = d.get("nanos", 0)
    if nanos < 0:
        nanos = -1 * nanos

    n += f".{nanos:09d}".rstrip("0")

    return n


def money_to_str(m: Money) -> str | None:
    """
    Convert a Money protobuf message to a string.

    The string is a decimal representation of the amount, e.g. "123.45".
    """
    if not m:
        return None
    return money_dict_to_str(MessageToDict(m))
