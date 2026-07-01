# Handoff — Scraper Faena — 2026-06-29

> Sesiones: 2026-06-28 (investigación + arquitectura) / 2026-06-29 (debugging anti-bot) / 2026-06-29 tarde (bypass TLS + precios) / 2026-06-29 noche (investigación moneda) / 2026-06-29 noche 2 (fix moneda USD ✅)
> Tema: Scraper / multi-sitio / Strategy + Template Method / anti-bot Accor / Firefox bypass

---

## Objetivo

Extender el scraper para soportar el **Hotel Faena Buenos Aires** (`all.accor.com`, SPA Nuxt.js). El objetivo de largo plazo es que agregar un hotel nuevo sea un proceso repetible documentado como **skill `agregar-hotel`**.

---

## Arquitectura implementada (sesión 2026-06-28) ✅

### Strategy + Template Method

| Archivo | Qué hace |
|---------|----------|
| `ScrawlingChinese/site_configs/alvear.py` | `AlvearConfig` — URL, params, CSS, wait_for del Alvear |
| `ScrawlingChinese/site_configs/faena.py` | `FaenaConfig` — anti-bot, selectores DOM, BROWSER_TYPE="firefox" |
| `ScrawlingChinese/parsers/base.py` | Protocol `RoomParser` |
| `ScrawlingChinese/parsers/llm_parser.py` | `LLMParser` — extracción vía Groq |
| `ScrawlingChinese/parsers/dom_parser.py` | `DOMParser` — BeautifulSoup sin LLM |
| `ScrawlingChinese/utils/hotel_scraper.py` | `HotelScraper` — Template Method con dos paths: `_crawl_firefox()` y `_crawl_chromium()` |
| `ScrawlingChinese/crawler.py` | `make_scraper(hotel, parser_type)`, `crawl_faena()`, `CRAWLERS` dict |

**División browser por parser:**
- Faena + DOMParser → `BROWSER_TYPE="firefox"` → `_crawl_firefox()` (Playwright directo, bypasea TLS)
- Alvear + LLMParser → Chromium default → `_crawl_chromium()` (Crawl4AI)
- Faena + LLMParser → `NotImplementedError` con mensaje claro (no soportado aún)

---

## Root cause del anti-bot — RESUELTO ✅ (sesión 2026-06-29 tarde)

### Diagnóstico completo recorrido

| Test | Resultado | Qué aprendimos |
|------|-----------|----------------|
| Headless Chromium, `magic=True` | Sin responses de `api.accor.com` | Stealth JS no alcanza |
| Headless Chromium, delay fijo 20s | HTML 84 KB sin rooms, cero responses | API cuelga la conexión |
| `<head>` del HTML | GTM + Kameleoon — sin DataDome/PerimeterX/Akamai | No es anti-bot comercial |
| Headed Chromium (browser visible) | Misma página de error "Technical error" | No es headless-detection |
| Firefox via Crawl4AI 0.4.x | `http://0,0/` — Firefox roto en esta versión | Crawl4AI 0.4.x pasa flags Chromium a Firefox |
| **Firefox via Playwright directo** | **`<< 200` en todas las APIs, 360 KB con rooms** | **TLS fingerprinting confirmado** |

### Root cause

`api.accor.com` hace **TLS fingerprinting (JA3/JA4)**: detecta la firma del handshake TLS de Playwright's Chromium y cuelga la conexión. Firefox tiene una firma TLS completamente distinta → pasa sin problema.

`tf-playwright-stealth` (ya incluida en Crawl4AI 0.4.x) parchea el fingerprinting de JavaScript pero **no el TLS** — por eso `magic=True` no ayudó.

### Por qué Crawl4AI 0.4.x no sirve para Firefox

`_build_browser_args()` en `async_crawler_strategy.py:388` hardcodea 15+ flags Chromium-específicos (incluyendo `--window-position=0,0`) que se pasan a TODOS los browsers. Firefox los interpreta como URLs → abre `http://0,0/`.

**Solución**: Playwright directo en `_crawl_firefox()`, sin pasar por Crawl4AI.

