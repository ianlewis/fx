# `fx.ianlewis.org`

[![tests](https://github.com/ianlewis/fx/actions/workflows/pull_request.tests.yml/badge.svg)](https://github.com/ianlewis/fx/actions/workflows/pull_request.tests.yml)
[![Netlify Status](https://api.netlify.com/api/v1/badges/657fceaf-8b71-41dc-85ec-3f9d26a573a5/deploy-status)](https://app.netlify.com/sites/fx-ianlewis-org/deploys)

`fx` is a simple currency exchange rate API. It currently supports MUFG
published rates between 31 currencies and JPY.

Full API documentation can be found at
[`https://fx.ianlewis.org/`](https://fx.ianlewis.org/).

The API is a static file API. Canonical data is stored in [Protocol
Buffers](https://protobuf.dev/) format. API static files are built at deploy
time.
