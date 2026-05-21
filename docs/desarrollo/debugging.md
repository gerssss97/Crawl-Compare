# Debugging del Proyecto

Guía completa de técnicas de debugging para el comparador de hoteles.

## EventBus Debug Mode

El sistema de eventos tiene un modo debug que muestra todos los eventos emitidos.

### Activar Debug Mode

Editar `UI/interfaz.py:25-30`:

```python
class InterfazApp:
    def __init__(self, root):
        self.root = root
        self.event_bus = EventBus()
        self.event_bus.enable_debug()  # ← Descomentar esta línea
```

### Output del Debug Mode

```
[EventBus] Evento 'hotel_changed' emitido con data: Alvear Palace
[EventBus] → Llamando callback: <function ControladorHotel.on_hotel_changed at 0x...>

[EventBus] Evento 'hotel_cargado' emitido con data: {'hotel': <HotelExcel>, 'tiene_tipos': True}
[EventBus] → Llamando callback: <function InterfazApp._on_hotel_cargado at 0x...>

[EventBus] Evento 'habitaciones_cargadas' emitido con data: ['dbl superior', 'jr suite', ...]
[EventBus] → Llamando callback: <function FormularioSeleccionHotel._on_habitaciones_cargadas at 0x...>
```

**Útil para:**
- ✅ Entender flujo completo de eventos
- ✅ Detectar eventos que no se disparan
- ✅ Detectar callbacks que no se ejecutan
- ✅ Identificar orden de ejecución incorrecto

---

## Print Debugging Estratégico

### Ubicaciones Clave con Prints

#### 1. Core/comparador_multiperiodo.py

**Líneas 45-180** - Muestra progreso detallado:

```python
print(f"\n{'='*80}")
print(f"🔍 Comparación Multi-Periodo")
print(f"{'='*80}\n")

for i, periodo in enumerate(periodos_aplicables, 1):
    print(f"[Periodo {i}/{len(periodos_aplicables)}] {periodo.nombre}")
    print(f"  Rango: {periodo.fecha_inicio} → {periodo.fecha_fin}")
    # ...
    print(f"  ✅ Precio Excel: ${precio_excel}")
    print(f"  🌐 Precio Web: ${precio_web}")
    print(f"  {'✅ OK' if coincide else '❌ DIFERENCIA'}: ${diferencia}")
```

**Para debugging específico**, agregar:

```python
# Después de línea 85 (scraping)
print(f"  DEBUG: Hotel web tiene {len(hotel_web.habitaciones)} habitaciones")
for hab in hotel_web.habitaciones[:3]:
    print(f"    - {hab.nombre}")

# Después de línea 120 (matching)
print(f"  DEBUG: Score de matching: {score:.2f}")
print(f"  DEBUG: Habitación matcheada: {habitacion_web.nombre}")
```

#### 2. Core/comparador.py

**Líneas 25-50** - Muestra scores de fuzzy matching:

```python
def encontrar_mejor_match(nombre_excel, habitaciones_web):
    # ...
    print(f"\n🔍 Fuzzy Matching:")
    print(f"  Excel: '{nombre_excel}'")

    for hab in habitaciones_web:
        score = calcular_score(nombre_excel, hab.nombre.lower())
        print(f"  {hab.nombre}: {score:.2f}")

    # ...
```

#### 3. ExtractorDatos/utils.py

**Líneas 15-80** - Muestra parsing de fechas:

```python
def extraer_fechas_de_texto(texto):
    print(f"\n📅 Extrayendo fechas de: '{texto}'")

    # ... lógica de extracción ...

    if fecha_inicio and fecha_fin:
        print(f"  ✅ Encontradas: {fecha_inicio} → {fecha_fin}")
    else:
        print(f"  ⚠️  No se encontraron fechas válidas")
```

#### 4. UI/interfaz.py

**Líneas 180-220** - Muestra cambios de estado:

```python
def _on_hotel_changed(self, data):
    print(f"\n🏨 Hotel cambió: {data.get('hotel').nombre if isinstance(data, dict) else data}")
    # ...

def _on_habitacion_changed(self, data):
    print(f"\n🛏️  Habitación cambió: {data}")
    # ...
```

---

## Inspección de AppState en Runtime

### Ver Estado Completo

Agregar breakpoint en `UI/interfaz.py` donde necesites:

```python
def _on_comparison_completed(self, data):
    # Inspeccionar estado completo
    print("\n" + "="*80)
    print("📊 ESTADO COMPLETO DE LA APP")
    print("="*80)
    print(f"Hotel: {self.state.hotel.get()}")
    print(f"Edificio: {self.state.edificio.get()}")
    print(f"Habitación: {self.state.habitacion.get()}")
    print(f"Fecha entrada: {self.state.fecha_entrada_completa.get()}")
    print(f"Fecha salida: {self.state.fecha_salida_completa.get()}")
    print(f"Adultos: {self.state.adultos.get()}")
    print(f"Niños: {self.state.ninos.get()}")
    print(f"Precio: {self.state.precio.get()}")
    print(f"Hoteles Excel cargados: {len(self.state.hoteles_excel)}")
    print(f"Habitaciones Excel: {len(self.state.habitaciones_excel)}")
    print(f"Habitaciones unificadas: {len(self.state.habitaciones_unificadas)}")

    if self.state.resultado_multiperiodo:
        print(f"Resultado multi-periodo: {self.state.resultado_multiperiodo.tiene_discrepancias}")

    print("="*80 + "\n")
```

### Ver Periodos de Habitación Actual

```python
def _on_habitacion_changed(self, habitacion_nombre):
    # Buscar habitación unificada actual
    hab_unificada = next(
        (h for h in self.state.habitaciones_unificadas if h.nombre == habitacion_nombre),
        None
    )

    if hab_unificada:
        print(f"\n🛏️  Habitación: {hab_unificada.nombre}")
        print(f"  Periodos aplicables: {len(hab_unificada.periodos)}")
        for periodo in hab_unificada.periodos:
            print(f"    - {periodo.nombre}: {periodo.fecha_inicio} → {periodo.fecha_fin}")
```

---

## Debugging de Scraper

### Ver HTML Crudo

Modificar `ScrawlingChinese/utils/scraper_utils.py:60`:

```python
async def scrape_with_llm(session, url, schema, params):
    result = await crawler.arun(
        url=url,
        # ... params ...
    )

    # DEBUG: Guardar HTML crudo
    with open('debug_html_raw.html', 'w', encoding='utf-8') as f:
        f.write(result.html)

    print(f"✅ HTML guardado en: debug_html_raw.html")
```

**Inspeccionar**: Abrir `debug_html_raw.html` en navegador y verificar que la página se cargó correctamente.

### Ver Input del LLM

Modificar `ScrawlingChinese/utils/scraper_utils.py:75`:

```python
# Antes de llamar al LLM
llm_input = {
    'schema': schema,
    'html_snippet': result.html[:1000]  # Primeros 1000 chars
}

with open('debug_llm_input.json', 'w', encoding='utf-8') as f:
    json.dump(llm_input, f, indent=2, ensure_ascii=False)

print(f"✅ Input LLM guardado en: debug_llm_input.json")
```

### Ver Output del LLM

```python
# Después de recibir respuesta del LLM
with open('debug_llm_output.json', 'w', encoding='utf-8') as f:
    json.dump(extracted_data, f, indent=2, ensure_ascii=False)

print(f"✅ Output LLM guardado en: debug_llm_output.json")
```

### Logs de Crawl4AI

Activar en `debug_config.py`:

```python
DEBUG_CRAWL4AI_VERBOSE = True
```

Esto habilita simultáneamente:
- Los logs verbosos de Crawl4AI (`[INIT]`, `[FETCH]`, `[SCRAPE]`, `[LOG]`, `[EXTRACT]`, `[COMPLETE]`) en `BrowserConfig` y `LLMExtractionStrategy`
- El print de `[DEBUG] obtener_hotel_web llamado con: ...` y los prints de cache/pickle en `Core/gestor_datos.py`