---

## Estado actual (2026-06-29 tarde)

### ✅ Funcionando
- **13 habitaciones extraídas en ~7s** con Firefox headless
- Todas las llamadas a `api.accor.com` devuelven `<< 200`
- Selector de nombres: `.hotel-accommodations-offers__item-title` ✅
- Path Firefox vs Chromium separado limpiamente en `HotelScraper`

### 🔧 Pendiente: precios en $0.00

Los precios se cargan en cadena DESPUÉS del selector de rooms:
```
selector rooms aparece
  ~1s después → POST affiliation-and-identification → 200
  inmediatamente → POST graphql (precios) → 200
    precios renderizados en DOM
```

El `wait_for_selector()` dispara cuando aparecen los rooms, pero los precios llegan 2-3 segundos después. Se implementó `page.wait_for_response("affiliation-and-identification") + asyncio.sleep(2)` — **este fix está en el código pero aún no se corrió el test de validación**.

Además, el selector `.offer-price__amount` existe en el HTML (confirmado en test diagnóstico: `price=True`), pero `soup.select()` devuelve 0 elementos — puede ser que el elemento exista en CSS/JS pero no como nodo DOM al momento de captura. El diagnostic de "Public rate" en `dom_parser.py` debería revelar el selector exacto una vez que los precios carguen.

El usuario quiere el **public rate** (no el member rate).

---

## Próximos pasos

1. **Correr el test** con el fix de `wait_for_response`:
   ```powershell
   python .claude/skills/scripts/test_scraper.py faena 15-07-2026 16-07-2026 2 --parser=dom
   ```
2. **Si `precios > 0`** → ver qué selector encontró el diagnostic y actualizar `DOM_PRECIO_SEL` en `faena.py` con el selector del public rate
3. **Si `precios = 0`** → el diagnostic de "Public rate" debería printar el elemento exacto para encontrar el selector correcto
4. **Limpiar código diagnóstico** en `dom_parser.py` (prints de `[DOM] candidato`) una vez que el selector de precio esté confirmado
5. **Skill `agregar-hotel`** — crear `.claude/skills/agregar-hotel.md` (ver plan en sección siguiente)

---

## Selectores CSS del Faena (encontrados en sesión 2026-06-28)

| Rol | Selector | Estado |
|-----|----------|--------|
| Contenedor rooms | `.hotel-accommodations` | ✅ |
| Nombre habitación | `.hotel-accommodations-offers__item-title` | ✅ |
| Precio (public rate) | `.offer-price__amount` | ⚠️ devuelve 0 elementos — pendiente confirmar/corregir |

**`wait_for`**: `css:.hotel-accommodations-offers__item-title`

**Parámetro `compositions`** (formato Accor): `"{adultos}-{edad1}-{edad2}"`. Ej: `"2-16-2"` = 2 adultos + niño 16 + niño 2.

---

## DOM selectors del Alvear

Pendiente. `AlvearConfig.DOM_NOMBRE_HAB_SEL = None`. `DOMParser` lanza `NotImplementedError` descriptivo si se intenta.

---

## Skill `agregar-hotel` (sesión futura — prioridad alta)

Crear `.claude/skills/agregar-hotel.md`. La idea: invocar la skill y que Claude sepa exactamente qué pedir, analice el HTML y agregue el hotel completo, testeando que el scraping manual pase antes de cerrar.

### Flujo de la skill

