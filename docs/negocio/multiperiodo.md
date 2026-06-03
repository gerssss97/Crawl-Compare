# Sistema Multi-Periodo

Documentación completa del sistema de comparación multi-periodo, la funcionalidad central del proyecto.

## Tabla de Contenidos

- [¿Qué es Multi-Periodo?](#qué-es-multi-periodo)
- [Por Qué Scraping Secuencial](#por-qué-scraping-secuencial)
- [Flujo Completo](#flujo-completo)
- [Optimización: Fuzzy Matching UNA VEZ](#optimización-fuzzy-matching-una-vez)
- [Error Handling](#error-handling)
- [Configuración](#configuración)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## ¿Qué es Multi-Periodo?

El sistema multi-periodo permite comparar precios de una habitación a través de **múltiples periodos estacionales** en una sola ejecución.

### Problema que Resuelve

Los hoteles tienen precios diferentes según la época del año (low season, high season, easter, etc.). Una reserva que abarca múltiples meses puede incluir varios periodos diferentes.

**Ejemplo**:
- Reserva: 15 de mayo → 20 de junio
- Periodos involucrados:
  - Low season (1 mayo - 31 mayo): $120/noche
  - High season (1 junio - 30 junio): $180/noche

Sin multi-periodo, solo podríamos comparar UN periodo a la vez. Con multi-periodo, comparamos TODOS los periodos aplicables en una sola ejecución.

---

## Por Qué Scraping Secuencial

### Estrategia: Secuencial vs Paralelo

**Paralelo (NO usado)**:
```python
# Todos los periodos scrapeados simultáneamente
tasks = [crawl_alvear(periodo1), crawl_alvear(periodo2), crawl_alvear(periodo3)]
results = await asyncio.gather(*tasks)
```

❌ **Problemas**:
- Rate limiting: Servidor detecta muchos requests simultáneos
- IP ban: Bloqu

eo temporal o permanente
- Resultados inconsistentes: Carga del servidor variable

**Secuencial (USADO)**:
```python
# Un periodo a la vez con delay
for periodo in periodos:
    result = await crawl_alvear(periodo)
    await asyncio.sleep(DELAY)  # Esperar antes del siguiente
```

✅ **Ventajas**:
- Evita rate limiting
- Menor probabilidad de IP ban
- Resultados más consistentes
- Respetuoso con el servidor

### Trade-off Aceptado

**Tiempo de ejecución**:
- 1 periodo: ~3s
- 3 periodos secuenciales: ~15s (3×3s + 2×2s delay)

**Alternativa paralela**:
- 3 periodos paralelos: ~3s (en teoría)
- **PERO**: Alta probabilidad de bloqueo → 0 resultados

**Conclusión**: Preferimos 15s con resultados confiables vs 3s con riesgo de fallo.

---

## Flujo Completo

### Diagrama Mermaid

```mermaid
flowchart TD
    Start([Usuario ejecuta comparación]) --> InferirPeriodos[inferir_periodos_desde_fechas]
    InferirPeriodos --> CheckPeriodos{Periodos<br/>aplicables?}

    CheckPeriodos -->|No| ErrorNoPeriodos[Error: Sin periodos]
    CheckPeriodos -->|Sí| LoopStart[Loop por cada periodo]

    LoopStart --> LoopCheck{Más<br/>periodos?}
    LoopCheck -->|No| BuildResult[Construir ResultadoComparacionMultiperiodo]

    LoopCheck -->|Sí| PrintPeriodo[Print: --- PERIODO n/total ---]
    PrintPeriodo --> ScrapePeriodo[Scraping: dar_hotel_web<br/>force_fresh=True]

    ScrapePeriodo --> FirstPeriodo{Es primer<br/>periodo?}

    FirstPeriodo -->|Sí| FuzzyMatch[Fuzzy matching:<br/>encontrar_mejor_match]
    FirstPeriodo -->|No| ReuseMatch[Reusar habitación<br/>del 1er periodo]

    FuzzyMatch --> CheckMatch{Match<br/>encontrado?}
    CheckMatch -->|No| ErrorMatch[Error: No se encontró match]
    CheckMatch -->|Sí| SaveMatch[Guardar habitacion_web_matcheada]

    SaveMatch --> ExtractPrice
    ReuseMatch --> SearchHab[Buscar habitación por nombre]
    SearchHab --> CheckHabExists{Habitación<br/>existe?}
    CheckHabExists -->|No| ErrorHabDesaparecio[Error: Habitación desapareció]
    CheckHabExists -->|Sí| ExtractPrice[Extraer precio_web<br/>combos0.precio]

    ExtractPrice --> GetPrecioExcel[Obtener precio_excel<br/>habitacion_unificada.precio_para_periodo]
    GetPrecioExcel --> CheckPrecioExcel{Precio Excel<br/>válido?}
    CheckPrecioExcel -->|No| ErrorPrecioExcel[Error: Precio Excel None]

    CheckPrecioExcel -->|Sí| CalcDiff[Calcular diferencia<br/>precio_web - precio_excel]
    CalcDiff --> CheckCoincide{abs(diferencia)<br/>< 1.0?}

    CheckCoincide -->|Sí| SetCoincideTrue[coincide = True]
    CheckCoincide -->|No| SetCoincideFalse[coincide = False]

    SetCoincideTrue --> CreateResPeriodo[Crear ResultadoPeriodo]
    SetCoincideFalse --> CreateResPeriodo

    CreateResPeriodo --> CheckLastPeriodo{Es último<br/>periodo?}
    CheckLastPeriodo -->|Sí| LoopStart
    CheckLastPeriodo -->|No| Delay[Delay SCRAPING_DELAY_SECONDS<br/>default: 2s]
    Delay --> LoopStart

    BuildResult --> CheckDiscrep{tiene_discrepancias<br/>= any(not p.coincide)?}
    CheckDiscrep --> ReturnResult[Return ResultadoComparacionMultiperiodo]

    ErrorNoPeriodos --> End1([Fin - Error])
    ErrorMatch --> End1
    ErrorHabDesaparecio --> End1
    ErrorPrecioExcel --> End1
    ReturnResult --> End2([Fin - Éxito])

    style Start fill:#e1f5ff
    style End2 fill:#c8e6c9
    style End1 fill:#ffcdd2
```

### Paso a Paso Detallado

**Archivo**: [Core/comparador_multiperiodo.py](../../Hoteles/Core/comparador_multiperiodo.py)

#### 1. Inferir Periodos Aplicables

```python
from Core.servicio_habitaciones import inferir_periodos_desde_fechas

periodos_aplicables = inferir_periodos_desde_fechas(
    hotel=hotel,
    fecha_entrada=date(2026, 5, 15),
    fecha_salida=date(2026, 6, 20),
    periodo_ids_habitacion={1, 2, 3}  # IDs de periodos de la habitación
)
# Retorna: [Periodo(id=1, low season), Periodo(id=2, high season)]
```

**Lógica**: Detecta overlap entre rango de reserva y periodos de la habitación.

---

#### 2. Loop Secuencial por Periodo

```python
resultados_periodos = []
habitacion_web_matcheada = None

for i, periodo in enumerate(periodos_aplicables):
    print(f"\n--- PERIODO {i+1}/{len(periodos_aplicables)} ---")
    print(f"Scraping con fechas: {periodo.fecha_inicio} a {periodo.fecha_fin}")
```

---

#### 3. Scraping con force_fresh=True

```python
from Core.controller import dar_hotel_web

hotel_web = await dar_hotel_web(
    fecha_entrada=periodo.fecha_inicio.strftime("%Y-%m-%d"),
    fecha_salida=periodo.fecha_fin.strftime("%Y-%m-%d"),
    adultos=adultos,
    ninos=ninos,
    force_fresh=True  # ← CRÍTICO: Evita contaminar caché entre periodos
)
```

**Por qué `force_fresh=True`**:
- Cada periodo necesita datos frescos (precios cambian por periodo)
- Sin `force_fresh`, el caché retornaría datos del periodo anterior
- Ver [../scraper/troubleshooting.md#problemas-de-caché](../scraper/troubleshooting.md#problemas-de-caché)

---

#### 4. Fuzzy Matching (SOLO Primer Periodo)

```python
if i == 0:  # Primer periodo
    print("→ Realizando fuzzy matching (primer periodo)...")
    from Core.comparador import encontrar_mejor_match

    habitacion_web = encontrar_mejor_match(
        nombre_habitacion_excel=habitacion_unificada.nombre,
        resultado_web=hotel_web
    )

    if not habitacion_web:
        raise ValueError(f"No se encontró match para '{habitacion_unificada.nombre}'")

    habitacion_web_matcheada = habitacion_web  # Guardar para reutilizar
    print(f"→ Match encontrado: {habitacion_web.nombre}")

else:  # Periodos subsiguientes
    print(f"→ Reusando habitación matcheada: {habitacion_web_matcheada.nombre}")

    # Buscar por nombre en hotel_web del nuevo periodo
    habitacion_web = next(
        (h for h in hotel_web.habitacion
         if h.nombre == habitacion_web_matcheada.nombre),
        None
    )

    if not habitacion_web:
        raise ValueError(f"Habitación '{habitacion_web_matcheada.nombre}' desapareció en periodo {i+1}")
```

**Optimización**: Fuzzy matching es costoso (4 métricas × N habitaciones). Al hacerlo solo una vez y reusar el nombre, ahorramos ~70% del tiempo de procesamiento.

---

#### 5. Extraer Precios

```python
# Precio web (del primer combo)
precio_web = habitacion_web.combos[0].precio if habitacion_web.combos else 0.0
print(f"→ Precio web: ${precio_web:.2f}")

# Precio Excel (del periodo específico)
precio_excel = habitacion_unificada.precio_para_periodo(periodo.id)

if precio_excel is None:
    raise ValueError(f"Habitación sin precio para periodo {periodo.id}")

print(f"→ Precio Excel: {precio_excel}")
```

---

#### 6. Comparar y Crear ResultadoPeriodo

```python
if isinstance(precio_excel, (int, float)):
    diferencia = precio_web - precio_excel
    coincide = abs(diferencia) < 1.0
else:
    # Precio es leyenda ("closing agreement", etc.)
    diferencia = 0.0
    coincide = True  # No comparamos leyendas

print(f"→ Diferencia: ${diferencia:.2f} ({'COINCIDE' if coincide else 'DISCREPANCIA'})")

resultados_periodos.append(ResultadoPeriodo(
    periodo=periodo,
    precio_excel=precio_excel,
    precio_web=precio_web,
    diferencia=diferencia,
    coincide=coincide
))
```

---

#### 7. Delay Entre Periodos

```python
if i < len(periodos_aplicables) - 1:  # No delay en el último
    delay_seconds = int(os.getenv("SCRAPING_DELAY_SECONDS", "2"))
    print(f"→ Esperando {delay_seconds}s antes del siguiente periodo...")
    await asyncio.sleep(delay_seconds)
```

**Configurable** via variable de entorno `SCRAPING_DELAY_SECONDS`.

---

#### 8. Construir Resultado Final

```python
tiene_discrepancias = any(not r.coincide for r in resultados_periodos)

resultado = ResultadoComparacionMultiperiodo(
    habitacion_excel_nombre=habitacion_unificada.nombre,
    habitacion_web_matcheada=habitacion_web_matcheada,
    periodos=resultados_periodos,
    tiene_discrepancias=tiene_discrepancias,
    mensaje_match=f"Match: {habitacion_web_matcheada.nombre} (score: {score:.2f})"
)

print(f"\n{'='*60}")
print(f"RESULTADO: {'DISCREPANCIAS' if tiene_discrepancias else 'TODO OK'}")
print(f"{'='*60}")

return resultado
```

---

## Optimización: Fuzzy Matching UNA VEZ

### Antes (Ineficiente)

```python
for periodo in periodos:
    hotel_web = await scrape(periodo)
    habitacion = fuzzy_match(nombre_excel, hotel_web)  # ← Repetido N veces
    # ...
```

**Costo**: 4 métricas × 20 habitaciones web × 3 periodos = **240 cálculos**

### Después (Optimizado)

```python
hotel_web_primer_periodo = await scrape(periodos[0])
habitacion_matcheada = fuzzy_match(nombre_excel, hotel_web_primer_periodo)  # ← Solo una vez

for periodo in periodos:
    hotel_web = await scrape(periodo)
    habitacion = buscar_por_nombre(habitacion_matcheada.nombre, hotel_web)  # ← Búsqueda simple
    # ...
```

**Costo**: 4 métricas × 20 habitaciones × 1 vez + 2 búsquedas simples = **82 cálculos** (66% reducción)

### Asumción Clave

**"El nombre de la habitación en el sitio web NO cambia entre periodos"**

✅ **Válido en 99.9% de los casos**: "Double Superior Room" se llama igual todo el año.

❌ **Falla si**: Sitio web cambia nombres dinámicamente (ej: "Summer Double" → "Winter Double").

**Mitigación**: Si la habitación desaparece en un periodo subsiguiente, se lanza error claro.

---

## Error Handling

El sistema maneja 5 tipos de errores:

### 1. Sin Periodos Aplicables

```python
if not periodos_aplicables:
    raise ValueError("No hay periodos aplicables para el rango de fechas seleccionado")
```

**Cuándo ocurre**: Fechas de reserva no coinciden con ningún periodo de la habitación.

---

### 2. Fuzzy Matching Falla (Primer Periodo)

```python
if not habitacion_web:
    raise ValueError(f"No se encontró match para '{habitacion_unificada.nombre}'")
```

**Cuándo ocurre**: Nombre de habitación Excel muy diferente al sitio web.

**Solución**: Ajustar nombres en Excel o verificar que la habitación existe en el sitio.

---

### 3. Habitación Desaparece en Periodo Subsiguiente

```python
if not habitacion_web:
    raise ValueError(f"Habitación '{habitacion_web_matcheada.nombre}' desapareció en periodo {i+1}")
```

**Cuándo ocurre**: Sitio web NO muestra la habitación en ciertos periodos (sold out, no disponible).

**Solución**: Verificar disponibilidad real en el sitio.

---

### 4. Precio Excel None

```python
if precio_excel is None:
    raise ValueError(f"Habitación sin precio para periodo {periodo.id}")
```

**Cuándo ocurre**: Excel no tiene precio definido para ese periodo.

**Solución**: Verificar que `periodo_ids` de la habitación incluye el periodo.

---

### 5. Scraping Falla

```python
try:
    hotel_web = await dar_hotel_web(...)
except Exception as e:
    # Error capturado en capa superior (ControladorComparacion)
    raise RuntimeError(f"Error en scraping: {str(e)}")
```

**Cuándo ocurre**: Sitio web caído, timeout, CSS selector cambió.

**Solución**: Ver [../scraper/troubleshooting.md](../scraper/troubleshooting.md)

---

## Configuración

### Variables de Entorno

**Archivo**: `Hoteles/.env`

```env
# Delay entre periodos (segundos)
SCRAPING_DELAY_SECONDS=2

# API key de Groq (obligatorio)
GROQ_API_KEY=gsk_...
```

> El email no usa credenciales: abre el cliente del SO vía `mailto:`. Ver [email.md](email.md).

### Modificar Delay

```bash
# En Hoteles/.env
SCRAPING_DELAY_SECONDS=5  # Aumentar a 5 segundos
```

**Cuándo aumentar**:
- Rate limiting 429
- IP ban temporal
- Sitio web lento

**Cuándo disminuir**:
- Sitio web rápido y permisivo
- Testing local

---

## Ejemplos de Uso

### Uso desde Código

```python
import asyncio
from datetime import date
from Core.comparador_multiperiodo import comparar_multiperiodo
from Core.controller import dar_hoteles_excel
from Core.servicio_habitaciones import unificar_habitaciones

async def main():
    # Cargar datos
    hoteles = dar_hoteles_excel()
    hotel = hoteles[0]
    habitaciones_unif = unificar_habitaciones(hotel)
    habitacion = habitaciones_unif[0]

    # Ejecutar comparación multi-periodo
    resultado = await comparar_multiperiodo(
        hotel=hotel,
        habitacion_unificada=habitacion,
        fecha_entrada=date(2026, 5, 15),
        fecha_salida=date(2026, 6, 20),
        adultos=2,
        ninos=0
    )

    # Resultados
    print(resultado.resumen())
    # "2/3 periodos con discrepancia"

    for res_periodo in resultado.periodos:
        print(f"{res_periodo.periodo.nombre}: {res_periodo}")
        # "low season: Excel $150.0 vs Web $140.0 - ❌ DIFF"

asyncio.run(main())
```

---

### Uso desde UI (InterfazApp)

El usuario solo clickea "Ejecutar Comparación". El flujo completo es automático:

1. ControladorComparacion valida campos
2. Emite `comparison_started`
3. Ejecuta `comparar_multiperiodo()` en thread daemon
4. Emite `comparison_completed` con `ResultadoComparacionMultiperiodo`
5. VistaResultados muestra tabla comparativa

Ver [../arquitectura/flujos-principales.md#flujo-3-comparación-multi-periodo](../arquitectura/flujos-principales.md#flujo-3-comparación-multi-periodo)

---

### Uso desde Skill /multiperiodo-test

```bash
# Modo fake (inventar datos web con UI)
python .claude/skills/scripts/multiperiodo_test.py --modo fake

# Modo real (scraping de verdad)
python .claude/skills/scripts/multiperiodo_test.py --modo real
```

Ver [../../.claude/skills/multiperiodo-test.md](../../.claude/skills/multiperiodo-test.md)

---

## Tiempos de Ejecución

| Periodos | Scraping | Fuzzy Match | Delays | Total |
|----------|----------|-------------|--------|-------|
| 1 | 3s | 0.5s | 0s | ~3.5s |
| 2 | 6s (2×3s) | 0.5s | 2s | ~8.5s |
| 3 | 9s (3×3s) | 0.5s | 4s (2×2s) | ~13.5s |
| 5 | 15s (5×3s) | 0.5s | 8s (4×2s) | ~23.5s |

**Fórmula**: `Total = (N_periodos × 3s) + 0.5s + ((N_periodos - 1) × DELAY)`

---

## Referencias

- **Archivo principal**: [Core/comparador_multiperiodo.py](../../Hoteles/Core/comparador_multiperiodo.py)
- **Checkpoint técnico**: [../../Hoteles/CHECKPOINT_MULTIPERIODO.md](../../Hoteles/CHECKPOINT_MULTIPERIODO.md)
- **Flujo detallado**: [../arquitectura/flujos-principales.md](../arquitectura/flujos-principales.md)
- **Scraper troubleshooting**: [../scraper/troubleshooting.md](../scraper/troubleshooting.md)

---

Ver también:
- [comparacion.md](comparacion.md) - Fuzzy matching detallado
- [periodos.md](periodos.md) - Extracción y asignación de periodos
- [email.md](email.md) - Generación de emails multi-periodo
