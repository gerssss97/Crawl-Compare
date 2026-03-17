# Multi-Sitio: Agregar Más Hoteles

Guía paso a paso para extender el scraper a múltiples hoteles.

## Overview

Actualmente el proyecto scrapea **solo Alvear Palace**. Esta guía muestra cómo agregar:
- Marriott
- Hilton
- Cualquier otro hotel con sistema de reservas online

**Estrategia**: Crear funciones `crawl_*()` separadas por hotel, cada una con su propia configuración.

---

## Arquitectura Multi-Sitio

### Estructura Propuesta

```
ScrawlingChinese/
├── config.py                    ← Configuración centralizada
├── crawler.py                   ← Funciones crawl_*()
├── utils/
│   ├── scraper_utils.py        ← Helpers compartidos
│   └── site_configs/           ← Configs específicas por sitio (nuevo)
│       ├── alvear.py
│       ├── marriott.py
│       └── hilton.py
└── models/                     ← Schemas Pydantic por sitio (opcional)
    ├── alvear_schema.py
    └── marriott_schema.py
```

### Diccionario de Crawlers

**Archivo**: `ScrawlingChinese/crawler.py:10-15`

```python
# Mapeo de hotel → función crawler
CRAWLERS = {
    "alvear": crawl_alvear,
    "marriott": crawl_marriott,    # Nuevo
    "hilton": crawl_hilton,        # Nuevo
}

def get_crawler(hotel_nombre: str):
    """
    Retorna función crawler para el hotel especificado.

    Args:
        hotel_nombre: str - Nombre del hotel (ej: "alvear", "marriott")

    Returns:
        Async function que scrapea el hotel

    Raises:
        KeyError si hotel no existe
    """
    if hotel_nombre not in CRAWLERS:
        raise KeyError(f"Hotel '{hotel_nombre}' no tiene crawler configurado")

    return CRAWLERS[hotel_nombre]
```

---

## Ejemplo: Agregar Marriott

### Paso 1: Crear Configuración Específica

**Archivo**: `ScrawlingChinese/utils/site_configs/marriott.py`

```python
"""
Configuración específica para Marriott.
"""

# URL base
BASE_URL = "https://www.marriott.com/reservation/availabilitySearch.mi"

# Selector CSS del contenedor de habitaciones
CSS_SELECTOR = "div.room-rate-list"

# Parámetros de URL
# Marriott usa formato diferente a Alvear
def construir_url_busqueda(fecha_entrada, fecha_salida, adultos, ninos):
    """
    Construye URL de búsqueda para Marriott.

    Args:
        fecha_entrada: str YYYY-MM-DD
        fecha_salida: str YYYY-MM-DD
        adultos: int
        ninos: int

    Returns:
        str - URL completa
    """
    from datetime import datetime

    # Marriott usa formato MM/DD/YYYY
    entrada_obj = datetime.strptime(fecha_entrada, "%Y-%m-%d")
    salida_obj = datetime.strptime(fecha_salida, "%Y-%m-%d")

    entrada_formatted = entrada_obj.strftime("%m/%d/%Y")
    salida_formatted = salida_obj.strftime("%m/%d/%Y")

    # Marriott combina adultos + niños en "numberOfGuests"
    total_guests = adultos + ninos

    return (
        f"{BASE_URL}?"
        f"fromDate={entrada_formatted}&"
        f"toDate={salida_formatted}&"
        f"numberOfGuests={total_guests}&"
        f"numberOfRooms=1"
    )


# Timeout específico (Marriott puede ser lento)
PAGE_TIMEOUT_MS = 90000  # 90 segundos

# Wait condition
WAIT_UNTIL = "networkidle"  # Marriott usa mucho JS
```

### Paso 2: Crear Schema Pydantic (Si Difiere)

Si Marriott tiene estructura diferente de datos, crear schema custom:

**Archivo**: `ScrawlingChinese/models/marriott_schema.py`

```python
from pydantic import BaseModel
from typing import List, Optional

class ComboPrecioMarriott(BaseModel):
    """
    Marriott puede tener campos adicionales.
    """
    rate_code: str                    # Ej: "BAR", "AAA"
    rate_name: str                    # Ej: "Best Available Rate"
    price_per_night: float            # Precio por noche
    total_price: float                # Precio total estadía
    taxes_included: bool = False      # Si incluye impuestos
    points_option: Optional[int]      # Puntos Marriott (si aplica)

class HabitacionMarriott(BaseModel):
    room_type: str                    # Ej: "Deluxe King"
    room_description: str             # Descripción larga
    max_occupancy: int                # Máximo de huéspedes
    rates: List[ComboPrecioMarriott]  # Opciones de tarifa

class HotelMarriott(BaseModel):
    property_name: str
    rooms: List[HabitacionMarriott]
```

