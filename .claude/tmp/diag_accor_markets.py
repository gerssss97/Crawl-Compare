"""
Diagnóstico: ¿qué POS/countryMarket da USD sin taxes en Accor?

Estrategia: interceptar el request graphql HotelPageHot (que sí tiene auth JWT),
modificar `countryMarket` y `currency` en el body antes de enviarlo,
y capturar la response con los precios reales.

Probamos: AR/USD, US/USD, GB/USD, y el default GB/EUR para comparar.

Corre con:
    conda activate crawler
    python .claude/tmp/diag_accor_markets.py
"""

import asyncio
import json
from datetime import datetime, timedelta

hoy = datetime.now()
checkin = (hoy + timedelta(days=21)).strftime("%Y-%m-%d")
checkout = (hoy + timedelta(days=22)).strftime("%Y-%m-%d")

BASE_URL = (
    f"https://all.accor.com/booking/en/accor/hotel/B8G3"
    f"?checkin={checkin}"
    f"&currency=USD"
    f"&partya=1"
    f"&viewtype=roomrate"
    f"&resultViewType=mda"
    f"&dateIn={checkin}"
    f"&dateOut={checkout}"
    f"&compositions=2"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) "
    "Gecko/20100101 Firefox/138.0"
)
WAIT_FOR_SEL = ".hotel-accommodations-offers__item-title"
PRECIO_SEL   = ".offer-price--alternative .offer-price__amount"

ACCOR_DOMAINS = ["api.accor.com", "all.accor.com/bff"]


def ts():
    return datetime.now().strftime("%H:%M:%S")


async def run_test(p, test_name: str, country_market: str, currency: str):
    """
    Abre el browser una sola vez, intercepta HotelPageHot y sobreescribe
    countryMarket + currency. Captura la response con los precios reales.
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"  countryMarket='{country_market}', currency='{currency}'")
    print(f"{'='*60}")

    browser = await p.firefox.launch(headless=True)
    try:
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
        )
        page = await context.new_page()

        hotpageshot_response = {}

        async def intercept(route, request):
            url = request.url

            # Interceptar solo el graphql que pide precios (HotelPageHot)
            if "graphql" in url:
                try:
                    body_bytes = request.post_data_buffer
                    if body_bytes:
                        body_json = json.loads(body_bytes.decode("utf-8"))
                        op = body_json.get("operationName", "")

                        if op == "HotelPageHot":
                            # Modificar countryMarket y currency
                            original_market = body_json.get("variables", {}).get("countryMarket", "?")
                            original_currency = body_json.get("variables", {}).get("currency", "?")
                            print(f"  [INTERCEPTED] HotelPageHot: market={original_market}, currency={original_currency}")

                            body_json["variables"]["countryMarket"] = country_market
                            body_json["variables"]["currency"] = currency
                            new_body = json.dumps(body_json)

                            print(f"  [MODIFIED]    HotelPageHot: market={country_market}, currency={currency}")

                            # Continuar con el body modificado
                            await route.continue_(post_data=new_body)
                            return
                except Exception as e:
                    print(f"  [INTERCEPT ERR] {e}")

            await route.continue_()

        await page.route("**/*", intercept)

        # Capturar la response del graphql HotelPageHot
        async def on_response(response):
            if "graphql" in response.url:
                try:
                    body = await response.body()
                    data = json.loads(body.decode("utf-8"))
                    op_check = data.get("data", {})
                    if "hotelOffers" in op_check:
                        hotpageshot_response["data"] = data
                        print(f"  [CAPTURED] hotelOffers response")
                except Exception:
                    pass

        page.on("response", on_response)

        print(f"  [{ts()}] Navegando...")
        await page.goto(BASE_URL, wait_until="networkidle")
        print(f"  [{ts()}] networkidle OK")

        # Esperar que los rooms aparezcan
        try:
            await page.wait_for_selector(WAIT_FOR_SEL, timeout=20000)
            print(f"  [{ts()}] Rooms en DOM ✓")
        except Exception as e:
            print(f"  [{ts()}] TIMEOUT rooms: {e}")

        # Esperar precios
        try:
            await page.wait_for_selector(PRECIO_SEL, timeout=15000)
            print(f"  [{ts()}] Precios en DOM ✓")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [{ts()}] TIMEOUT precios: {e}")

        # Leer precios del DOM
        precio_elements = await page.query_selector_all(PRECIO_SEL)
        print(f"\n  PRECIOS EN DOM ({len(precio_elements)} elementos):")
        for i, el in enumerate(precio_elements[:6]):
            text = await el.text_content()
            print(f"    [{i}] {text.strip()!r}")

        # Leer la response de graphql si la capturamos
        if hotpageshot_response:
            print(f"\n  PRECIOS EN GRAPHQL RESPONSE:")
            offers = (
                hotpageshot_response["data"]
                .get("data", {})
                .get("hotelOffers", {})
                .get("offers", [])
            )
            print(f"  Offers: {len(offers)}")
            for offer in offers[:5]:
                name = offer.get("name", "?")[:50]
                per_night = offer.get("prices", {}).get("perNight", {})
                value = per_night.get("value", "?")
                curr = per_night.get("currencyCode", "?")
                taxes = per_night.get("taxes", {})
                t_included = taxes.get("included", "?") if taxes else "?"
                t_value = taxes.get("value", "?") if taxes else "?"
                print(f"    '{name}': {curr} {value} | taxes_included={t_included} taxes_value={t_value}")
        else:
            print(f"\n  GRAPHQL RESPONSE: no capturada (posible que el interceptor no la modificó a tiempo)")
            # Intentar leer desde el DOM como fallback
            html = await page.content()
            usd_c = html.count("US$") + html.count('"USD"')
            eur_c = html.count("€") + html.count('"EUR"')
            print(f"  DOM: US$/USD={usd_c}, €/EUR={eur_c}")

    finally:
        await browser.close()


async def main():
    print(f"Fechas: {checkin} → {checkout}")
    print(f"Hotel: Faena (B8G3)")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # Test 1: default (sin interceptar) — para tener baseline
        # No necesitamos correrlo de nuevo, sabemos que es GB/EUR

        # Test 2: AR/USD — Argentina + USD
        await run_test(p, "Argentina POS + USD", "AR", "USD")

        # Test 3: US/USD — USA POS + USD (el que usamos antes con taxes)
        await run_test(p, "USA POS + USD", "US", "USD")

        # Test 4: GB/USD — UK POS forzado USD
        await run_test(p, "UK POS + USD forzado", "GB", "USD")

    print("\n" + "="*60)
    print("CONCLUSIÓN: comparar precios entre tests para identificar")
    print("qué combinación da el mismo precio que ve el usuario (~$503)")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
