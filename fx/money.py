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

from google.type.money_pb2 import Money
from google.protobuf.json_format import MessageToDict


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


def dict_to_str(d):
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
    return dict_to_str(MessageToDict(m))
