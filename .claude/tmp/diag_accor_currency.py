"""
Diagnóstico: mecanismo de moneda en Accor (all.accor.com)

Abre el Faena con Firefox headless, captura:
  - Todos los cookies seteados por Accor
  - Todos los requests a api.accor.com con sus URLs y body (si son POST)
  - El valor de `pos` en cada request de pricing
  - El currency que devuelve el DOM

Corre con:
    conda activate crawler
    python .claude/tmp/diag_accor_currency.py
"""

import asyncio
import json
import re
from datetime import datetime, timedelta

# Fechas futuras (3 semanas a partir de hoy)
hoy = datetime.now()
checkin = (hoy + timedelta(days=21)).strftime("%Y-%m-%d")
checkout = (hoy + timedelta(days=22)).strftime("%Y-%m-%d")

URL = (
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

# Dominios de Accor que nos interesan
ACCOR_DOMAINS = ["api.accor.com", "accor.com/api", "accorhotels", "all.accor.com/bff"]


def ts():
    return datetime.now().strftime("%H:%M:%S")


async def main():
    from playwright.async_api import async_playwright

    print(f"[{ts()}] URL de prueba:")
    print(f"  {URL}")
    print()

    captured_requests = []

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
        )

        # ---- Interceptar requests y capturar body de POSTs ----
        async def intercept_route(route, request):
            url = request.url
            is_accor = any(d in url for d in ACCOR_DOMAINS)

            if is_accor:
                body_text = None
                try:
                    body_bytes = request.post_data_buffer
                    if body_bytes:
                        body_text = body_bytes.decode("utf-8", errors="replace")
                except Exception:
                    pass

                captured_requests.append({
                    "method": request.method,
                    "url": url,
                    "body": body_text,
                    "headers": dict(request.headers),
                })

            await route.continue_()

        await context.route("**/*", intercept_route)

        page = await context.new_page()

        # ---- Escuchar responses de Accor ----
        response_data = []

        def on_response(resp):
            if any(d in resp.url for d in ACCOR_DOMAINS):
                print(f"[{ts()}] << {resp.status:3d}  {resp.url[:120]}")

        page.on("response", on_response)

        print(f"[{ts()}] Navegando...")
        await page.goto(URL, wait_until="networkidle")
        print(f"[{ts()}] networkidle. URL final: {page.url}")

        # ---- Esperar rooms ----
        try:
            print(f"[{ts()}] Esperando habitaciones...")
            await page.wait_for_selector(WAIT_FOR_SEL, timeout=20000)
            print(f"[{ts()}] Habitaciones en DOM ✓")
        except Exception as e:
            print(f"[{ts()}] TIMEOUT esperando habitaciones: {e}")

        # ---- Esperar precios ----
        try:
            print(f"[{ts()}] Esperando precios...")
            await page.wait_for_selector(PRECIO_SEL, timeout=15000)
            print(f"[{ts()}] Precios en DOM ✓")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[{ts()}] TIMEOUT esperando precios: {e}")

        # ---- Capturar cookies ----
        cookies = await context.cookies()

        # ---- Capturar símbolos de moneda en DOM ----
        html = await page.content()

        print()
        print("=" * 70)
        print("COOKIES SETEADAS POR ACCOR")
        print("=" * 70)

        accor_cookies = [c for c in cookies if "accor" in c["domain"].lower() or "accor" in c["name"].lower()]
        all_relevant = [c for c in cookies if any(
            k in c["name"].lower() for k in ["currency", "locale", "pos", "lang", "region", "market"]
        )]
        other_cookies = [c for c in cookies if c not in accor_cookies and c not in all_relevant]

        print("\n[cookies con 'accor' en nombre o dominio]")
        for c in accor_cookies:
            print(f"  {c['name'][:50]:<50} = {c['value'][:80]}")

        print("\n[cookies con currency/locale/pos/lang/region/market en nombre]")
        for c in all_relevant:
            if c not in accor_cookies:
                print(f"  {c['name'][:50]:<50} = {c['value'][:80]}")

        print(f"\n[resto de cookies: {len(other_cookies)} cookies, dominios únicos]")
        domains = {c["domain"] for c in other_cookies}
        for d in sorted(domains):
            dc = [c for c in other_cookies if c["domain"] == d]
            print(f"  {d}: {[c['name'] for c in dc]}")

        print()
        print("=" * 70)
        print("REQUESTS A API.ACCOR / BFF")
        print("=" * 70)

        for req in captured_requests:
            method = req["method"]
            url    = req["url"]
            body   = req["body"]

            print(f"\n  {method} {url[:120]}")

            # Extraer pos de la URL
            pos_match = re.search(r"pos=([a-z\-]+)", url)
            if pos_match:
                print(f"    >>> POS en URL: {pos_match.group(1)}")

            # Extraer currency de la URL
            cur_match = re.search(r"currency=([A-Z]+)", url, re.IGNORECASE)
            if cur_match:
                print(f"    >>> currency en URL: {cur_match.group(1)}")

            # Headers relevantes
            rel_headers = {k: v for k, v in req["headers"].items()
                           if any(h in k.lower() for h in ["cookie", "accept-lang", "x-accor", "x-pos", "currency", "origin"])}
            if rel_headers:
                print(f"    headers relevantes: {json.dumps(rel_headers, indent=6)}")

            # Body POST: buscar pos, currency, locale
            if body:
                body_short = body[:500]
                print(f"    body (primeros 500 chars): {body_short}")
                for key in ["pos", "currency", "locale", "market"]:
                    matches = re.findall(rf'"{key}"\s*:\s*"([^"]+)"', body, re.IGNORECASE)
                    if matches:
                        print(f"    >>> '{key}' en body: {matches}")

        print()
        print("=" * 70)
        print("MONEDA VISIBLE EN DOM")
        print("=" * 70)

        # Buscar símbolos y valores de precio en el HTML
        precio_elements = await page.query_selector_all(PRECIO_SEL)
        print(f"\nElementos '{PRECIO_SEL}': {len(precio_elements)}")
        for i, el in enumerate(precio_elements[:5]):
            text = await el.text_content()
            print(f"  [{i}] '{text.strip()}'")

        # Buscar "US$", "USD", "€", "EUR" en el HTML completo
        usd_count = html.count("US$") + html.count("USD")
        eur_count = html.count("€") + html.count("EUR")
        ars_count = html.count("ARS") + html.count("$")
        print(f"\nOcurrencias en HTML: US$/USD={usd_count} | €/EUR={eur_count} | ARS=$={ars_count}")

        # Buscar data-currency atributos
        cur_attrs = re.findall(r'data-currency[^"]*"([^"]+)"', html)
        if cur_attrs:
            print(f"data-currency attrs: {set(cur_attrs)}")

        # Buscar cualquier JSON con "currency" en el HTML (scripts inline)
        currency_in_scripts = re.findall(r'"currency"\s*:\s*"([A-Z]+)"', html)
        if currency_in_scripts:
            print(f"'currency' en scripts inline: {set(currency_in_scripts)}")

        pos_in_html = re.findall(r'"pos"\s*:\s*"([a-z\-]+)"', html)
        if pos_in_html:
            print(f"'pos' en HTML/scripts: {set(pos_in_html)}")

        print()
        print("=" * 70)
        print("GRAPHQL: requests con 'graphql' en URL")
        print("=" * 70)
        graphql_reqs = [r for r in captured_requests if "graphql" in r["url"].lower()]
        print(f"Total graphql requests: {len(graphql_reqs)}")
        for req in graphql_reqs:
            print(f"\n  {req['method']} {req['url'][:120]}")
            if req["body"]:
                try:
                    body_json = json.loads(req["body"])
                    # Buscar variables relevantes
                    body_str = json.dumps(body_json, indent=2)
                    for key in ["currency", "pos", "locale", "market", "priceType"]:
                        matches = re.findall(rf'"{key}"\s*:\s*"?([^",\n}}]+)"?', body_str, re.IGNORECASE)
                        if matches:
                            print(f"    >>> '{key}': {matches[:3]}")
                except json.JSONDecodeError:
                    # Body is not JSON (might be multipart or urlencoded)
                    print(f"    body (non-JSON): {req['body'][:200]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
