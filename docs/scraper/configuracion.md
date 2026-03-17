# Configuración del Scraper

Guía completa de todos los parámetros configurables del sistema de scraping.

## Variables de Entorno

**Archivo**: `Hoteles/.env`

### API Keys (Requeridas)

```env
# Groq Cloud API Key
# Obtener en: https://console.groq.com/keys
GROQ_API_KEY=gsk_tu_api_key_aqui
```

**¿Cómo obtenerla?**
1. Ir a [console.groq.com](https://console.groq.com)
2. Crear cuenta (gratis)
3. Navegar a "API Keys"
4. Crear nueva key
5. Copiar y pegar en `.env`

### Configuración de Scraping

```env
# Delay entre scraping de periodos (segundos)
# Default: 2s
# Aumentar si hay rate limiting
SCRAPING_DELAY_SECONDS=2

# Timeout para navegación de página (milisegundos)
# Default: 60000 (60s)
PAGE_TIMEOUT_MS=60000

# Máximo de reintentos si falla extracción
# Default: 3
MAX_SCRAPING_RETRIES=3
```

---

## Configuración de URLs y Selectores

**Archivo**: `ScrawlingChinese/config.py`

```python
# URL base del hotel
BASE_URL = "https://www.alvearpalace.com/search"

# Selector CSS del contenedor de habitaciones
# Ajustar si el sitio cambia estructura
CSS_SELECTOR = "div.rooms-container"
```

### Cómo Actualizar CSS_SELECTOR

Si el sitio web cambia y el scraper deja de funcionar:

1. **Abrir sitio en navegador**:
   ```
   https://www.alvearpalace.com/search?checkin=2026-02-15&checkout=2026-02-16&adults=2&children=0
   ```

2. **Abrir DevTools** (F12 o Ctrl+Shift+I)

3. **Inspeccionar elemento** que contiene las habitaciones:
   - Click derecho en lista de habitaciones → "Inspeccionar"
   - Buscar el `<div>` o `<section>` que envuelve TODAS las habitaciones

4. **Copiar selector**:
   - Click derecho en el elemento en DevTools
   - "Copy" → "Copy selector"
   - Ejemplo: `div.rooms-container` o `#rooms-list`

5. **Actualizar en config.py**:
   ```python
   CSS_SELECTOR = "div.nuevo-selector"  # Pegar aquí
   ```

6. **Probar**:
   ```bash
   python .claude/skills/scripts/test_scraper.py
   ```

---

## Configuración del Browser

**Archivo**: `ScrawlingChinese/utils/scraper_utils.py:20-40`

### BrowserConfig

```python
browser_config = BrowserConfig(
    headless=True,                     # Sin ventana visual
    verbose=False,                     # Sin logs detallados
    extra_args=["--disable-gpu"],      # Args adicionales de Chromium
)
```

**Opciones disponibles:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `headless` | bool | True | Si False, abre ventana de navegador visible |
| `verbose` | bool | False | Si True, muestra logs detallados de Crawl4AI |
| `extra_args` | list[str] | [] | Argumentos adicionales para Chromium |

**Extra args útiles:**

```python
extra_args=[
    "--disable-gpu",              # Deshabilita GPU (útil en servers)
    "--no-sandbox",               # Sin sandbox (solo en Docker)
    "--disable-dev-shm-usage",    # Evita problemas de memoria compartida
    "--window-size=1920,1080",    # Resolución de ventana
    "--user-agent=Mozilla/5.0...", # User agent custom
]
```

### CrawlerRunConfig

```python
crawl_config = CrawlerRunConfig(
    wait_until="networkidle",          # Condición de espera
    css_selector=CSS_SELECTOR,         # Selector del contenido
    screenshot=False,                  # Sin screenshots
    page_timeout=60000,                # Timeout en ms
)
```

**Opciones disponibles:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `wait_until` | str | "networkidle" | Cuándo considerar página cargada |
| `css_selector` | str | None | Selector CSS del contenido a extraer |
| `screenshot` | bool | False | Si True, captura screenshot |
| `page_timeout` | int | 60000 | Timeout en milisegundos |

**Valores de wait_until:**

- `"load"` - Espera evento `load` del DOM (rápido, puede no cargar JS)
- `"domcontentloaded"` - Espera DOM completo (sin imágenes/CSS)
- `"networkidle"` - **Recomendado** - Espera que red esté idle (todo cargado)
- `"commit"` - Espera primer frame (muy rápido, incompleto)

**Para sitios con mucho JavaScript dinámico**: Usar `"networkidle"`.

---

## Configuración de Extracción LLM

**Archivo**: `ScrawlingChinese/utils/scraper_utils.py:45-70`

### LLMExtractionStrategy

```python
extraction_strategy = LLMExtractionStrategy(
    provider="groq/deepseek-r1-distill-llama-70b",  # Modelo LLM
    api_token=GROQ_API_KEY,                         # API key
    schema=HotelWeb.model_json_schema(),            # Schema Pydantic
    extraction_type="schema",                       # Tipo de extracción
    instruction="...",                              # Prompt para el LLM
    chunk_token_threshold=4000,                     # Tokens por chunk
    overlap_rate=0.1,                               # Overlap entre chunks
)
```

**Opciones disponibles:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `provider` | str | - | Formato: `groq/modelo` o `openai/modelo` |
| `api_token` | str | - | API key del provider |
| `schema` | dict | - | JSON Schema (desde Pydantic) |
| `extraction_type` | str | "schema" | `"schema"` o `"simple"` |
| `instruction` | str | - | Prompt que guía al LLM |
| `chunk_token_threshold` | int | 4000 | Máximo tokens por chunk |
| `overlap_rate` | float | 0.1 | % de overlap entre chunks (0.0-1.0) |

### Modelos Disponibles (Groq)

**Gratuitos en preview:**

```python
# DeepSeek-R1 (recomendado para extracción)
provider="groq/deepseek-r1-distill-llama-70b"

# Llama 3.1 70B (alternativa)
provider="groq/llama-3.1-70b-versatile"

# Mixtral 8x7B (más rápido, menos preciso)
provider="groq/mixtral-8x7b-32768"
```

**Rendimiento comparativo:**

| Modelo | Velocidad | Precisión | Costo |
|--------|-----------|-----------|-------|
| DeepSeek-R1 70B | Rápido | ✅ Alta | Gratis |
| Llama 3.1 70B | Medio | ✅ Alta | Gratis |
| Mixtral 8x7B | ⚡ Muy rápido | ⚠️ Media | Gratis |

### Ajustar Instrucción del LLM

**Instrucción actual:**

```python
instruction=(
    "Extrae información de habitaciones de hotel. "
    "Para cada habitación, identifica el nombre y todos los combos de precio disponibles. "
    "Cada combo tiene título, descripción opcional y precio. "
    "Retorna JSON que coincida exactamente con el schema provisto."
)
```

**Personalizar para mejorar precisión:**

```python
instruction=(
    "Extrae TODAS las habitaciones del hotel. "
    "Nombre de habitación: Texto visible que describe el tipo (ej: 'Double Superior'). "
    "Combos de precio: TODAS las opciones de precio disponibles para esa habitación. "
    "Título del combo: Plan de tarifa (ej: 'Standard Rate', 'Best Available Rate'). "
    "Descripción: Qué incluye (ej: 'Room only', 'Breakfast included'). "
    "Precio: Número en USD, SIN símbolo $. "
    "IMPORTANTE: No inventes datos, solo extrae lo visible. "
    "Retorna JSON válido según el schema."
)
```

**Consejos:**
- ✅ Ser específico sobre qué extraer
- ✅ Dar ejemplos de formato esperado
- ✅ Mencionar "según el schema" para reforzar validación
- ❌ No hacer instrucción muy larga (max ~200 palabras)

### Ajustar Chunk Settings

**Para HTML muy grandes (>10,000 tokens):**

```python
chunk_token_threshold=6000,   # Aumentar threshold
overlap_rate=0.15,             # Aumentar overlap para no perder datos
```

**Para HTML pequeños (<2,000 tokens):**

```python
chunk_token_threshold=8000,   # Threshold alto = 1 solo chunk
overlap_rate=0.0,              # Sin overlap necesario
```

---

## Configuración de Parámetros de Búsqueda

**Archivo**: `ScrawlingChinese/crawler.py:15-30`

### Parámetros Default

```python
async def crawl_alvear(
    fecha_entrada: str,     # Formato: YYYY-MM-DD
    fecha_salida: str,      # Formato: YYYY-MM-DD
    adultos: int = 2,       # Default: 2 adultos
    ninos: int = 0          # Default: 0 niños
):
```

### Construir URL de Búsqueda

```python
from ScrawlingChinese.config import BASE_URL

url = f"{BASE_URL}?checkin={fecha_entrada}&checkout={fecha_salida}&adults={adultos}&children={ninos}"

# Ejemplo:
# https://www.alvearpalace.com/search?checkin=2026-02-15&checkout=2026-02-16&adults=2&children=0
```

**Si el sitio usa parámetros diferentes:**

```python
# Algunos sitios usan nombres diferentes
url = f"{BASE_URL}?arrival={fecha_entrada}&departure={fecha_salida}&guests={adultos}"

# O formato de fecha diferente
from datetime import datetime
fecha_entrada_obj = datetime.strptime(fecha_entrada, "%Y-%m-%d")
fecha_entrada_formatted = fecha_entrada_obj.strftime("%m/%d/%Y")  # 02/15/2026

url = f"{BASE_URL}?checkin={fecha_entrada_formatted}&checkout=..."
```

---

## Configuración de Caché

**Archivo**: `Core/gestor_datos.py:50-80`

### Habilitar/Deshabilitar Caché

```python
def dar_hotel_web(self, ..., force_fresh=False):
    """
    force_fresh=False → Usa caché si existe
    force_fresh=True  → Siempre scrapea fresco
    """
```

**Uso desde código:**

```python
# Usar caché (primera vez scrapea, luego carga de .pkl)
hotel_web = gestor.dar_hotel_web(..., force_fresh=False)

# Forzar scraping fresco (multi-periodo)
hotel_web = gestor.dar_hotel_web(..., force_fresh=True)
```

### Limpiar Caché Manualmente

```bash
# Eliminar archivo de caché
rm hotel_guardado.pkl

# O desde Python
import os
if os.path.exists('hotel_guardado.pkl'):
    os.remove('hotel_guardado.pkl')
```

### Ubicación del Caché

**Actual**: Raíz del proyecto (`hotel_guardado.pkl`)

**Cambiar ubicación** en `gestor_datos.py`:

```python
CACHE_DIR = Path("cache/")
CACHE_FILE = CACHE_DIR / "hotel_guardado.pkl"

def _guardar_cache(self, hotel_web):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(hotel_web, f)
```

---

## Configuración de Reintentos

**Archivo**: `ScrawlingChinese/utils/scraper_utils.py:90-130`

```python
MAX_RETRIES = 3  # Cambiar según necesidad
RETRY_DELAY_SECONDS = 2  # Delay entre reintentos
```

**Estrategia de reintentos:**

```python
for intento in range(1, MAX_RETRIES + 1):
    try:
        result = await crawler.arun(...)
        # ... validación ...
        return hotel_web
    except Exception as e:
        print(f"⚠️  Intento {intento} falló: {e}")
        if intento < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY_SECONDS)

raise Exception(f"Falló después de {MAX_RETRIES} intentos")
```

**Ajustar para sitios inestables:**

```python
MAX_RETRIES = 5              # Más intentos
RETRY_DELAY_SECONDS = 5      # Más delay entre intentos
```

---

## Configuración Multi-Periodo

**Archivo**: `.env`

```env
# Delay entre scraping de periodos
# Importante para evitar rate limiting
SCRAPING_DELAY_SECONDS=2
```

**Uso en código** (`Core/comparador_multiperiodo.py:130`):

```python
import os

DELAY = int(os.getenv('SCRAPING_DELAY_SECONDS', 2))

for periodo in periodos_aplicables:
    # ... scraping ...
    await asyncio.sleep(DELAY)
```

**Recomendaciones:**

| Escenario | Delay Recomendado |
|-----------|-------------------|
| Testing local | 1-2s |
| Multi-periodo (3-5 periodos) | 2-3s |
| Multi-periodo (>5 periodos) | 3-5s |
| Sitio con rate limiting estricto | 5-10s |

---

## Resumen de Archivos de Configuración

```
Hoteles/
├── .env                                    ← API keys + variables globales
├── ScrawlingChinese/
│   ├── config.py                          ← BASE_URL + CSS_SELECTOR
│   ├── crawler.py                         ← Funciones crawl_*()
│   └── utils/
│       └── scraper_utils.py               ← Browser + LLM config
└── Core/
    └── gestor_datos.py                     ← Caché config
```

**Modificaciones comunes:**

| Qué modificar | Dónde | Cuándo |
|---------------|-------|--------|
| API key | `.env` | Primera vez / renovación |
| URL del hotel | `config.py` | Cambio de sitio web |
| CSS selector | `config.py` | Sitio cambió estructura |
| Delay multi-periodo | `.env` | Rate limiting / performance |
| Modelo LLM | `scraper_utils.py` | Mejorar precisión / velocidad |
| Instrucción LLM | `scraper_utils.py` | Mejorar extracción |
| Timeout navegación | `scraper_utils.py` | Sitio muy lento |
| Máximo reintentos | `scraper_utils.py` | Sitio inestable |

---

Ver también:
- [como-funciona.md](como-funciona.md) - Arquitectura completa del scraper
- [troubleshooting.md](troubleshooting.md) - Solución de problemas
- [multi-sitio.md](multi-sitio.md) - Agregar más hoteles