"""
Diagnóstico POS de Accor: ¿qué POS le corresponde a Argentina y qué monedas acepta?

1. Fetcha /referential/v1/pos/countries?siteCode=all → mapeo país→POS
2. Busca Argentina (AR)
3. Fetcha /referential/v1/pos/{pos}/currencies → currencies disponibles
4. Hace un graphql HotelPageHot con el POS de Argentina + currency=USD → precios

Si Argentina tiene un POS que soporta USD, ese es el mecanismo correcto.

Corre con:
    conda activate crawler
    python .claude/tmp/diag_accor_pos.py
"""

import asyncio
import json
from datetime import datetime, timedelta

hoy = datetime.now()
checkin = (hoy + timedelta(days=21)).strftime("%Y-%m-%d")
checkout = (hoy + timedelta(days=22)).strftime("%Y-%m-%d")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) "
    "Gecko/20100101 Firefox/138.0"
)

GRAPHQL_QUERY = """
query HotelPageHot(
  $hotelOffersHotelId: String!,
  $dateIn: Date!,
  $dateOut: Date!,
  $nbAdults: PositiveInt!,
  $childrenAges: [NonNegativeInt]!,
  $selectionStep: Int!,
  $countryMarket: String,
  $currency: CurrencyISOCode,
  $hideMemberRate: Boolean,
  $offersSelectionFilters: HotelOfferFiltersInput,
  $concession: String,
  $use: UseType,
  $selection: [InputGroupRoomSelection]
) {
  hotelOffers(
    hotelId: $hotelOffersHotelId
    dateIn: $dateIn
    dateOut: $dateOut
    nbAdults: $nbAdults
    childrenAges: $childrenAges
    selectionStep: $selectionStep
    countryMarket: $countryMarket
    currency: $currency
    hideMemberRate: $hideMemberRate
    offersSelectionFilters: $offersSelectionFilters
    concession: $concession
    use: $use
    selection: $selection
  ) {
    offers {
      ...RoomOffer
    }
  }
}

fragment RoomOffer on HotelOffer {
  id
  name
  prices {
    perNight {
      value
      currencyCode
      taxes {
        included
        value
        currencyCode
      }
    }
  }
}
"""


