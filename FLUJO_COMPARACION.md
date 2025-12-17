# Flujo de Comparación - Crawl-Compare

## Estado Actual de la Aplicación

**IMPORTANTE**: La aplicación ahora usa **EXCLUSIVAMENTE** comparación multi-periodo. El flujo single-periodo está **DEPRECATED** pero aún presente en el código.

---

## Flujo Activo (Multi-Periodo)

### 1. Usuario Presiona "Ejecutar Comparación"

**Archivo**: `UI/interfaz.py:628`

```
Usuario hace clic en botón
    ↓
ejecutar_comparacion_wrapper()
    ↓
ControladorComparacion.ejecutar_comparacion_async()
```

---

### 2. Controlador de Comparación

**Archivo**: `UI/controllers/controlador_comparacion.py`

```
ejecutar_comparacion_async()
    ↓
_run_async() [ejecuta en thread daemon]
    ↓
_ejecutar_comparacion() [método async principal]
    ↓
1. Emite evento 'comparison_started'
2. Valida todo con ControladorValidacion.validar_todo()
3. Obtiene datos del estado (fechas, adultos, niños, habitación)
4. Parsea fechas a objetos date
5. Busca hotel actual en hoteles_excel
6. Busca habitacion_unificada en habitaciones_unificadas
7. Llama a comparar_multiperiodo()
8. Emite evento 'comparison_completed' con resultado
```

---

### 3. Comparación Multi-Periodo

**Archivo**: `Core/comparador_multiperiodo.py`

```
comparar_multiperiodo(habitacion_unificada, fecha_entrada, fecha_salida, adultos, ninos, hotel)
    ↓
1. Infiere periodos aplicables desde habitacion_unificada.periodos
2. LOOP por cada periodo:
    a. Calcula fechas de scraping (inicio periodo o fecha_entrada, lo mayor)
    b. Llama a dar_hotel_web() con:
       - force_fresh=False
       - use_pickle=False
       - force_pickle=True (MODO TESTING) o False (PRODUCCIÓN)
    c. Si es primer periodo: Ejecuta fuzzy matching y guarda resultado
    d. Si es periodo subsiguiente: Reutiliza habitacion_web del primer match
    e. Obtiene precio del periodo actual
    f. Compara precio Excel vs Web
    g. Agrega resultado a lista
    h. Delay de 2 segundos (configurable)
3. Retorna ResultadoComparacionMultiperiodo
```

---

### 4. Obtención de Datos Web

**Archivo**: `Core/controller.py → Core/gestor_datos.py`

```
dar_hotel_web(fecha_ingreso, fecha_egreso, adultos, niños, force_fresh, use_pickle, force_pickle)
    ↓
gestor.obtener_hotel_web(...)
    ↓
DECISIÓN basada en parámetros:

├─ [force_pickle=True] → Carga pickle directo (TESTING)
│   └─ Retorna hotel_guardado_nuevos.pkl
│
├─ [force_fresh=False] → Intenta caché memoria
│   └─ Si fechas coinciden: Retorna self.__hotel_web
│
├─ [use_pickle=True AND force_fresh=False] → Intenta caché archivo
│   └─ Si existe: Carga pickle y retorna
│
└─ [Ninguno anterior] → Scraping FRESCO
    ├─ Convierte fechas a formato ISO
    ├─ Llama a crawl_alvear()
    ├─ Guarda en memoria
    └─ Si use_pickle=True: Guarda en archivo pickle
```

---

### 5. Visualización de Resultados

**Archivo**: `UI/interfaz.py`

```
EventBus emite 'comparison_completed'
    ↓
InterfazApp._on_comparison_completed(data)
    ↓
Detecta tipo de resultado:
    ├─ ResultadoComparacionMultiperiodo:
    │   └─ vista_resultados.mostrar_resultado_multiperiodo(resultado)
    │       ├─ Muestra tabla comparativa con todos los periodos
    │       ├─ Marca en ROJO periodos con discrepancias
    │       └─ Muestra detalles de habitación web
    │
    └─ dict (legacy):
        └─ Muestra mensaje simple (DEPRECATED)
```

---

