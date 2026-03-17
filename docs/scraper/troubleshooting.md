# Troubleshooting del Scraper

Guía completa para diagnosticar y resolver problemas con el scraper web (Crawl4AI + DeepSeek-R1).

## Tabla de Contenidos

- [Errores Comunes](#errores-comunes)
- [Debugging Paso a Paso](#debugging-paso-a-paso)
- [Verificación de Configuración](#verificación-de-configuración)
- [Problemas de Caché](#problemas-de-caché)
- [Rate Limiting y IP Ban](#rate-limiting-y-ip-ban)
- [Logs y Diagnóstico Avanzado](#logs-y-diagnóstico-avanzado)

---

## Errores Comunes

### Tabla de Errores

| Error | Causa | Solución |
|-------|-------|----------|
| **No extrae datos** (habitaciones vacías) | CSS_SELECTOR incorrecto o cambió la estructura HTML | Inspeccionar elemento en browser, actualizar selector en `ScrawlingChinese/config.py` |
| **Timeout** | Página lenta, servidor sobrecargado, red lenta | Aumentar `wait_until` o `timeout` en `utils/scraper_utils.py` |
| **JSON inválido** del LLM | Schema Pydantic no coincide con datos extraídos | Revisar estructura de `HabitacionWeb` en `Models/hotelWeb.py`, ajustar prompt LLM |
| **Caché contamina datos** | `hotel_guardado.pkl` tiene datos viejos | Usar `force_fresh=True` o eliminar `hotel_guardado.pkl` |
| **Rate limiting (429)** | Demasiados requests rápidos | Aumentar `SCRAPING_DELAY_SECONDS` en `.env`, esperar unos minutos |
| **API key inválida** | GROQ_API_KEY incorrecta o sin permisos | Verificar key en `.env`, regenerar en console.groq.com si es necesario |
| **Error de conexión** | Red caída, proxy/firewall bloqueando | Verificar conectividad, probar con otra red |
| **Habitación no matchea** en multi-periodo | Cambió nombre o desapareció del sitio | Verificar nombre en sitio web, ajustar fuzzy matching |
| **Precio None o $0** | LLM no extrajo precio correctamente | Revisar HTML crudo, ajustar prompt de extracción |

---

## Debugging Paso a Paso

### Paso 1: Verificar Conectividad Básica

```bash
# Verificar que el sitio está accesible
curl -I https://bookings.alvearpalace.com

# Debe retornar: HTTP/2 200 (o similar)
```

Si falla: problema de red o el sitio está caído.

---

### Paso 2: Verificar API Key de Groq

```bash
# Verificar que .env existe
ls Hoteles/.env

# Verificar contenido (Linux/Mac)
cat Hoteles/.env | grep GROQ_API_KEY

# Verificar contenido (Windows)
type Hoteles\.env | findstr GROQ_API_KEY

# Debe mostrar: GROQ_API_KEY=gsk_...
```

Si falla:
1. Crear `.env` en `Hoteles/`
2. Agregar `GROQ_API_KEY=tu_key_aqui`
3. Obtener key en https://console.groq.com/keys

---

### Paso 3: Ejecutar Scraper con Debugging

```python
# En Python shell
import asyncio
from ScrawlingChinese.crawler import crawl_alvear
from datetime import date, timedelta

# Fechas de prueba
entrada = date.today() + timedelta(days=7)
salida = entrada + timedelta(days=1)

# Ejecutar
resultado = asyncio.run(crawl_alvear(
    fecha_entrada=entrada.strftime("%Y-%m-%d"),
    fecha_salida=salida.strftime("%Y-%m-%d"),
    adultos=2,
    ninos=0
))

# Verificar resultado
print(f"Habitaciones extraídas: {len(resultado.habitacion)}")
for hab in resultado.habitacion[:3]:  # Primeras 3
    print(f"- {hab.nombre}: ${hab.combos[0].precio if hab.combos else 'Sin precio'}")
```

Si retorna `[]` (vacío):
- Verificar logs en consola
- Pasar al Paso 4

---

### Paso 4: Inspeccionar HTML Crudo

Modificar temporalmente `ScrawlingChinese/utils/scraper_utils.py`:

```python
# Agregar después de la línea donde se obtiene el HTML
print("=== HTML CRUDO ===")
print(result.html[:2000])  # Primeros 2000 caracteres
print("=== FIN HTML ===")
```

Ejecutar scraper nuevamente y verificar:
- ¿El HTML contiene información de habitaciones?
- ¿El CSS_SELECTOR está capturando la sección correcta?

Si NO contiene habitaciones:
- El sitio cambió su estructura
- Necesitas actualizar CSS_SELECTOR

---

### Paso 5: Verificar CSS Selector

Abrir sitio en browser con DevTools:

1. Ir a https://bookings.alvearpalace.com
2. F12 → Inspector
3. Buscar elemento que contiene las habitaciones
4. Click derecho → Copy → Copy Selector

Actualizar en `ScrawlingChinese/config.py`:

```python
CSS_SELECTOR = "#nuevo-selector-aqui"  # Actualizar
```

---

### Paso 6: Verificar Extracción LLM

Si el scraper obtiene HTML pero no extrae JSON correcto, revisar:

```python
# Ver respuesta del LLM en ScrawlingChinese/utils/scraper_utils.py
# Agregar print después de la extracción

print("=== RESPUESTA LLM ===")
print(result.extracted_content)
print("=== FIN LLM ===")
```

Problemas comunes:
- LLM retorna `null` o `{}` → HTML no tiene información suficiente
- LLM retorna JSON con estructura diferente → Ajustar schema Pydantic
- LLM retorna error → Verificar API key, límites de uso

---

## Verificación de Configuración

### Archivo: ScrawlingChinese/config.py

```python
BASE_URL = "https://bookings.alvearpalace.com"
CSS_SELECTOR = "#habitaciones"  # ← Verificar este selector
```

**Cómo verificar**:
1. Abrir sitio en browser
2. F12 → Consola
3. Ejecutar: `document.querySelector("#habitaciones")`
4. Debe retornar un elemento (no `null`)

Si retorna `null`: CSS_SELECTOR está mal, necesita actualización.

---

### Archivo: ScrawlingChinese/utils/scraper_utils.py

```python
# Configuración de browser
browser_config = BrowserConfig(
    headless=True,      # ← Cambiar a False para ver navegador
    wait_until="networkidle",  # ← Cambiar a "domcontentloaded" si es muy lento
    timeout=60000,      # ← Aumentar si hay timeouts (en ms)
)

# Configuración de LLM
llm_extraction_strategy = LLMExtractionStrategy(
    provider="groq",
    api_token=os.getenv("GROQ_API_KEY"),  # ← Verificar que existe
    schema=HotelWeb.model_json_schema(),   # ← Debe coincidir con estructura esperada
    extraction_type="schema",
    instruction="...",  # ← Prompt del LLM
)
```

**Parámetros ajustables para debugging**:

| Parámetro | Default | Debug | Uso |
|-----------|---------|-------|-----|
| `headless` | `True` | `False` | Ver navegador en acción |
| `wait_until` | `"networkidle"` | `"domcontentloaded"` | Acelerar carga |
| `timeout` | `60000` (60s) | `120000` (120s) | Páginas muy lentas |

---

## Problemas de Caché

### Síntoma

El scraper retorna datos viejos o desactualizados, incluso después de cambios en el sitio web.

### Causa

Archivo `hotel_guardado.pkl` cachea resultados anteriores.

### Solución 1: Eliminar Caché Manual

```bash
# Verificar si existe caché
ls hotel_guardado.pkl

# Eliminar caché (Linux/Mac)
rm hotel_guardado.pkl

# Eliminar caché (Windows)
del hotel_guardado.pkl

# Ejecutar scraper nuevamente
python Hoteles/app.py
```

### Solución 2: Usar force_fresh en Código

```python
from Core.controller import dar_hotel_web

# Forzar scraping fresco (ignora caché)
hotel_web = await dar_hotel_web(
    fecha_entrada="2026-02-01",
    fecha_salida="2026-02-05",
    adultos=2,
    ninos=0,
    force_fresh=True  # ← Bypass de caché
)
```

**Nota**: En comparación multi-periodo, `force_fresh=True` se usa automáticamente para evitar contaminación de caché entre periodos.

### Solución 3: Verificar Lógica de Caché

En `Core/gestor_datos.py`:

```python
# Línea ~50-70: Lógica de caché
if force_fresh:
    # Siempre scraping fresco, NO guardar en caché
    hotel_web = await crawl_alvear(...)
else:
    # Verificar caché memoria → caché archivo → scraping
    if self._hotel_web_cache is not None:
        return self._hotel_web_cache  # Caché memoria
    if os.path.exists("hotel_guardado.pkl"):
        # Cargar desde archivo
        ...
```

**Debugging**: Agregar prints para ver qué rama se ejecuta.

---

## Rate Limiting y IP Ban

### Síntoma

Error `429 Too Many Requests` o scraper se bloquea después de varios requests.

### Causa

Sitio web detecta demasiados requests rápidos y aplica rate limiting.

### Solución 1: Aumentar Delay entre Periodos

En `.env`:

```env
SCRAPING_DELAY_SECONDS=5  # Aumentar de 2 a 5 segundos
```

Reiniciar app después de cambiar `.env`.

### Solución 2: Esperar antes de Reintentar

```bash
# Esperar 5-10 minutos antes de volver a ejecutar comparación
# El rate limiting suele ser temporal (ventanas de tiempo)
```

### Solución 3: Verificar Logs del Servidor

Si tienes acceso a logs del servidor web:

```
2026-01-31 12:34:56 - IP 192.168.1.100 - Rate limit exceeded (10 req/min)
```

Ajustar delay para estar dentro del límite permitido.

### Solución 4: Usar Proxy Rotation (Avanzado)

**NO IMPLEMENTADO actualmente**, pero se puede agregar:

```python
# En ScrawlingChinese/utils/scraper_utils.py
browser_config = BrowserConfig(
    proxy="http://proxy-server:port",  # Rotar proxies
    # ...
)
```

---

## Logs y Diagnóstico Avanzado

### Habilitar Logs de Crawl4AI

```python
# En ScrawlingChinese/crawler.py
import logging

# Configurar logging al inicio
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("crawl4ai")
logger.setLevel(logging.DEBUG)
```

Ejecutar scraper y revisar logs detallados en consola.

---

### Verificar Reintentos

El scraper tiene lógica de reintentos (máx 3). Ver en `ScrawlingChinese/utils/scraper_utils.py`:

```python
# Línea ~40-60: Lógica de reintentos
for intento in range(1, 4):  # 3 intentos
    try:
        result = await crawler.arun(...)
        if result.extracted_content:
            break  # Éxito
    except Exception as e:
        print(f"Intento {intento}/3 falló: {e}")
        if intento == 3:
            raise  # Último intento, propagar error
```

Si ves múltiples intentos en consola:
- Primera razón de fallo: revisar primero
- Si falla 3 veces: problema más grave (selector, sitio caído, etc.)

---

### Inspeccionar Resultado Crudo

```python
# Guardar resultado completo en archivo para análisis
import json

resultado = asyncio.run(crawl_alvear(...))

# Guardar en JSON para inspección
with open("debug_scraper.json", "w", encoding="utf-8") as f:
    json.dump(resultado.model_dump(), f, indent=2, ensure_ascii=False)

print("Resultado guardado en debug_scraper.json")
```

Abrir `debug_scraper.json` y verificar:
- ¿Tiene habitaciones?
- ¿Precios son correctos?
- ¿Nombres de habitaciones son claros?

---

## Comandos Útiles

### Test Rápido del Scraper

Usar skill `/test-scraper`:

```bash
# Test con defaults
/test-scraper

# Test con fechas específicas
/test-scraper alvear 15-02-2026 20-02-2026 2 0
```

Ver detalles en [/.claude/skills/test-scraper.md](../../.claude/skills/test-scraper.md)

---

### Verificar Estructura HTML Actual

```bash
# Descargar HTML del sitio
curl https://bookings.alvearpalace.com > sitio_actual.html

# Buscar palabra clave (ej: "superior")
grep -i "superior" sitio_actual.html

# En Windows
findstr /i "superior" sitio_actual.html
```

---

## Checklist de Troubleshooting

Cuando el scraper falla, seguir en orden:

- [ ] ✅ Verificar conectividad al sitio web
- [ ] ✅ Verificar `GROQ_API_KEY` en `.env`
- [ ] ✅ Eliminar caché `hotel_guardado.pkl`
- [ ] ✅ Ejecutar scraper con debugging (prints)
- [ ] ✅ Inspeccionar HTML crudo
- [ ] ✅ Verificar CSS_SELECTOR en browser DevTools
- [ ] ✅ Revisar estructura JSON extraída por LLM
- [ ] ✅ Aumentar timeout si hay errores de tiempo
- [ ] ✅ Agregar delay si hay rate limiting
- [ ] ✅ Revisar logs de Crawl4AI

Si todo lo anterior falla:
- El sitio web cambió significativamente → Requiere actualización de código
- El LLM no puede extraer datos → Ajustar prompt o schema Pydantic

---

## Contacto y Soporte

Si ninguna solución funciona:

1. Documentar el problema:
   - Mensaje de error completo
   - Logs de consola
   - HTML crudo (primeros 1000 caracteres)
   - Configuración actual (config.py, scraper_utils.py)

2. Crear issue en GitHub (si aplica)

3. Consultar documentación de Crawl4AI: https://crawl4ai.com/docs

---

Ver también:
- [como-funciona.md](como-funciona.md) - Entender el flujo del scraper
- [configuracion.md](configuracion.md) - Configuración detallada
- [multi-sitio.md](multi-sitio.md) - Agregar nuevos hoteles