async def fetch_with_firefox(url: str, method="GET", body=None, headers_extra=None) -> tuple:
    """Hace un fetch directo usando Playwright Firefox (bypass TLS fingerprinting)."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="en-US")
        page = await context.new_page()

        result = {}

        async def handle_route(route, request):
            await route.continue_()

        await page.route("**/*", handle_route)

        # Usamos page.evaluate para hacer fetch desde el contexto del browser
        # (así los headers del browser se incluyen automáticamente)
        script = f"""
        async () => {{
            const options = {{
                method: '{method}',
                headers: {{
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...{json.dumps(headers_extra or {})},
                }},
                {f"body: JSON.stringify({json.dumps(body)})," if body else ""}
            }};
            const resp = await fetch('{url}', options);
            const text = await resp.text();
            return {{ status: resp.status, body: text }};
        }}
        """

        # Primero navegamos a accor para establecer el contexto de cookies
        await page.goto("https://all.accor.com", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        res = await page.evaluate(script)
        await browser.close()
        return res["status"], res["body"]


async def main():
    print("=" * 70)
    print("1. FETCHING POS/COUNTRIES (mapeo país → POS)")
    print("=" * 70)
    status, body = await fetch_with_firefox(
        "https://api.accor.com/referential/v1/pos/countries?siteCode=all"
    )
    print(f"Status: {status}")

    if status == 200:
        data = json.loads(body)
        # Buscar Argentina
        countries = data if isinstance(data, list) else data.get("countries", data.get("data", []))
        print(f"Total países: {len(countries) if isinstance(countries, list) else 'N/A'}")

        ar_entries = []
        if isinstance(countries, list):
            for item in countries:
                if isinstance(item, dict):
                    # Puede ser {country: "AR", pos: "argentina"} o similar
                    country_code = item.get("code", item.get("country", item.get("countryCode", "")))
                    pos_code = item.get("pos", item.get("posCode", item.get("market", "")))
                    name = item.get("name", item.get("countryName", ""))
                    if "AR" in str(country_code).upper() or "ARGENTIN" in str(name).upper():
                        ar_entries.append(item)

        if ar_entries:
            print(f"\nArgentina encontrada:")
            for e in ar_entries:
                print(f"  {json.dumps(e, indent=2)}")
        else:
            print("\nArgentina NO encontrada en lista. Primeros 5 entries:")
            if isinstance(countries, list):
                for item in countries[:5]:
                    print(f"  {json.dumps(item)}")
            else:
                print(f"  Estructura: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                print(f"  Raw (primeros 500 chars): {body[:500]}")
    else:
        print(f"Error: {body[:200]}")

    print()
    print("=" * 70)
    print("2. FETCHING CURRENCIES PARA POS 'argentina' y 'united-states'")
    print("=" * 70)

    for pos_code in ["argentina", "united-states", "AR", "ar", "USA", "us"]:
        status, body = await fetch_with_firefox(
            f"https://api.accor.com/referential/v1/pos/{pos_code}/currencies?groupByContinent=true"
        )
        if status == 200:
            try:
                data = json.loads(body)
                # Buscar USD
                body_str = json.dumps(data)
                has_usd = "USD" in body_str
                print(f"  POS '{pos_code}': HTTP 200, USD disponible: {has_usd}")
                if has_usd:
                    print(f"    Currencies (filtrado USD):")
                    if isinstance(data, list):
                        for c in data:
                            if "USD" in str(c):
                                print(f"      {c}")
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if "USD" in str(v):
                                print(f"      {k}: {v}")
            except Exception as e:
                print(f"  POS '{pos_code}': HTTP 200, parse error: {e}")
        else:
            print(f"  POS '{pos_code}': HTTP {status}")

    print()
    print("=" * 70)
    print("3. GRAPHQL HotelPageHot CON DISTINTOS countryMarket + USD")
    print("=" * 70)

    # Probar distintos country markets que podrían dar USD
    markets_to_try = [
        ("AR", "USD"),   # Argentina directamente
        ("US", "USD"),   # USA
        ("GB", "USD"),   # Gran Bretaña + USD (el que usa el scraper pero con USD forzado)
    ]

    for country_market, currency in markets_to_try:
        print(f"\n  Probando countryMarket='{country_market}' + currency='{currency}'...")
        payload = {
            "operationName": "HotelPageHot",
            "variables": {
                "dateIn": checkin,
                "dateOut": checkout,
                "nbAdults": 2,
                "childrenAges": [],
                "selectionStep": 0,
                "hotelOffersHotelId": "B8G3",
                "countryMarket": country_market,
                "currency": currency,
                "offersSelectionFilters": {
                    "cancellationPolicies": None,
                    "isAccessible": False,
                    "mealPlans": None,
                },
                "concession": None,
                "use": "NIGHT",
                "hideMemberRate": False,
                "selection": [],
                "totalRoomInBasket": 1,
            },
            "query": GRAPHQL_QUERY,
        }

        status, body = await fetch_with_firefox(
            "https://api.accor.com/bff/v1/graphql",
            method="POST",
            body=payload,
        )
        print(f"  HTTP {status}")
        if status == 200:
            try:
                data = json.loads(body)
                offers = (
                    data.get("data", {})
                    .get("hotelOffers", {})
                    .get("offers", [])
                )
                print(f"  Offers count: {len(offers)}")
                if offers:
                    for offer in offers[:3]:
                        name = offer.get("name", "?")
                        prices = offer.get("prices", {})
                        per_night = prices.get("perNight", {})
                        value = per_night.get("value", "?")
                        curr = per_night.get("currencyCode", "?")
                        taxes = per_night.get("taxes", {})
                        tax_included = taxes.get("included", "?") if isinstance(taxes, dict) else "?"
                        tax_value = taxes.get("value", "?") if isinstance(taxes, dict) else "?"
                        print(f"    '{name}': {curr} {value} | taxes_included={tax_included} tax_value={tax_value}")
            except Exception as e:
                print(f"  Parse error: {e}")
                print(f"  Body: {body[:500]}")
        else:
            print(f"  Body: {body[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