### Pipeline de Scraping (3 niveles)

Para diagnosticar **por qué falla un scrape** (sobre todo dentro del `.exe`, donde no podés meter prints ad-hoc), está `DEBUG_SCRAPING_PIPELINE` (default `True`). Vuelca al stdout — y por lo tanto a `output.log` en el `.exe` — tres niveles del pipeline en `ScrawlingChinese/utils/scraper_utils.py`:

| Nivel | Qué loguea |
|-------|-----------|
| **L1-Crawl** | `result.success`, `status_code`, `error_message`, y tamaño del HTML y markdown que devolvió Crawl4AI. Si esto falla, el problema es de browser/red, no del LLM. |
| **L2-Markdown** | Chars, tokens estimados y preview (200 chars) del markdown que se le pasa a Groq. Sirve para ver si el markdown está vacío o truncado antes del LLM. |
| **L3-Groq** | Respuesta cruda del LLM (preview de 500 chars), si el JSON parsea correctamente, y la razón exacta por la que se marcó el resultado como "incompleto". |

**Cuándo usarlo**:
- Falla el scraping en el `.exe` pero anda en dev → activar y revisar `output.log` para ver en qué nivel se rompe.
- El LLM devuelve datos incompletos → mirá L3-Groq para ver el motivo exacto.
- Sospechás que el markdown llega vacío → mirá L2-Markdown.

> Para guardar el markdown completo a archivo (no stdout), usar `DEBUG_LLM_MARKDOWN = True` — pero ojo que crea un `debug_llm_input_*.txt` por cada intento. Para diagnóstico puntual en `.exe`, `DEBUG_SCRAPING_PIPELINE` alcanza.

---

## Debugging de Validaciones

### Validación de Fechas

Agregar prints en `UI/controllers/controlador_validacion.py:30-60`:

```python
def validar_fechas(self):
    entrada = self.estado_app.fecha_entrada_completa.get()
    salida = self.estado_app.fecha_salida_completa.get()

    print(f"\n📅 Validando fechas:")
    print(f"  Entrada: '{entrada}'")
    print(f"  Salida: '{salida}'")

    if not entrada or not salida:
        print(f"  ❌ Campos vacíos")
        return False, "Ingrese ambas fechas"

    try:
        fecha_entrada_obj = datetime.strptime(entrada, "%d-%m-%Y")
        fecha_salida_obj = datetime.strptime(salida, "%d-%m-%Y")
        print(f"  ✅ Parsing exitoso")
    except ValueError as e:
        print(f"  ❌ Error de parsing: {e}")
        return False, "Formato de fecha inválido"

    # ... más validaciones ...
```

### Validación de Precio Actualizado

```python
def validar_precio_actualizado(self):
    precio = self.estado_app.precio.get()

    print(f"\n💰 Validando precio:")
    print(f"  Valor: '{precio}'")

    if precio == "(ninguna seleccionada)":
        print(f"  ❌ Precio no actualizado")
        return False

    print(f"  ✅ Precio válido")
    return True
```

---

## Debugging de Threading

### Ver Thread en Ejecución

En `UI/controllers/controlador_comparacion.py:45`:

```python
def ejecutar_comparacion_async(self):
    print(f"\n🧵 Thread actual: {threading.current_thread().name}")
    print(f"  Is daemon: {threading.current_thread().daemon}")

    thread = threading.Thread(
        target=self._ejecutar_comparacion_thread,
        daemon=True,
        name="ComparacionWorker"
    )

    print(f"🚀 Iniciando thread: {thread.name}")
    thread.start()
```

### Ver Excepciones en Threads

```python
def _ejecutar_comparacion_thread(self):
    try:
        # ... lógica ...
    except Exception as e:
        print(f"\n❌ ERROR EN THREAD:")
        print(f"  Tipo: {type(e).__name__}")
        print(f"  Mensaje: {str(e)}")

        import traceback
        traceback.print_exc()

        self.event_bus.emit('comparison_error', str(e))
```