## Flujo Deprecated (Single-Periodo)

### ⚠️ NO SE USA ACTUALMENTE

**Archivo**: `UI/interfaz.py:634-684`

```
ejecutar_comparacion() [DEPRECATED]
    ↓
Este método AÚN EXISTE pero NO SE LLAMA desde ejecutar_comparacion_wrapper()
    ├─ Valida fechas manualmente
    ├─ Llama a dar_hotel_web() directamente (línea 663)
    ├─ Llama a comparar_habitaciones() (single-periodo)
    └─ Muestra resultado simple en text widget
```

**Por qué existe aún**: Compatibilidad con código legacy que podría llamarlo directamente (como tests antiguos).

---

## Parámetros de Control de Caché

### force_pickle (TESTING)
- **`True`**: Carga pickle DIRECTO, ignora fechas, súper rápido
- **`False`**: Flujo normal
- **Uso**: Testing y desarrollo

### force_fresh (SCRAPING FRESCO)
- **`True`**: Ignora TODO caché, hace scraping siempre
- **`False`**: Intenta usar caché
- **Uso**: Cuando necesitás datos actualizados

### use_pickle (MULTI-PERIODO)
- **`True`**: Usa y guarda pickle
- **`False`**: Solo usa caché en memoria
- **Uso**: `False` para multi-periodo (cada periodo tiene fechas diferentes)

---

## Configuración Actual (TESTING MODE)

**Archivo**: `Core/comparador_multiperiodo.py:111-113`

```python
force_fresh=False,     # No fuerza scraping
use_pickle=False,      # No usa pickle (multi-periodo)
force_pickle=True      # CARGA PICKLE DIRECTO (TESTING)
```

### Para Volver a Producción

Cambiar a:
```python
force_fresh=False,     # Usa caché si existe
use_pickle=False,      # No contamina pickle con multi-periodo
force_pickle=False     # NO usa pickle, hace scraping
```

---

## Código Legacy a Eliminar (Futuro)

1. **`ejecutar_comparacion()`** en `interfaz.py:634-684`
2. **`run_async()`** en `interfaz.py:631-632`
3. **Llamada directa a `dar_hotel_web`** en `interfaz.py:663`

**NO eliminar aún**: Puede haber tests o scripts que dependan de estos métodos.

---

## Eventos del Sistema

### Emitidos por ControladorComparacion
- `comparison_started`: Comparación iniciada
- `comparison_completed`: Comparación exitosa (data: ResultadoComparacionMultiperiodo)
- `comparison_error`: Error en comparación (data: str mensaje)

### Escuchados por InterfazApp
- `comparison_started` → Limpia resultados previos
- `comparison_completed` → Muestra resultado multi-periodo
- `comparison_error` → Muestra error en messagebox

---

## Diagrama de Flujo Simplificado

```
[Usuario presiona botón]
         ↓
[ControladorComparacion]
         ↓
[comparar_multiperiodo]
         ↓
    ┌────────┐
    │ Loop   │ → [dar_hotel_web] → [Caché o Scraping]
    │ Por    │ → [Fuzzy Matching] (solo 1ra vez)
    │ Periodo│ → [Comparar Precios]
    └────────┘
         ↓
[ResultadoComparacionMultiperiodo]
         ↓
[EventBus: comparison_completed]
         ↓
[VistaResultados.mostrar_resultado_multiperiodo()]
         ↓
[Usuario ve tabla comparativa]
```

---

## Notas Importantes

1. **Multi-periodo es el estándar**: Aunque selecciones un solo periodo, el sistema usa el flujo multi-periodo.

2. **Fuzzy Matching una sola vez**: Para optimizar, el matching de habitaciones se hace SOLO en el primer periodo y se reutiliza.

3. **Caché inteligente**: Cada periodo hace su propio scraping con fechas específicas, pero el caché en memoria evita scraping duplicado en la misma sesión.

4. **Testing con pickle**: El modo `force_pickle=True` es para desarrollo rápido sin esperar scraping.

5. **Delays configurables**: El delay entre periodos (2s por defecto) está en `.env` como `SCRAPING_DELAY_SECONDS`.