```
1. RECOLECTAR
   Claude pregunta:
   a) Nombre del hotel y clave interna (ej: "faena")
   b) URL de búsqueda con parámetros de ejemplo (1 noche, 2 adultos, fechas futuras)
   c) Cómo se construyen los parámetros (fechas, adultos, niños — ¿formato especial?)
   d) outerHTML completo — copiado desde DevTools DESPUÉS de que cargaron las habitaciones
   e) ¿Tiene anti-bot? (probar abrir en modo incógnito)

2. ANALIZAR HTML
   Claude encuentra:
   - Selector contenedor principal
   - Selector nombre de habitación
   - Selector precio
   - Selector para wait_for (el que aparece ÚLTIMO al cargar)
   Confirma con el usuario antes de continuar.

3. CREAR SiteConfig
   site_configs/{hotel}.py con todos los campos.
   Actualiza site_configs/__init__.py.

4. REGISTRAR EN CRAWLER
   crawl_{hotel}() en crawler.py + _SITE_CONFIGS + CRAWLERS.

5. TEST DOM (OBLIGATORIO)
   Corre test-scraper con --parser=dom y fechas futuras.
   Verifica: >= 1 habitación, nombre no vacío, precio > 0.
   Si falla → debug, ajustar selectores, repetir.

6. TEST LLM (opcional)
   Misma validación con --parser=llm.

7. ACTUALIZAR DOCS
   tree-directory.md + multi-sitio.md
```

---

## Archivos clave tocados esta sesión

| Archivo | Cambio |
|---------|--------|
| `Hoteles/ScrawlingChinese/site_configs/faena.py` | `BROWSER_TYPE="firefox"`, `HEADLESS=True`, `USER_AGENT` Firefox, selectores restaurados |
| `Hoteles/ScrawlingChinese/utils/hotel_scraper.py` | Split en `_crawl_firefox()` + `_crawl_chromium()`, `_FirefoxResult` mock, guard LLMParser |
| `Hoteles/ScrawlingChinese/utils/scraper_utils.py` | `get_browser_config()` acepta `user_agent`, `headless`, `browser_type`; workaround bug `chrome_channel` Firefox |
| `Hoteles/ScrawlingChinese/parsers/dom_parser.py` | Diagnostic temporal: prints `[DOM]` de nombres/precios y búsqueda de "Public rate" |

---

## Continuación — 2026-06-29 tarde (precios USD)

### Objetivo de la sesión
Corregir los precios que salían en `$0.00` y luego resolver que salían en EUR en lugar de USD.

### Lo que funcionó ✅

**Fix 1 — `wait_for_selector` en lugar de `wait_for_response`** (`hotel_scraper.py:128`)

`wait_for_response("affiliation-and-identification")` fallaba silenciosamente porque la respuesta ya había ocurrido durante el `wait_until="networkidle"` de `page.goto()`. Los listeners de `wait_for_response` solo capturan respuestas **futuras**. Reemplazado por:
```python
await page.wait_for_selector(DOM_PRECIO_SEL, timeout=15000)
```
Resultado: 13 habitaciones con `precios=26` (2 por habitación). ✅

**Fix 2 — Intercepción de currency vía Playwright route** (`hotel_scraper.py:116-132`)

Accor determina la moneda por IP-geolocation, ignorando `currency=USD` en la URL. Se implementó un route interceptor que:
- Reescribe `accorApi/header?pos=united-kingdom` → `pos=united-states` (para el header)
- Modifica el body del POST `api.accor.com/bff/v1/graphql` cuando contiene `"currency"` → `"USD"`

Resultado: precios en `US$` reales (ej: `US$550.88`). ✅

`locale="en-US"` en el contexto Playwright **no afecta el POS** — lo dejamos pero no es lo que resuelve la moneda.

### Lo que NO funcionó ❌

- `Accept-Language: en-US` (via `locale="en-US"` en Playwright context) — no cambia el `pos` de Accor, que es 100% IP-based
- `wait_for_response("affiliation-and-identification")` — llega tarde porque el networkidle de goto() ya consumió esa response

### Estado actual — pendiente para próxima sesión

**1. Member rate vs Public rate** — los 26 precios en el DOM son 2 por habitación, intercalados:
- Índices pares (`offer-price--default`, clase `price-display--member-rate`): member rate — ej. `US$550.88`
- Índices impares (`offer-price--alternative`, atributo `show-price-label=""`): public rate — ej. `US$611.75`

El selector actual `.offer-price__amount` toma los member rates (índice `i` directo). Para el public rate usar:
```python
DOM_PRECIO_SEL = ".offer-price--alternative .offer-price__amount"
```