**Si la estructura es similar**, reutilizar `HotelWeb`:

```python
from Models.hotelWeb import HotelWeb, HabitacionWeb, ComboPrecio

# Usar schema estándar
schema = HotelWeb.model_json_schema()
```

### Paso 3: Crear Función Crawler

**Archivo**: `ScrawlingChinese/crawler.py:100-180`

```python
async def crawl_marriott(
    fecha_entrada: str,
    fecha_salida: str,
    adultos: int = 2,
    ninos: int = 0
) -> HotelWeb:
    """
    Scrapea Marriott Hotel.

    Args:
        fecha_entrada: str YYYY-MM-DD
        fecha_salida: str YYYY-MM-DD
        adultos: int (default 2)
        ninos: int (default 0)

    Returns:
        HotelWeb con habitaciones
    """
    from ScrawlingChinese.utils.site_configs import marriott
    from ScrawlingChinese.utils.scraper_utils import scrape_with_llm

    # Construir URL
    url = marriott.construir_url_busqueda(
        fecha_entrada, fecha_salida, adultos, ninos
    )

    print(f"\n🔍 Scrapeando Marriott")
    print(f"  URL: {url}")

    # Configuración específica de Marriott
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )

    crawl_config = CrawlerRunConfig(
        wait_until=marriott.WAIT_UNTIL,
        css_selector=marriott.CSS_SELECTOR,
        page_timeout=marriott.PAGE_TIMEOUT_MS,
        screenshot=False,
    )

    # Schema (usar HotelWeb estándar o custom)
    from Models.hotelWeb import HotelWeb
    schema = HotelWeb.model_json_schema()

    # Instrucción custom para Marriott
    instruction = (
        "Extrae TODAS las habitaciones disponibles en este hotel Marriott. "
        "Para cada habitación, extrae el tipo, descripción y TODAS las opciones de tarifa. "
        "Cada tarifa tiene código, nombre, precio por noche y precio total. "
        "Retorna JSON según el schema provisto."
    )

    # Estrategia LLM
    extraction_strategy = LLMExtractionStrategy(
        provider="groq/deepseek-r1-distill-llama-70b",
        api_token=os.getenv('GROQ_API_KEY'),
        schema=schema,
        extraction_type="schema",
        instruction=instruction,
        chunk_token_threshold=5000,  # Marriott puede tener HTML grande
        overlap_rate=0.1,
    )

    # Scraping con reintentos
    MAX_RETRIES = 3

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for intento in range(1, MAX_RETRIES + 1):
            try:
                result = await crawler.arun(
                    url=url,
                    config=crawl_config,
                    extraction_strategy=extraction_strategy
                )

                if result.extracted_content:
                    import json
                    data = json.loads(result.extracted_content)
                    hotel_web = HotelWeb(**data)

                    print(f"  ✅ Extracción exitosa: {len(hotel_web.habitaciones)} habitaciones")
                    return hotel_web
                else:
                    print(f"  ⚠️  Intento {intento}: Sin contenido extraído")

            except Exception as e:
                print(f"  ❌ Intento {intento} falló: {e}")

            if intento < MAX_RETRIES:
                await asyncio.sleep(2)

        raise Exception(f"Marriott scraping falló después de {MAX_RETRIES} intentos")
```

### Paso 4: Registrar en CRAWLERS

**Archivo**: `ScrawlingChinese/crawler.py:10-15`

```python
CRAWLERS = {
    "alvear": crawl_alvear,
    "marriott": crawl_marriott,  # ← Agregar aquí
}
```

### Paso 5: Actualizar Skill /test-scraper

**Archivo**: `.claude/skills/scripts/test_scraper.py:15-20`

```python
# Diccionario de crawlers disponibles
CRAWLERS = {
    "alvear": crawl_alvear,
    "marriott": crawl_marriott,  # ← Agregar aquí
}
```

**Uso:**

```bash
# Testear Marriott
python .claude/skills/scripts/test_scraper.py marriott 15-02-2026 16-02-2026 2 0
```

### Paso 6: Actualizar Excel con Datos de Marriott

