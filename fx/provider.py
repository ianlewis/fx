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

"""Currency conversion provider functions."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

from google.protobuf.json_format import MessageToDict

from fx.provider_pb2 import ProviderList  # type: ignore[attr-defined]


def write_providers_site(
    base_dir: str | Path,
    providers: list[Any],
    logger: logging.Logger,
) -> None:
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

    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    json_path = base_path.joinpath("provider.json")
    logger.debug(
        "writing %s providers to %s...",
        len(plist.providers),
        json_path,
    )

    # Write providers list JSON.
    with json_path.open("w") as f:
        json.dump(MessageToDict(plist), f, separators=(",", ":"))

    # Write providers list CSV.
    csv_path = base_path.joinpath("provider.csv")
    logger.debug(
        "writing %s providers to %s...",
        len(plist.providers),
        csv_path,
    )
    csv_fields = ["name", "code"]

    with csv_path.open("w") as f:
        if len(plist.providers) > 0:
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            for p in plist.providers:
                w.writerow(
                    {
                        "name": p.name,
                        "code": p.code,
                    },
                )

    # Write providers list protobuf
    proto_path = base_path.joinpath("provider.binpb")
    with proto_path.open("wb") as f:
        logger.debug("writing %s...", f.name)
        f.write(plist.SerializeToString())

    # Write individual providers
    provider_path = base_path.joinpath("provider")
    provider_path.mkdir(parents=True, exist_ok=True)

    for p in plist.providers:
        # Write provider JSON
        p_json_path = provider_path.joinpath(f"{p.code}.json")
        with p_json_path.open("w") as f:
            logger.debug("writing %s...", f.name)
            json.dump(MessageToDict(p), f, separators=(",", ":"))

        # Write provider CSV
        p_csv_path = provider_path.joinpath(f"{p.code}.csv")
        with p_csv_path.open("w") as f:
            logger.debug("writing %s...", f.name)
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            w.writerow(
                {
                    "name": p.name,
                    "code": p.code,
                },
            )

        # Write provider protobuf
        p_proto_path = provider_path.joinpath(f"{p.code}.binpb")
        with p_proto_path.open("wb") as f:
            logger.debug("writing %s...", f.name)
            f.write(p.SerializeToString())