**2. Discrepancia de precios** — scraper muestra ~$550 (member) / ~$611 (public) pero el usuario ve ~$503 en su browser. Causa desconocida — puede ser sesión logueada, tarifa diferente, o que el interceptor de graphql body no modifica todos los requests de pricing. Requiere comparar el HTML guardado en `.claude/tmp/page-faena-*.html` con lo que muestra el browser.

**3. Código diagnóstico a limpiar** una vez confirmado el selector de precio correcto:
- `dom_parser.py:36` — `print(f"  [DOM] nombres=... precios=...")` + bloque `_dump_precio_html`
- `hotel_scraper.py` — bloque de dump de HTML completo (lines ~145-155)

### Archivos tocados esta sesión

| Archivo | Cambio |
|---------|--------|
| `Hoteles/ScrawlingChinese/utils/hotel_scraper.py` | `wait_for_selector` para precios; `locale="en-US"`; route interceptor pos+currency; dump HTML crudo |
| `Hoteles/ScrawlingChinese/parsers/dom_parser.py` | Diagnostic dump de nodos de precio (`_dump_precio_html`) |
| `CLAUDE.md` | Aclaración sobre cómo invocar project skills (Read directo, no Skill tool) |

---

## Continuación — 2026-06-29 noche (investigación moneda USD)

### Contexto de la sesión
El scraper volvía a devolver precios en EUR. Se investigó la causa y se preparó el entorno para la próxima sesión.

### Lo que se descubrió

**Causa del EUR**: El route interceptor de la sesión anterior (`pos=united-states` + graphql currency) fue reemplazado por un `_passthrough` que no hace nada. Sin interceptor → Accor detecta IP argentina → asigna POS europeo → EUR.

**Diferencia de contextos (importante para el fix)**:

| Contexto | Moneda | Taxes |
|---|---|---|
| Usuario en browser (IP AR, selecciona USD manual) | USD | Sin incluir — declarados aparte |
| Scraper anterior (interceptor `pos=united-states`) | USD | Incluidos — estructura mercado US |
| Scraper actual (sin interceptor) | EUR | Incluidos |

El interceptor anterior daba USD pero con **estructura incorrecta** (taxes incluidos). El objetivo real es replicar lo que ve el usuario: USD sin taxes incluidos.

**`currency=USD` en la URL no funciona**: Aunque el parámetro aparece en la URL del usuario, Accor lo ignora a nivel de API — confirmado con Firefox donde las API calls sí llegan. Agregado igualmente a `build_params` (no rompe nada y puede afectar la UI).

### Lo que NO funcionó ❌
- `currency=USD` como parámetro URL en `build_params` → Accor lo ignora en sus API calls

### Herramienta instalada para próxima sesión ✅
**Playwright MCP** (`@playwright/mcp@latest`) instalado globalmente:
```
claude mcp add playwright npx @playwright/mcp@latest
```
Con esto Claude puede abrir el browser, navegar a la página del Faena, cambiar la moneda a USD y capturar exactamente qué mecanismo usa Accor (cookie, header, API call) — sin intervención manual del usuario.

#### Archivos tocados en sesión noche (investigación moneda)

| Archivo | Cambio |
|---------|--------|
| `Hoteles/ScrawlingChinese/site_configs/faena.py` | Agregado `"currency": "USD"` a `build_params` (no resuelve el problema pero no rompe nada) |

---

## Continuación — 2026-06-29 noche 2 (fix moneda USD) ✅ RESUELTO

### Contexto

El MCP de Playwright no estaba disponible (no persistió entre sesiones). Se usó Playwright directo desde Python con scripts de diagnóstico en `.claude/tmp/`.

### Diagnóstico: mecanismo real de moneda

**Lo que se descubrió** con `diag_accor_currency.py`:

- `aem-api.accor.com/accorApi/header?lang=en&pos=united-kingdom&brand=all` → el `pos=united-kingdom` está **hardcodeado en el JS del front-end**, no es IP-based.
- El request que determina los precios es `POST api.accor.com/bff/v1/graphql` con `operationName=HotelPageHot`, variables: `"countryMarket":"GB","currency":"EUR"`.
- No hay cookies de moneda ni POS. El mecanismo no es por cookie.
- El currency switcher del DOM desde IP argentina solo muestra monedas europeas (sin USD).

