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

import os
import csv
import json

from google.protobuf.json_format import MessageToDict

from quote_pb2 import Provider


def update_providers(base_dir, providers, logger):

    provider_path = os.path.join(
        base_dir,
        "provider",
    )

    os.makedirs(provider_path, exist_ok=True)

    for provider in providers:
        logger.info(f"Updating provider {provider.code}...")

        json_path = os.path.join(provider_path, f"{provider.code}.json")
        csv_path = os.path.join(provider_path, f"{provider.code}.csv")

        provider_dict = MessageToDict(
            Provider(
                code=provider.code,
                name=provider.name,
            )
        )
        with open(json_path, "w") as f:
            json.dump(provider_dict, f)

        with open(csv_path, "w") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["code", "name"],
            )
            w.writeheader()
            w.writerow(provider_dict)
