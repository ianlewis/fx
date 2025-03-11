# fx.ianlewis.org

`fx.ianlewis.org` is a currency conversion API. It currently supports MUFG published rates between 31 currencies and JPY.

## Provider

Currency exchange provider information can be retrieved via the provider endpoint.

<https://fx.ianlewis.org/v1/provider/MUFG.json>

```json
{
  "code": "MUFG",
  "name": "MUFG Bank, Ltd."
}
```

## Currencies

Currency information can be retrieved via the currency endpoint using the currency's ISO 4217 alphabetic code.

<https://fx.ianlewis.org/v1/currency/USD.json>

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

## Quotes

Currency exchange rate quotes can be retrieved via a provider's quote endpoint. The `Quote` object's format is defined in [`quote.proto`](https://github.com/ianlewis/fx/blob/main/fx/quote.proto).

<https://fx.ianlewis.org/v1/provider/MUFG/quote/USD/JPY/2024/03/11.json>

```json
[
  {
    "providerCode": "MUFG",
    "date": {
      "year": 2024,
      "month": 3,
      "day": 11
    },
    "baseCurrencyCode": "USD",
    "quoteCurrencyCode": "JPY",
    "ask": {
      "currencyCode": "JPY",
      "units": "147",
      "nanos": 820000000
    },
    "bid": {
      "currencyCode": "JPY",
      "units": "145",
      "nanos": 820000000
    },
    "mid": {
      "currencyCode": "JPY",
      "units": "146",
      "nanos": 820000000
    }
  }
]
```