**Prueba de markets** con `diag_accor_markets.py` (interceptor Playwright que modifica el body graphql en vuelo):

| countryMarket | currency | Public rate (Park View, 20-21 Jul) |
|---|---|---|
| `GB` | `EUR` (baseline) | €507.46 |
| `GB` | `USD` (interceptor anterior) | US$577.93 |
| `AR` | `USD` | **$475.15** ← coincide con browser usuario |
| `US` | `USD` | $475.15 (idéntico a AR) |

`AR` y `US` comparten región tarifaria. `GB+USD` da precios más altos porque aplica el tipo de cambio EUR→USD del mercado UK.

### Fix implementado ✅

Route interceptor en `_crawl_firefox()` que modifica `HotelPageHot` antes de enviarlo:

```python
async def _intercept(route, request):
    if "graphql" in request.url and request.method == "POST":
        try:
            body_json = json.loads(request.post_data_buffer.decode("utf-8"))
            if body_json.get("operationName") == "HotelPageHot":
                vars_ = body_json.setdefault("variables", {})
                vars_["countryMarket"] = "AR"
                vars_["currency"] = "USD"
                await route.continue_(post_data=json.dumps(body_json))
                return
        except Exception:
            pass
    await route.continue_()
await page.route("**/*", _intercept)
```

**Bug que retrasó el fix:** `json` no estaba importado en `hotel_scraper.py`. El `NameError` era tragado por `except Exception: pass`, el request pasaba sin modificar, y los precios salían con el mismo número en EUR pero con símbolo `$` (conversión visual sin recalcular).

### Resultados finales (test scraper 20-21 Jul 2026, 2 adultos)

```
13 habitaciones extraídas en ~10s
  1. PARK VIEW ROOM          → $475.15 USD
  2. ACCESSIBLE PARK VIEW    → $475.15 USD
  3. SKYLINE VIEW ROOM       → $543.15 USD
  ...
```

Verificado contra browser del usuario: precios coinciden (diferencia residual atribuida a fechas distintas).

### Código diagnóstico limpiado

- `dom_parser.py`: eliminados `print [DOM]`, call a `_dump_precio_html()`, búsqueda de "Public rate", y la función `_dump_precio_html` completa.
- `hotel_scraper.py`: eliminado dump de HTML crudo a `.claude/tmp/`.

### Archivos tocados esta sesión

| Archivo | Cambio |
|---------|--------|
| `Hoteles/ScrawlingChinese/utils/hotel_scraper.py` | `import json`; `_intercept` reemplaza `_passthrough`; eliminado dump HTML crudo |
| `Hoteles/ScrawlingChinese/parsers/dom_parser.py` | Eliminado código diagnóstico completo (`_dump_precio_html`, prints `[DOM]`, búsqueda "Public rate") |
| `docs/problemas/scraper/currency-market.md` | Documentación completa del problema y solución |
| `docs/problemas/README.md` | Estado → ✅ Resuelto |

---

## Estado actual del scraper Faena

**✅ COMPLETAMENTE FUNCIONAL**

- 13 habitaciones en ~10s con Firefox headless
- Precios en USD del mercado AR (sin taxes bundleadas)
- Selector de public rate correcto (`.offer-price--alternative .offer-price__amount`)
- Sin código diagnóstico

## Próximos pasos

1. **Skill `agregar-hotel`** — crear `.claude/skills/agregar-hotel.md` (ver plan en sección de más abajo)
2. **DOM selectors del Alvear** — `AlvearConfig.DOM_NOMBRE_HAB_SEL = None`, pendiente investigar

---

## Archivos de referencia

| Archivo | Descripción |
|---------|-------------|
| `docs/handoffs/bodyFaena.md` | HTML del Faena con rooms (fuente de selectores) |
| `docs/features/multi-hotel-strategy-pattern.md` | Plan de arquitectura |
