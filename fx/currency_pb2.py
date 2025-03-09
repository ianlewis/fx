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

# flake8: noqa

# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: fx/currency.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.type import date_pb2 as google_dot_type_dot_date__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x11\x66x/currency.proto\x1a\x16google/type/date.proto"\x9b\x01\n\x08\x43urrency\x12\x17\n\x0f\x61lphabetic_code\x18\x01 \x01(\t\x12\x14\n\x0cnumeric_code\x18\x02 \x01(\t\x12\x0c\n\x04name\x18\x03 \x01(\t\x12\x13\n\x0bminor_units\x18\x04 \x01(\x05\x12\x11\n\tcountries\x18\x05 \x03(\t\x12*\n\x0fwithdrawal_date\x18\x06 \x01(\x0b\x32\x11.google.type.Date"-\n\x0c\x43urrencyList\x12\x1d\n\ncurrencies\x18\x01 \x03(\x0b\x32\t.Currencyb\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "fx.currency_pb2", globals())
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _CURRENCY._serialized_start = 46
    _CURRENCY._serialized_end = 201
    _CURRENCYLIST._serialized_start = 203
    _CURRENCYLIST._serialized_end = 248
# @@protoc_insertion_point(module_scope)
