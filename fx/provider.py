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

from fx.provider_pb2 import ProviderList


def write_providers_site(base_dir, providers, logger):
    """
    write_provider_site writes provider API files to the site directory.

    providers - a list of currently registered providers.
    """
    plist = ProviderList()
    for p in providers:
        plist.providers.add(
            name=p.name,
            code=p.code,
            supported_base_currencies=p.supported_base_currencies,
            supported_quote_currencies=p.supported_quote_currencies,
        )

    os.makedirs(base_dir, exist_ok=True)

    json_path = os.path.join(base_dir, "provider.json")
    logger.debug(f"writing {len(plist.providers)} providers to {json_path}...")

    # write providers list JSON.
    with open(json_path, "w") as f:
        json.dump(MessageToDict(plist), f)

    # write providers list CSV.
    csv_path = os.path.join(base_dir, "provider.csv")
    logger.debug(f"writing {len(plist.providers)} providers to {csv_path}...")
    csv_fields = ["name", "code"]

    with open(csv_path, "w") as f:
        if len(plist.providers) > 0:
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            for p in plist.providers:
                w.writerow(
                    {
                        "name": p.name,
                        "code": p.code,
                    }
                )

    # Write providers list proto
    proto_path = os.path.join(base_dir, "provider.binpb")
    with open(proto_path, "wb") as f:
        logger.debug(f"writing {f.name}...")
        f.write(plist.SerializeToString())

    # Write individual providers
    provider_dir = os.path.join(base_dir, "provider")
    os.makedirs(provider_dir, exist_ok=True)

    for p in plist.providers:
        # Write provider json
        p_json_path = os.path.join(provider_dir, f"{p.code}.json")
        with open(p_json_path, "w") as f:
            logger.debug(f"writing {f.name}...")
            json.dump(MessageToDict(p), f)

        # Write provider csv
        p_csv_path = os.path.join(provider_dir, f"{p.code}.csv")
        with open(p_csv_path, "w") as f:
            logger.debug(f"writing {f.name}...")
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            w.writerow(
                {
                    "name": p.name,
                    "code": p.code,
                }
            )

        # Write provider proto
        p_proto_path = os.path.join(provider_dir, f"{p.code}.binpb")
        with open(p_proto_path, "wb") as f:
            logger.debug(f"writing {f.name}...")
            f.write(p.SerializeToString())
