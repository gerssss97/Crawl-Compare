# Controladores UI

Documentación completa de los controladores UI que orquestan la lógica de negocio sin dependencias directas de widgets.

Todos los controladores siguen el pattern: `__init__(estado_app, event_bus)` y usan eventos para comunicarse.

## Tabla de Contenidos

- [ControladorHotel](#controladorhotel)
- [ControladorValidacion](#controladorvalidacion)
- [ControladorComparacion](#controladorcomparacion)
- [ControladorPrecios](#controladorprecios)

---

## ControladorHotel

**Archivo**: [UI/controllers/controlador_hotel.py](../../Hoteles/UI/controllers/controlador_hotel.py)

### Propósito

Gestiona la carga de hoteles, edificios y habitaciones desde Excel. Agrupa habitaciones por periodos.

### Responsabilidades

- Cargar lista de hoteles desde estado
- Cargar edificios/tipos según hotel seleccionado
- Cargar habitaciones según hotel/edificio
- Agrupar habitaciones por periodos aplicables
- Emitir eventos cuando se cargan datos

### Constructor

```python
def __init__(self, estado_app: AppState, event_bus: EventBus):
    self.estado_app = estado_app
    self.event_bus = event_bus

    # Suscribirse a eventos
    self.event_bus.on('hotel_changed', self.on_hotel_changed)
    self.event_bus.on('edificio_changed', self.on_edificio_changed)
```

### Métodos Principales

#### `cargar_hoteles() → list[str]`
Carga lista de nombres de hoteles (sin duplicados, sin sufijo "(A)").

```python
hoteles = controlador.cargar_hoteles()
# ["Alvear Palace", "Four Seasons", "Marriott"]
```

**Implementación**:
```python
def cargar_hoteles(self):
    hoteles = self.estado_app.hoteles_excel
    nombres = [h.nombre.replace(" (A)", "").strip() for h in hoteles]
    return list(set(nombres))  # Sin duplicados
```

---

#### `cargar_edificios(hotel_nombre: str) → list[str]`
Carga nombres únicos de edificios/tipos de un hotel.

```python
edificios = controlador.cargar_edificios("Alvear Palace")
# ["Palace Wing", "Garden Wing"]
```

**Implementación**:
```python
def cargar_edificios(self, hotel_nombre):
    # Buscar hotel
    hotel = next((h for h in self.estado_app.hoteles_excel
                 if hotel_nombre in h.nombre), None)

    if not hotel or not hotel.tipos:
        return []

    # Nombres únicos
    return list(set([t.nombre for t in hotel.tipos]))
```

---

#### `cargar_habitaciones(hotel_nombre: str, edificio_nombre: str = None) → list[str]`
Carga nombres de habitaciones unificadas (sin duplicados).

```python
# Habitaciones de hotel sin tipos
habitaciones = controlador.cargar_habitaciones("Hotel Simple")
# ["dbl superior", "dbl deluxe", "suite"]

# Habitaciones de edificio específico
habitaciones = controlador.cargar_habitaciones("Alvear Palace", "Palace Wing")
# ["dbl superior palace", "dbl deluxe palace"]
```

**Implementación**:
```python
def cargar_habitaciones(self, hotel_nombre, edificio_nombre=None):
    from Core.servicio_habitaciones import unificar_habitaciones

    hotel = next((h for h in self.estado_app.hoteles_excel
                 if hotel_nombre in h.nombre), None)

    if not hotel:
        return []

    # Obtener habitaciones unificadas
    habitaciones_unif = unificar_habitaciones(hotel)

    # Filtrar por edificio si es necesario
    if edificio_nombre:
        habitaciones_unif = [h for h in habitaciones_unif
                            if h.tipo_origen and h.tipo_origen.nombre == edificio_nombre]

    # Nombres únicos
    nombres = list(set([h.nombre for h in habitaciones_unif]))
    return sorted(nombres)
```

---

### Event Handlers

#### `on_hotel_changed(hotel_nombre: str)`
Maneja evento cuando cambia selección de hotel.

```python
def on_hotel_changed(self, hotel_nombre):
    # Buscar hotel
    hotel = next((h for h in self.estado_app.hoteles_excel
                 if hotel_nombre in h.nombre), None)

    if not hotel:
        return

    # Determinar si tiene tipos
    tiene_tipos = bool(hotel.tipos)

    # Emitir evento con datos
    self.event_bus.emit('hotel_cargado', {
        'hotel': hotel,
        'tiene_tipos': tiene_tipos
    })

    # Si NO tiene tipos → cargar habitaciones directas
    if not tiene_tipos:
        habitaciones = self.cargar_habitaciones(hotel_nombre)
        self.event_bus.emit('habitaciones_cargadas', habitaciones)
```

**Eventos emitidos**:
- `hotel_cargado` - data: `{hotel: HotelExcel, tiene_tipos: bool}`
- `habitaciones_cargadas` - data: `list[str]` (si no tiene tipos)

---

#### `on_edificio_changed(edificio_nombre: str)`
Maneja evento cuando cambia selección de edificio.

```python
def on_edificio_changed(self, edificio_nombre):
    hotel_nombre = self.estado_app.hotel.get()
    habitaciones = self.cargar_habitaciones(hotel_nombre, edificio_nombre)
    self.event_bus.emit('habitaciones_cargadas', habitaciones)
```

**Eventos emitidos**:
- `habitaciones_cargadas` - data: `list[str]`

---

### Tabla de Eventos

| Evento | Escucha/Emite | Data | Descripción |
|--------|---------------|------|-------------|
| `hotel_changed` | ✅ Escucha | `str` (nombre hotel) | AppState detectó cambio en combobox |
| `edificio_changed` | ✅ Escucha | `str` (nombre edificio) | AppState detectó cambio |
| `hotel_cargado` | ⬆️ Emite | `{hotel, tiene_tipos}` | Hotel cargado con metadata |
| `habitaciones_cargadas` | ⬆️ Emite | `list[str]` | Habitaciones disponibles |

---

## ControladorValidacion

**Archivo**: [UI/controllers/controlador_validacion.py](../../Hoteles/UI/controllers/controlador_validacion.py)

### Propósito

Valida campos del formulario antes de ejecutar comparación. NO escucha eventos (se llama directamente).

### Responsabilidades

- Validar formato de fechas (DD-MM-AAAA)
- Validar existencia de fechas
- Validar orden de fechas (salida > entrada)
- Validar que todos los campos estén completos
- Mostrar mensajes de error al usuario

### Constructor

```python
def __init__(self, estado_app: AppState):
    self.estado_app = estado_app
    # NO recibe event_bus
```

### Métodos Principales

#### `validar_fecha(fecha_str: str, nombre_campo: str) → bool`
Valida formato y existencia de una fecha.

```python
if not controlador.validar_fecha("15-02-2026", "Fecha de entrada"):
    # Error mostrado, retornar
    pass
```

**Validaciones**:
1. Campo no vacío
2. Formato DD-MM-AAAA
3. Fecha válida (no 31 de febrero, etc.)

**Errores mostrados**:
- "El campo 'Fecha de entrada' no puede estar vacío"
- "Formato de fecha inválido. Use DD-MM-AAAA"
- "Fecha inválida: 31-02-2026"

---

#### `validar_orden_fechas(fecha_entrada: str, fecha_salida: str) → bool`
Valida que fecha_salida > fecha_entrada.

```python
if not controlador.validar_orden_fechas("15-02-2026", "20-02-2026"):
    # Error mostrado
    pass
```

**Error mostrado**:
- "La fecha de salida debe ser posterior a la fecha de entrada"

---

#### `validar_campos_completos() → bool`
Valida que hotel, habitación y precio estén seleccionados.

```python
if not controlador.validar_campos_completos():
    # Error mostrado
    pass
```

**Validaciones**:
1. Hotel seleccionado
2. Habitación seleccionada
3. Precio actualizado (no "(ninguna seleccionada)")

**Errores mostrados**:
- "Debe seleccionar un hotel"
- "Debe seleccionar una habitación"
- "El campo 'Precio' no puede estar vacío"

---

#### `validar_todo() → bool`
Ejecuta todas las validaciones en orden.

```python
if controlador.validar_todo():
    # Todas las validaciones pasaron → ejecutar comparación
    pass
```

**Orden de validación**:
1. `validar_fecha(fecha_entrada)`
2. `validar_fecha(fecha_salida)`
3. `validar_orden_fechas()`
4. `validar_campos_completos()`

**Retorna**: `True` si todas las validaciones pasan, `False` si alguna falla.

---

### Ejemplo de Uso

```python
from UI.controllers.controlador_validacion import ControladorValidacion
from UI.state.app_state import AppState
from UI.state.event_bus import EventBus
from tkinter import messagebox

event_bus = EventBus()
estado_app = AppState(event_bus)

# Configurar estado
estado_app.hotel.set("Alvear Palace")
estado_app.habitacion.set("dbl superior")
estado_app.precio.set("$150.00")
estado_app.fecha_entrada_completa.set("15-02-2026")
estado_app.fecha_salida_completa.set("20-02-2026")

# Crear controlador
controlador = ControladorValidacion(estado_app)

# Validar todo
if controlador.validar_todo():
    print("✅ Validación exitosa")
else:
    print("❌ Validación falló")
```

---

## ControladorComparacion

**Archivo**: [UI/controllers/controlador_comparacion.py](../../Hoteles/UI/controllers/controlador_comparacion.py)

### Propósito

Ejecuta la comparación multi-periodo de forma asíncrona sin bloquear la UI.

### Responsabilidades

- Validar campos antes de comparar
- Ejecutar comparación en thread daemon
- Emitir eventos de inicio/fin/error
- Manejar excepciones durante comparación

### Constructor

```python
def __init__(self, estado_app: AppState, event_bus: EventBus, controlador_validacion: ControladorValidacion):
    self.estado_app = estado_app
    self.event_bus = event_bus
    self.controlador_validacion = controlador_validacion
```

**Nota**: Recibe `controlador_validacion` como dependencia.

---

### Métodos Principales

#### `ejecutar_comparacion_async()`
Dispara comparación en background thread.

```python
controlador.ejecutar_comparacion_async()
# Retorna inmediatamente, comparación corre en background
```

**Flujo**:
1. Crea thread daemon
2. Ejecuta `_run_async()` en el thread
3. Retorna inmediatamente (no bloquea)

**Implementación**:
```python
def ejecutar_comparacion_async(self):
    def run_async():
        asyncio.run(self._ejecutar_comparacion())

    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
```

---

#### `_run_async()` (interno)
Wrapper para ejecutar función async en thread.

---

#### `_ejecutar_comparacion()` (async, interno)
Función async principal que ejecuta la comparación.

```python
async def _ejecutar_comparacion(self):
    # 1. Validar campos
    if not self.controlador_validacion.validar_todo():
        return  # Validación falló, mensajes ya mostrados

    # 2. Emitir evento de inicio
    self.event_bus.emit('comparison_started')

    try:
        # 3. Parsear fechas
        fecha_entrada = datetime.strptime(fecha_entrada_str, "%d-%m-%Y").date()
        fecha_salida = datetime.strptime(fecha_salida_str, "%d-%m-%Y").date()

        # 4. Buscar hotel y habitación
        hotel = next((h for h in self.estado_app.hoteles_excel
                     if habitacion_nombre in h.nombre), None)

        habitacion_unificada = next(
            (h for h in self.estado_app.habitaciones_unificadas
             if h.nombre == habitacion_nombre),
            None
        )

        # 5. Ejecutar comparación multi-periodo
        from Core.comparador_multiperiodo import comparar_multiperiodo

        resultado = await comparar_multiperiodo(
            hotel=hotel,
            habitacion_unificada=habitacion_unificada,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            adultos=adultos,
            ninos=ninos
        )

        # 6. Guardar resultado en estado
        self.estado_app.resultado_multiperiodo = resultado

        # 7. Emitir evento de completado
        self.event_bus.emit('comparison_completed', resultado)

    except Exception as e:
        # Emitir evento de error
        self.event_bus.emit('comparison_error', str(e))
```

---

### Tabla de Eventos

| Evento | Escucha/Emite | Data | Descripción |
|--------|---------------|------|-------------|
| `comparison_started` | ⬆️ Emite | `None` | Comparación iniciada |
| `comparison_completed` | ⬆️ Emite | `ResultadoComparacionMultiperiodo` | Comparación exitosa |
| `comparison_error` | ⬆️ Emite | `str` (mensaje error) | Error durante comparación |

---

### Ejemplo de Uso

```python
from UI.controllers.controlador_comparacion import ControladorComparacion
from UI.controllers.controlador_validacion import ControladorValidacion
from UI.state.app_state import AppState
from UI.state.event_bus import EventBus

event_bus = EventBus()
estado_app = AppState(event_bus)

# Crear controladores
controlador_validacion = ControladorValidacion(estado_app)
controlador_comparacion = ControladorComparacion(estado_app, event_bus, controlador_validacion)

# Suscribirse a eventos
def on_started():
    print("🔄 Comparación iniciada...")

def on_completed(resultado):
    print(f"✅ Comparación completada: {resultado.resumen()}")

def on_error(mensaje):
    print(f"❌ Error: {mensaje}")

event_bus.on('comparison_started', on_started)
event_bus.on('comparison_completed', on_completed)
event_bus.on('comparison_error', on_error)

# Configurar estado (hotel, habitación, fechas, etc.)
# ...

# Ejecutar
controlador_comparacion.ejecutar_comparacion_async()
# Retorna inmediatamente, eventos se emiten cuando termine
```

---

## ControladorPrecios

**Archivo**: [UI/controllers/controlador_precios.py](../../Hoteles/UI/controllers/controlador_precios.py)

### Propósito

Calcula precio de habitación según periodos aplicables y actualiza `AppState.precio`.

### Responsabilidades

- Escuchar cambio de habitación
- Calcular precio según periodos y fechas
- Actualizar `AppState.precio` dinámicamente
- Emitir evento `precios_actualizados`

### Constructor

```python
def __init__(self, estado_app: AppState, event_bus: EventBus):
    self.estado_app = estado_app
    self.event_bus = event_bus

    # Suscribirse a eventos
    self.event_bus.on('habitacion_unificada_changed', self.on_habitacion_changed)
    # También escucha cambios en fechas (traces en AppState)
```

---

### Métodos Principales

#### `calcular_precio(habitacion_unificada: HabitacionUnificada, hotel: HotelExcel) → str`
Calcula precio según periodos aplicables.

**Lógica**:
1. Si NO hay fechas → `"(ninguna seleccionada)"`
2. Si NO hay periodos aplicables → `"(sin periodos aplicables)"`
3. Si hay 1 periodo → Precio simple (ej: `"$150.00"`)
4. Si hay múltiples periodos con mismo precio → Precio simple
5. Si hay múltiples periodos con precios diferentes → Rango (ej: `"$120.00 - $180.00"`)

```python
precio_str = controlador.calcular_precio(habitacion_unificada, hotel)
# "$150.00" o "$120.00 - $180.00" o "(ninguna seleccionada)"
```

**Implementación** (simplificada):
```python
def calcular_precio(self, habitacion_unificada, hotel):
    # Sin fechas
    if not self.estado_app.fecha_entrada_completa.get():
        return "(ninguna seleccionada)"

    # Inferir periodos aplicables
    periodos_aplicables = inferir_periodos_desde_fechas(
        hotel,
        fecha_entrada,
        fecha_salida,
        habitacion_unificada.periodo_ids
    )

    if not periodos_aplicables:
        return "(sin periodos aplicables)"

    # Obtener precios de cada periodo
    precios = []
    for periodo in periodos_aplicables:
        precio = habitacion_unificada.precio_para_periodo(periodo.id)
        if isinstance(precio, (int, float)):
            precios.append(precio)

    if not precios:
        return "(sin precio)"

    # Un solo precio o todos iguales
    if len(set(precios)) == 1:
        return f"${precios[0]:.2f}"

    # Múltiples precios diferentes
    return f"${min(precios):.2f} - ${max(precios):.2f}"
```

---

#### `on_habitacion_changed(habitacion_nombre: str)`
Maneja evento cuando cambia habitación seleccionada.

```python
def on_habitacion_changed(self, habitacion_nombre):
    # Buscar habitación unificada
    habitacion = next((h for h in self.estado_app.habitaciones_unificadas
                      if h.nombre == habitacion_nombre), None)

    if not habitacion:
        return

    # Buscar hotel
    hotel = next((h for h in self.estado_app.hoteles_excel
                 if hotel_nombre in h.nombre), None)

    # Calcular precio
    precio_str = self.calcular_precio(habitacion, hotel)

    # Actualizar estado
    self.estado_app.precio.set(precio_str)

    # Emitir evento
    self.event_bus.emit('precios_actualizados', {
        'tipo': 'calculado',
        'precio': precio_str,
        'habitacion': habitacion
    })
```

---

### Tabla de Eventos

| Evento | Escucha/Emite | Data | Descripción |
|--------|---------------|------|-------------|
| `habitacion_unificada_changed` | ✅ Escucha | `HabitacionUnificada` | Habitación seleccionada cambió (emitido desde `_on_habitacion_changed` en CrawlCompareGUI) |
| `precios_actualizados` | ⬆️ Emite | ver abajo | Precio(s) calculados y actualizados |

**Formatos del evento `precios_actualizados`**:

```python
# Precios calculados exitosamente
{
    'tipo': 'precios_calculados',
    'precios': [
        {'periodo': Periodo, 'precio': float, 'nombre_grupo': str},
        ...
    ]
}

# Sin fechas ingresadas
{
    'tipo': 'sin_fechas',
    'mensaje': str
}

# Sin periodos aplicables para las fechas
{
    'tipo': 'sin_periodos',
    'mensaje': str
}
```

`CrawlCompareGUI._on_precios_actualizados()` despacha:
- `tipo == 'precios_calculados'` → `CTkPrecioPanel.mostrar_precios_multiples(data['precios'])`
- `tipo in ('sin_fechas', 'sin_periodos')` → `CTkPrecioPanel._mostrar_mensaje(data['mensaje'])`

---

## Diagrama de Interacción entre Controladores

```mermaid
sequenceDiagram
    participant Usuario
    participant EventBus
    participant CtrlHotel
    participant CtrlPrecios
    participant CtrlValidacion
    participant CtrlComparacion

    Usuario->>EventBus: Selecciona hotel
    EventBus->>CtrlHotel: hotel_changed
    CtrlHotel->>EventBus: hotel_cargado
    CtrlHotel->>EventBus: habitaciones_cargadas

    Usuario->>EventBus: Selecciona habitación
    EventBus->>CtrlPrecios: habitacion_changed
    CtrlPrecios->>CtrlPrecios: calcular_precio()
    CtrlPrecios->>EventBus: precios_actualizados

    Usuario->>CtrlComparacion: Click "Ejecutar"
    CtrlComparacion->>CtrlValidacion: validar_todo()
    CtrlValidacion-->>CtrlComparacion: True
    CtrlComparacion->>EventBus: comparison_started
    CtrlComparacion->>CtrlComparacion: comparar_multiperiodo (async)
    CtrlComparacion->>EventBus: comparison_completed
```

---

## Resumen de Controladores

| Controlador | Eventos Escuchados | Eventos Emitidos | Propósito |
|-------------|-------------------|------------------|-----------|
| **ControladorHotel** | `hotel_changed`, `edificio_changed` | `hotel_cargado`, `habitaciones_cargadas` | Cargar datos de Excel |
| **ControladorValidacion** | - | - | Validar formulario |
| **ControladorComparacion** | - | `comparison_started`, `comparison_completed`, `comparison_error` | Ejecutar comparación async |
| **ControladorPrecios** | `habitacion_unificada_changed` | `precios_actualizados` | Calcular precio dinámico |

---

Ver también:
- [../desarrollo/convenciones.md#pattern-controlador](../desarrollo/convenciones.md#pattern-controlador) - Pattern completo
- [../arquitectura/event-driven-mvc.md](../arquitectura/event-driven-mvc.md) - Arquitectura event-driven
- [../arquitectura/flujos-principales.md](../arquitectura/flujos-principales.md) - Flujos que usan controladores