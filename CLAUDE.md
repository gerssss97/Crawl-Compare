# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ejecutar la Aplicación

```bash
# Punto de entrada principal
python app.py

# Alternativas
python UI/interfaz.py
python main.py  # Para testing
```

## Comandos Comunes

### Testing
```bash
# Ejecutar tests
python -m pytest Tests/

# Test específico del extractor
python Tests/testExtractor2.py
```

### Modo Debug
Para activar el debug del EventBus, descomentar en `UI/interfaz.py`:
```python
self.event_bus.enable_debug()
```

## Arquitectura del Proyecto

### Event-Driven MVC
La aplicación usa una arquitectura MVC con comunicación basada en eventos (EventBus).

**Flujo de datos:**
```
User Input → UI Components → EventBus → Controllers → Core Services → EventBus → UI Updates
```

### Capas Principales

#### 1. **UI Layer** - Interfaz gráfica (Tkinter)
- **state/** - Gestión de estado centralizada
  - `EventBus`: Sistema pub/sub para comunicación desacoplada entre componentes
  - `AppState`: Estado global de la aplicación (hotel, fechas, habitación, precio, etc.)

- **components/** - Componentes UI reutilizables (heredan de `BaseComponent`)
  - Todos implementan: `_setup_ui()`, `get_value()`, `set_value()`, `reset()`
  - `DateInputWidget`: Validación de fechas DD-MM-AAAA en tiempo real
  - `LabeledComboBox`: Combobox con label estandarizado
  - `PeriodosPanel`: Visualización de periodos agrupados
  - `PrecioPanel`: Display del precio de habitación
  - `EntradaEtiquetada`: Entry con label para inputs numéricos/texto

- **views/** - Vistas compuestas que agrupan componentes
  - `FormularioSeleccionHotel`: Maneja selección dinámica hotel/edificio/habitación
  - `FormularioReserva`: Fechas de entrada/salida + adultos/niños + botón ejecutar
  - `VistaResultados`: Visualización de resultados de comparación

- **controllers/** - Lógica de negocio sin dependencias de UI
  - `ControladorHotel`: Carga hoteles/edificios/habitaciones desde Excel, agrupa por periodos
  - `ControladorValidacion`: Validaciones de negocio (fechas, campos completos, orden)
  - `ControladorComparacion`: Ejecución asíncrona de comparación (scraping + matching)

- **styles/** - Gestión de estilos
  - `FontManager`: Centraliza las 9 fuentes de la aplicación

#### 2. **Core Layer** - Lógica de negocio central
- `controller.py`: Fachada de servicios (dar_hoteles_excel, comparar_habitaciones, dar_hotel_web)
  - Funciones email: `generar_texto_email_multiperiodo()`, `enviar_email_multiperiodo()`
- `gestor_datos.py`: GestorDatos - orquestador principal de datos Excel/Web
  - Parámetro `force_fresh` para bypass de caché en multi-periodo
- `comparador.py`: Algoritmos de fuzzy matching (RapidFuzz) para comparar habitaciones
- `comparador_multiperiodo.py`: Lógica de comparación multi-periodo (NUEVO)
  - Scraping secuencial con delays configurables
  - Fuzzy matching UNA VEZ (primer periodo), reutilización para periodos subsiguientes
  - Error handling robusto con continuación en caso de fallo
- `periodo_utils.py`: Utilidades para manejo de periodos

#### 3. **Models Layer** - Modelos Pydantic
- `hotelExcel.py`: HotelExcel, TipoHabitacionExcel, HabitacionExcel, PeriodoGroup
- `hotelWeb.py`: HotelWeb, HabitacionWeb, ComboPrecio
- `periodo.py`: Periodo con auto-incrementing IDs

#### 4. **Data Extraction** - Extracción de Excel
- `ExtractorDatos/extractor.py`: Extrae datos de `Data/Extracto_prueba2.xlsx`
- `ExtractorDatos/utils.py`: Utilidades de parsing de fechas y periodos

#### 5. **Web Scraping** - ScrawlingChinese
- `crawler.py`: Scraper asíncrono de precios de habitaciones
- `config.py`: Configuración del crawler
- `utils/`: Utilidades de scraping

### Sistema de Eventos (EventBus)

**Eventos principales:**
- `hotel_changed`: Cuando cambia selección de hotel
- `edificio_changed`: Cuando cambia selección de edificio
- `habitacion_changed`: Cuando cambia selección de habitación
- `comparison_started`: Al iniciar comparación
- `comparison_completed`: Al completar comparación (data: {mensaje, coincide, habitacion_web})
- `comparison_error`: Si ocurre error en comparación
- `hotel_cargado`: Cuando se carga un hotel (data: {hotel, tiene_tipos})
- `habitaciones_cargadas`: Cuando se cargan habitaciones

**Pattern:**
```python
# Emitir evento
self.event_bus.emit('event_name', data)

# Suscribirse a evento
self.event_bus.on('event_name', callback_function)
```

## Convenciones de Código

### Nombres en Español
El proyecto usa nombres de archivos y variables en español:
- `controlador_hotel.py` (no `hotel_controller.py`)
- `formulario_reserva.py` (no `reservation_form.py`)
- `estado_app` (no `app_state`)

### Patrón de Componentes
Todos los componentes UI heredan de `BaseComponent` y deben implementar:
```python
class MiComponente(BaseComponent):
    def _setup_ui(self):
        # Construir interfaz
        pass

    def get_value(self):
        # Obtener valor
        return self._value

    def set_value(self, value):
        # Establecer valor
        self._value = value

    def reset(self):
        # Resetear a estado inicial
        pass
```

### Patrón de Controladores
Los controladores reciben `estado_app` y `event_bus`:
```python
class MiControlador:
    def __init__(self, estado_app, event_bus):
        self.estado_app = estado_app
        self.event_bus = event_bus

        # Suscribirse a eventos
        self.event_bus.on('evento', self.handler)

    def handler(self, data):
        # Manejar evento
        pass
```

## Flujo de Trabajo Típico

### Agregar un Nuevo Componente
1. Crear archivo en `UI/components/mi_componente.py`
2. Heredar de `BaseComponent`
3. Implementar `_setup_ui()`, `get_value()`, `set_value()`
4. Exportar en `UI/components/__init__.py`
5. Usar en vistas o interfaz principal

### Agregar un Nuevo Controlador
1. Crear archivo en `UI/controllers/controlador_x.py`
2. Constructor recibe `estado_app` y `event_bus`
3. Suscribirse a eventos en `__init__`
4. Emitir eventos cuando corresponda
5. Exportar en `UI/controllers/__init__.py`
6. Instanciar en `InterfazApp.__init__`

### Modificar Lógica de Comparación
La comparación **multi-periodo** se ejecuta así:
1. Usuario llena formulario y presiona "Ejecutar comparación"
2. `ControladorValidacion.validar_todo()` valida campos (incluyendo precio actualizado)
3. `ControladorComparacion.ejecutar_comparacion_async()` ejecuta en thread
4. Parsea fechas y busca `habitacion_unificada` en estado
5. Llama a `comparar_multiperiodo()` que:
   - Infiere periodos aplicables desde rango de fechas
   - Loop SECUENCIAL por cada periodo:
     - Scraping con `dar_hotel_web(force_fresh=True)`
     - Fuzzy matching solo en primer periodo
     - Extrae precio web y compara con precio Excel del periodo
     - Delay de 2s entre periodos
   - Retorna `ResultadoComparacionMultiperiodo`
6. Emite `comparison_completed` con resultado (objeto, no dict)
7. `InterfazApp._on_comparison_completed()` detecta tipo de resultado:
   - Si `ResultadoComparacionMultiperiodo`: Llama `vista_resultados.mostrar_resultado_multiperiodo()`
   - Si dict (legacy): Muestra mensaje simple
8. UI muestra tabla comparativa con todos los periodos

## Datos Importantes

### Archivo de Datos
`Data/Extracto_prueba2.xlsx` - Excel con hoteles, habitaciones y periodos

### Estructura de Hotel
```
HotelExcel
├── nombre: str
├── tipos: List[TipoHabitacionExcel]  # Edificios (opcional)
│   └── habitaciones: List[HabitacionExcel]
├── habitaciones_directas: List[HabitacionExcel]  # Si no hay tipos
├── periodos_group: List[PeriodoGroup]
└── extras: List[Extra]
```

### Habitaciones con Periodos
- Cada habitación tiene `periodo_ids: set[int]`
- Los periodos se agrupan por `PeriodoGroup.nombre`
- Un edificio/habitación puede tener múltiples periodos
- Los periodos se muestran en `PeriodosPanel` agrupados

### Validación de Fechas
- Formato: DD-MM-AAAA
- Fecha entrada debe ser >= hoy
- Fecha salida debe ser > fecha entrada
- Validación inline en `DateInputWidget`
- Validación de negocio en `ControladorValidacion`

## Compatibilidad con Código Legacy

Algunos métodos se mantienen por compatibilidad:
- `ejecutar_comparacion()` en `interfaz.py` (DEPRECATED - usa `ControladorComparacion`)
- `run_async()` en `interfaz.py` (DEPRECATED)
- Acceso directo a widgets: `self.resultado`, `self.periodos_text` (para código que accede directamente)

Al modificar código legacy, preferir migrar a la nueva arquitectura usando controladores y componentes.

## Sistema Multi-Periodo (Nuevo)

### Características Principales
- **Scraping secuencial**: Un request por periodo con delays de 2s (configurable vía `SCRAPING_DELAY_SECONDS`)
- **Fuzzy matching optimizado**: Se ejecuta UNA VEZ en el primer periodo, luego reutiliza resultado
- **Cache bypass**: Parámetro `force_fresh=True` evita contaminación de caché
- **Error handling robusto**: Si un periodo falla, continúa con los demás
- **UI tabla comparativa**: Muestra todos los periodos con estado ✅ OK / ❌ DIFF
- **Email automático**: Envía breakdown completo si hay discrepancias en CUALQUIER periodo

### Estructura de Resultado
```python
ResultadoComparacionMultiperiodo:
    habitacion_excel_nombre: str
    habitacion_web_matcheada: HabitacionWeb
    periodos: List[ResultadoPeriodo]
        - periodo: Periodo
        - precio_excel: float | str
        - precio_web: float
        - diferencia: float
        - coincide: bool
    tiene_discrepancias: bool
    mensaje_match: str
```

### Configuración
Variables de entorno en `.env`:
```env
GROQ_API_KEY=gsk_...               # Requerido para scraping
GMTP_KEY=...                       # Opcional, para envío de emails
SCRAPING_DELAY_SECONDS=2           # Delay entre periodos (default: 2s)
```

### Archivos Clave
- `Core/comparador_multiperiodo.py`: Lógica principal (230 líneas)
- `UI/views/vista_resultados.py`: Método `mostrar_resultado_multiperiodo()`
- `UI/interfaz.py`: Handler `_on_comparison_completed()` con detección de tipo
- Documentación completa: `CHECKPOINT_MULTIPERIODO.md`

## Debugging

### EventBus Debug
Activar para ver todos los eventos emitidos:
```python
self.event_bus.enable_debug()
```

### Print Debugging
El código tiene varios `print()` para debugging:
- `Core/comparador.py`: Muestra scores de fuzzy matching
- `Core/comparador_multiperiodo.py`: Muestra progreso detallado de cada periodo
- `ExtractorDatos/utils.py`: Muestra parsing de fechas
- `UI/interfaz.py`: Muestra cambios de hotel/habitación

### Estado de la Aplicación
El estado completo está en `InterfazApp.state` (AppState):
```python
self.state.hotel.get()  # Hotel actual
self.state.habitacion.get()  # Habitación actual
self.state.hoteles_excel  # Lista de HotelExcel
self.state.habitaciones_excel  # Habitaciones del hotel actual
self.state.resultado_multiperiodo  # ResultadoComparacionMultiperiodo (último)
```

## Testing

La aplicación ejecuta `testExtractor2.py` al iniciar para generar el archivo de validación.

Para testear sin ejecutar el extractor:
```python
python -c "from UI.interfaz import InterfazApp; import tkinter as tk; root = tk.Tk(); app = InterfazApp(root); root.mainloop()"
```

## Performance

- La comparación se ejecuta en background thread (daemon) para no bloquear UI
- El scraping es asíncrono usando aiohttp
- Fuzzy matching usa RapidFuzz (optimizado en C)

## Notas de Seguridad

- Email credentials están en variables de entorno
- No hacer commit de `Data/` con información sensible
- El scraping debe respetar robots.txt y rate limits