**Archivo**: `Data/Extracto_prueba2.xlsx`

Agregar nueva sheet o sección:

```
| Hotel: Marriott Buenos Aires |
|------------------------------|
| Room Type        | Price     |
| Deluxe King      | $320.00   |
| Executive Suite  | $520.00   |
| ...              | ...       |
```

El extractor de Excel (`ExtractorDatos/`) automáticamente detectará el nuevo hotel.

---

## Adaptadores de Schema

Si un sitio tiene estructura MUY diferente, crear adaptador:

**Archivo**: `ScrawlingChinese/adapters/marriott_adapter.py`

```python
from Models.hotelWeb import HotelWeb, HabitacionWeb, ComboPrecio
from ScrawlingChinese.models.marriott_schema import HotelMarriott

def adaptar_marriott_a_hotelweb(hotel_marriott: HotelMarriott) -> HotelWeb:
    """
    Convierte schema de Marriott a schema estándar HotelWeb.

    Args:
        hotel_marriott: HotelMarriott - Datos de Marriott

    Returns:
        HotelWeb - Datos normalizados
    """
    habitaciones_web = []

    for room in hotel_marriott.rooms:
        # Convertir rates de Marriott a combos de precio estándar
        combos = []
        for rate in room.rates:
            combo = ComboPrecio(
                titulo=f"{rate.rate_name} ({rate.rate_code})",
                descripcion=f"${rate.price_per_night}/noche, Total: ${rate.total_price}",
                precio=rate.total_price  # Usar precio total
            )
            combos.append(combo)

        # Crear habitación web estándar
        hab_web = HabitacionWeb(
            nombre=f"{room.room_type} (max {room.max_occupancy} pax)",
            combos_precios=combos
        )
        habitaciones_web.append(hab_web)

    return HotelWeb(habitaciones=habitaciones_web)
```

**Uso en crawler:**

```python
# En crawl_marriott()
from ScrawlingChinese.models.marriott_schema import HotelMarriott
from ScrawlingChinese.adapters.marriott_adapter import adaptar_marriott_a_hotelweb

# Extraer con schema de Marriott
data = json.loads(result.extracted_content)
hotel_marriott = HotelMarriott(**data)

# Adaptar a schema estándar
hotel_web = adaptar_marriott_a_hotelweb(hotel_marriott)

return hotel_web
```

---

## Selector Dinámico desde UI

Permitir al usuario elegir hotel en la interfaz:

**Archivo**: `UI/views/formulario_seleccion_hotel.py`

Agregar dropdown de sitio web:

```python
class FormularioSeleccionHotel(BaseComponent):
    def _setup_ui(self):
        # Selector de sitio (Alvear vs Marriott)
        self.sitio_combo = LabeledComboBox(
            self.frame,
            label="Sitio Web:",
            values=["Alvear Palace", "Marriott", "Hilton"]
        )
        self.sitio_combo.pack(...)

        # Vincular a AppState
        self.sitio_combo.get_combobox().bind(
            '<<ComboboxSelected>>',
            lambda e: self.estado_app.sitio_web.set(self.sitio_combo.get_value())
        )
```

**Actualizar AppState**:

```python
class AppState:
    def __init__(self, event_bus):
        # ...
        self.sitio_web = tk.StringVar(value="Alvear Palace")
```

**Actualizar ControladorComparacion**:

```python
def _ejecutar_comparacion_thread(self):
    # Obtener sitio seleccionado
    sitio = self.estado_app.sitio_web.get()

    # Mapear a nombre de crawler
    sitio_map = {
        "Alvear Palace": "alvear",
        "Marriott": "marriott",
        "Hilton": "hilton",
    }

    crawler_name = sitio_map.get(sitio, "alvear")

    # Usar crawler correcto
    from ScrawlingChinese.crawler import get_crawler
    crawler_func = get_crawler(crawler_name)

    hotel_web = await crawler_func(
        fecha_entrada=...,
        fecha_salida=...,
        adultos=...,
        ninos=...
    )
```

---

## Testing Multi-Sitio

### Test Manual por Sitio

```bash
# Alvear
python .claude/skills/scripts/test_scraper.py alvear

# Marriott
python .claude/skills/scripts/test_scraper.py marriott

# Hilton
python .claude/skills/scripts/test_scraper.py hilton
```

### Test Comparativo

**Crear script**: `Tests/test_multi_sitio.py`

