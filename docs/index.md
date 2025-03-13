# fx.ianlewis.org

`fx.ianlewis.org` is a currency conversion API. It currently supports MUFG published rates between 31 currencies and JPY.

## Data Types & Endpoints

The following sections outline the various data types available in the API.

- [Swagger UI](https://petstore.swagger.io/?url=https://fx.ianlewis.org/openapi.yaml)
- [Redoc](https://redocly.github.io/redoc/?url=https://fx.ianlewis.org/openapi.yaml)

The full OpenAPI definition can be viewed at [/openapi.yaml](/openapi.yaml).

### Provider

Currency exchange provider information can be retrieved via the provider endpoint. The `Provider` object's format is defined in [`provider.proto`](https://github.com/ianlewis/fx/blob/main/fx/provider.proto).

[/v1/provider.json](/v1/provider.json)

```json
{
  "providers": [
    {
      "code": "MUFG",
      "name": "MUFG Bank, Ltd."
    }
  ]
}
```

Individual providers can be accessed via their code.

[/v1/provider/MUFG.json](/v1/provider/MUFG.json)

```json
{
  "code": "MUFG",
  "name": "MUFG Bank, Ltd."
}
```

### Currencies

Currency information can be retrieved via the currency endpoint using the currency's ISO 4217 alphabetic code. The `Currency` object's format is defined in [`currency.proto`](https://github.com/ianlewis/fx/blob/main/fx/currency.proto).

[/v1/currency.json](/v1/currency.json)

```json
{
  "currencies": [
    {
      "alphabeticCode": "AFN",
      "numericCode": "971",
      "name": "Afghani",
      "minorUnits": 2,
      "countries": ["AFGHANISTAN"]
    }
    // ...
  ]
}
```

[/v1/currency/USD.json](/v1/currency/USD.json)

```json
{
  "alphabeticCode": "USD",
  "numericCode": "840",
  "name": "US Dollar",
  "countries": [
    "AMERICAN SAMOA",
    "BONAIRE, SINT EUSTATIUS AND SABA",
    "BRITISH INDIAN OCEAN TERRITORY (THE)",
    "ECUADOR",
    "EL SALVADOR",
    "GUAM",
    "HAITI",
    "MARSHALL ISLANDS (THE)",
    "MICRONESIA (FEDERATED STATES OF)",
    "NORTHERN MARIANA ISLANDS (THE)",
    "PALAU",
    "PANAMA",
    "PUERTO RICO",
    "TIMOR-LESTE",
    "TURKS AND CAICOS ISLANDS (THE)",
    "UNITED STATES MINOR OUTLYING ISLANDS (THE)",
    "UNITED STATES OF AMERICA (THE)",
    "VIRGIN ISLANDS (BRITISH)",
    "VIRGIN ISLANDS (U.S.)"
  ]
}
```

### Quotes

Currency exchange rate quotes can be retrieved via a provider's quote endpoint. The `Quote` object's format is defined in [`quote.proto`](https://github.com/ianlewis/fx/blob/main/fx/quote.proto).

Quotes for a single day can be accessed by date.

[/v1/provider/MUFG/quote/USD/JPY/2025/03/11.json](/v1/provider/MUFG/quote/USD/JPY/2025/03/11.json)

```json
{
  "providerCode": "MUFG",
  "date": {
    "year": 2025,
    "month": 3,
    "day": 11
  },
  "baseCurrencyCode": "USD",
  "quoteCurrencyCode": "JPY",
  "ask": {
    "currencyCode": "JPY",
    "units": "147",
    "nanos": 680000000
  },
  "bid": {
    "currencyCode": "JPY",
    "units": "145",
    "nanos": 680000000
  },
  "mid": {
    "currencyCode": "JPY",
    "units": "146",
    "nanos": 680000000
  }
}
```

## Formats

Each endpoint can be accessed in JSON (.json), CSV (.csv), and Protocol Buffers Wire format (.binpb) via their associated file extension.

[/v1/provider/MUFG/quote/USD/JPY/2025/03.csv](/v1/provider/MUFG/quote/USD/JPY/2025/03.csv)

```csv
date,providerCode,baseCurrencyCode,quoteCurrencyCode,ask,bid,mid
2025/03/03,MUFG,USD,JPY,151.56,149.56,150.56
2025/03/04,MUFG,USD,JPY,150.26,148.26,149.26
2025/03/05,MUFG,USD,JPY,150.87,148.87,149.87
2025/03/06,MUFG,USD,JPY,150.25,148.25,149.25
2025/03/07,MUFG,USD,JPY,149.07,147.07,148.07
2025/03/10,MUFG,USD,JPY,148.38,146.38,147.38
2025/03/11,MUFG,USD,JPY,147.68,145.68,146.68
2025/03/12,MUFG,USD,JPY,149.08,147.08,148.08
...
```