---

## Debugging Avanzado con pdb

### Breakpoint en Código

```python
# En cualquier archivo
import pdb; pdb.set_trace()  # Execution se pausa aquí
```

**Comandos útiles:**
- `n` - next line
- `s` - step into function
- `c` - continue execution
- `p variable` - print variable
- `pp variable` - pretty print
- `l` - list code around current line
- `q` - quit debugger

### Ejemplo en comparador_multiperiodo.py

```python
def comparar_multiperiodo(habitacion_unificada, ...):
    # ...

    for i, periodo in enumerate(periodos_aplicables):
        import pdb; pdb.set_trace()  # Pausa en cada periodo

        # Inspeccionar variables
        # (pdb) p periodo.nombre
        # (pdb) p precio_excel
        # (pdb) pp hotel_web.habitaciones
```

---

## Troubleshooting Común

### Problema: EventBus no dispara eventos

**Debug:**
```python
# En UI/state/event_bus.py, agregar al método emit():
def emit(self, event_name, data=None):
    print(f"[EventBus] emit() llamado: {event_name}")
    print(f"  Listeners registrados: {len(self._listeners.get(event_name, []))}")

    if event_name not in self._listeners:
        print(f"  ⚠️  No hay listeners para '{event_name}'")

    # ... resto del código ...
```

### Problema: Fuzzy matching da resultados incorrectos

**Debug:**
```python
# Usar skill /compare-debug
python .claude/skills/scripts/compare_debug.py \
  "habitacion excel" \
  "habitacion web 1" \
  "habitacion web 2" \
  "habitacion web 3"
```

Ver scores individuales y ajustar pesos en `Core/comparador.py:18-22`.

### Problema: Scraper no extrae datos

**Checklist:**
1. ✅ Verificar HTML crudo se descarga (ver arriba)
2. ✅ Verificar CSS_SELECTOR es correcto
3. ✅ Verificar schema Pydantic coincide con HTML
4. ✅ Verificar API key de Groq es válida
5. ✅ Ver logs de Crawl4AI (activar logging)

### Problema: Multi-periodo falla en un periodo específico

**Debug:**
```python
# En Core/comparador_multiperiodo.py:100, agregar try-except detallado:
for i, periodo in enumerate(periodos_aplicables):
    try:
        # ... lógica ...
    except Exception as e:
        print(f"\n❌ ERROR en periodo {i+1}: {periodo.nombre}")
        print(f"  Excepción: {type(e).__name__}: {str(e)}")

        import traceback
        traceback.print_exc()

        # Continuar con siguiente periodo
        continue
```

### Problema: UI se congela

**Causa**: Operación bloqueante en main thread.

**Solución**: Mover lógica pesada a thread daemon:

```python
import threading

def operacion_pesada():
    # ... código que tarda ...
    pass

thread = threading.Thread(target=operacion_pesada, daemon=True)
thread.start()
```

---

## Herramientas Útiles

### Ver Estructura de Objetos Pydantic

```python
from Models.hotelExcel import HotelExcel

# Cargar hotel
hotel = ...  # Tu objeto HotelExcel

# Pretty print
import json
print(json.dumps(hotel.model_dump(), indent=2, ensure_ascii=False))
```

### Benchmark de Performance

```python
import time

start = time.time()
# ... código a medir ...
end = time.time()

print(f"⏱️  Tiempo: {end - start:.2f}s")
```

### Memory Profiling (Opcional)

```bash
pip install memory_profiler

# Decorar función a perfilar
from memory_profiler import profile

@profile
def mi_funcion():
    # ...
    pass

# Ejecutar
python -m memory_profiler mi_script.py
```

---

Ver también:
- [testing.md](testing.md) - Tests automatizados
- [../scraper/troubleshooting.md](../scraper/troubleshooting.md) - Problemas específicos de scraping
- [../arquitectura/event-driven-mvc.md](../arquitectura/event-driven-mvc.md) - Entender flujo de eventos