```python
import asyncio
from ScrawlingChinese.crawler import get_crawler

async def comparar_sitios():
    """
    Scrapea todos los sitios con mismos parámetros y compara resultados.
    """
    params = {
        'fecha_entrada': '2026-02-15',
        'fecha_salida': '2026-02-16',
        'adultos': 2,
        'ninos': 0
    }

    sitios = ['alvear', 'marriott', 'hilton']

    for sitio in sitios:
        print(f"\n{'='*60}")
        print(f"🏨 Scrapeando {sitio.upper()}")
        print(f"{'='*60}")

        try:
            crawler = get_crawler(sitio)
            hotel_web = await crawler(**params)

            print(f"✅ Habitaciones encontradas: {len(hotel_web.habitaciones)}")

            # Primera habitación como muestra
            if hotel_web.habitaciones:
                hab = hotel_web.habitaciones[0]
                print(f"  Ejemplo: {hab.nombre}")
                print(f"  Combos: {len(hab.combos_precios)}")
                if hab.combos_precios:
                    print(f"  Precio: ${hab.combos_precios[0].precio}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(comparar_sitios())
```

**Ejecutar:**

```bash
python Tests/test_multi_sitio.py
```

---

## Checklist para Agregar Nuevo Sitio

- [ ] 1. Inspeccionar sitio web en navegador
  - [ ] Identificar URL de búsqueda con parámetros
  - [ ] Identificar CSS selector del contenedor de habitaciones
  - [ ] Verificar estructura de datos (JSON en network tab si usa API)

- [ ] 2. Crear archivo de configuración
  - [ ] `ScrawlingChinese/utils/site_configs/<sitio>.py`
  - [ ] Definir `BASE_URL`, `CSS_SELECTOR`, `PAGE_TIMEOUT_MS`
  - [ ] Implementar `construir_url_busqueda()`

- [ ] 3. Definir schema Pydantic (si difiere)
  - [ ] `ScrawlingChinese/models/<sitio>_schema.py`
  - [ ] Modelos para habitación, combo precio, hotel
  - [ ] O reutilizar `HotelWeb` estándar

- [ ] 4. Crear función crawler
  - [ ] `async def crawl_<sitio>()` en `crawler.py`
  - [ ] Configurar browser, crawl config, extraction strategy
  - [ ] Implementar reintentos y manejo de errores

- [ ] 5. Registrar crawler
  - [ ] Agregar a `CRAWLERS` dict en `crawler.py`
  - [ ] Agregar a skill `/test-scraper`

- [ ] 6. Testear
  - [ ] `python .claude/skills/scripts/test_scraper.py <sitio>`
  - [ ] Verificar que extrae al menos 3 habitaciones
  - [ ] Verificar precios son válidos (>0)

- [ ] 7. Actualizar Excel
  - [ ] Agregar datos del nuevo hotel en `Data/Extracto_prueba2.xlsx`
  - [ ] Verificar extractor de Excel detecta nuevo hotel

- [ ] 8. Actualizar UI (opcional)
  - [ ] Agregar dropdown de selección de sitio
  - [ ] Actualizar lógica de comparación para usar sitio correcto

---

## Mejores Prácticas Multi-Sitio

### 1. Mantener Consistencia

Todos los crawlers deben retornar el mismo schema (`HotelWeb`) para facilitar comparación.

### 2. Configuración Centralizada

No hardcodear URLs/selectores en funciones. Usar archivos de config separados.

### 3. Manejo de Errores Específico por Sitio

Algunos sitios pueden requerir lógica especial:

```python
async def crawl_sitio_problematico(...):
    # Sitio requiere cookies específicas
    cookies = {
        'session_id': 'abc123',
        'preferred_currency': 'USD'
    }

    # Crawl4AI permite pasar cookies
    result = await crawler.arun(
        url=url,
        config=crawl_config,
        cookies=cookies  # ← Custom cookies
    )
```

### 4. Testing Continuo

Sitios web cambian. Implementar tests automatizados:

```python
# Tests/test_scrapers.py
@pytest.mark.asyncio
async def test_alvear_scraper():
    hotel = await crawl_alvear('2026-02-15', '2026-02-16')
    assert len(hotel.habitaciones) > 0
    assert hotel.habitaciones[0].combos_precios[0].precio > 0
```

---

Ver también:
- [como-funciona.md](como-funciona.md) - Arquitectura del scraper
- [configuracion.md](configuracion.md) - Configuración detallada
- [troubleshooting.md](troubleshooting.md) - Solución de problemas
