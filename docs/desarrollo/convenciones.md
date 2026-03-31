# Convenciones de Código

Este documento define las convenciones de código del proyecto **Crawl-Compare**. Seguir estas convenciones es crítico para mantener consistencia y facilitar el mantenimiento.

## Tabla de Contenidos

- [Nombres en Español](#nombres-en-español)
- [Pattern BaseComponent](#pattern-basecomponent)
- [Pattern Controlador](#pattern-controlador)
- [Pattern Modelos Pydantic](#pattern-modelos-pydantic)
- [Commits Conventional](#commits-conventional)
- [Resumen de Convenciones](#resumen-de-convenciones)

---

## Nombres en Español

El proyecto usa **español consistentemente** en todos los nombres de archivos, clases, variables y funciones.

### Archivos

| ✅ Correcto | ❌ Incorrecto |
|-------------|---------------|
| `controlador_hotel.py` | `hotel_controller.py` |
| `formulario_reserva.py` | `reservation_form.py` |
| `vista_resultados.py` | `results_view.py` |
| `periodos_panel.py` | `periods_panel.py` |
| `entrada_etiquetada.py` | `labeled_entry.py` |

**Excepción permitida**: `date_input.py` (legacy, se mantiene por compatibilidad)

### Clases

| ✅ Correcto | ❌ Incorrecto |
|-------------|---------------|
| `ControladorHotel` | `HotelController` |
| `FormularioReserva` | `ReservationForm` |
| `VistaResultados` | `ResultsView` |
| `PeriodosPanel` | `PeriodsPanel` |
| `EntradaEtiquetada` | `LabeledEntry` |

**Pattern de nombres de clases**:
- **Controladores**: `Controlador` + Sustantivo
- **Vistas/Componentes**: Sustantivo + `Panel/Widget/Vista/Formulario`
- **Modelos**: Sustantivo + `Excel/Web` (para distinguir fuentes)

### Variables y Funciones

| ✅ Correcto | ❌ Incorrecto |
|-------------|---------------|
| `estado_app` | `app_state` |
| `event_bus` | `eventBus` |
| `fecha_entrada_completa` | `full_entry_date` |
| `cargar_hoteles()` | `loadHotels()` |
| `actualizar_periodos()` | `updatePeriods()` |

**Regla**: snake_case en español para variables y funciones

### Constantes

| ✅ Correcto | ❌ Incorrecto |
|-------------|---------------|
| `LEYENDAS_AGREEMENT` | `AGREEMENT_LEGENDS` |
| `TIPOS_PERMITIDOS` | `ALLOWED_TYPES` |
| `SCRAPING_DELAY_SECONDS` | `SCRAPING_DELAY_SECONDS` ✅ (inglés aceptable para env vars) |

---

## Pattern BaseComponent

Todos los componentes UI **DEBEN** heredar de `BaseComponent` e implementar los métodos obligatorios.

### Código Completo del Pattern

```python
from UI.components.base_component import BaseComponent
import tkinter as tk
from tkinter import ttk

class MiComponente(BaseComponent):
    """
    Descripción breve del componente.

    Este componente hace X, Y, Z.
    """

    def __init__(self, parent, param1, param2=valor_default, **kwargs):
        """
        Inicializa el componente.

        Args:
            parent: Widget padre (tk.Frame, tk.Tk, etc.)
            param1: Descripción del parámetro 1
            param2: Descripción del parámetro 2 (default: valor_default)
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        # Guardar parámetros ANTES de llamar a super().__init__
        # (porque super() llama a _setup_ui() que puede necesitar estos valores)
        self.param1 = param1
        self.param2 = param2

        # Llamar a constructor de BaseComponent
        # Esto automáticamente llama a _setup_ui() y _bind_events()
        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """
        Construye la interfaz del componente.

        OBLIGATORIO implementar.
        Se llama automáticamente desde __init__ de BaseComponent.
        """
        # Crear widgets
        self._label = tk.Label(self, text=self.param1)
        self._label.grid(row=0, column=0)

        self._entry = ttk.Entry(self)
        self._entry.grid(row=1, column=0)

        # Guardar valor interno
        self._value = None

    def _bind_events(self):
        """
        Conecta eventos internos del componente.

        OPCIONAL implementar.
        Se llama automáticamente después de _setup_ui().
        """
        # Ejemplo: detectar cambios en el entry
        self._entry.bind('<KeyRelease>', self._on_change)

    def _on_change(self, event):
        """Handler privado de eventos internos."""
        self._value = self._entry.get()
        # Emitir evento externo si es necesario
        if hasattr(self, '_callback') and self._callback:
            self._callback(self._value)

    def get_value(self):
        """
        Obtiene el valor actual del componente.

        OBLIGATORIO implementar.

        Returns:
            El valor actual (tipo depende del componente)
        """
        return self._entry.get()

    def set_value(self, value):
        """
        Establece el valor del componente.

        OBLIGATORIO implementar.

        Args:
            value: Valor a establecer
        """
        self._entry.delete(0, tk.END)
        self._entry.insert(0, str(value))
        self._value = value

    def reset(self):
        """
        Resetea el componente a su estado inicial.

        OPCIONAL implementar.
        Si no se implementa, BaseComponent provee implementación vacía.
        """
        self._entry.delete(0, tk.END)
        self._value = None

    # Métodos públicos adicionales (opcional)
    def on_change(self, callback):
        """
        Registra un callback para cambios de valor.

        Args:
            callback: Función a llamar cuando cambia el valor
        """
        self._callback = callback
```

### Checklist de Implementación

Al crear un nuevo componente, verificar:

- [ ] ✅ Hereda de `BaseComponent`
- [ ] ✅ Implementa `_setup_ui()` - Construye interfaz
- [ ] ✅ Implementa `get_value()` - Retorna valor
- [ ] ✅ Implementa `set_value(value)` - Establece valor
- [ ] ⚠️ Implementa `reset()` - Opcional pero recomendado
- [ ] ⚠️ Implementa `_bind_events()` - Opcional si tiene eventos
- [ ] ✅ Tiene docstrings en clase y métodos públicos
- [ ] ✅ Llama a `super().__init__(parent, **kwargs)` al final del `__init__`

### Ejemplo Real: DateInputWidget

```python
class DateInputWidget(BaseComponent):
    """Widget para entrada de fecha con validación DD-MM-AAAA."""

    def __init__(self, parent, label_text="Fecha", fonts=None, **kwargs):
        self.label_text = label_text
        self.fonts = fonts or FontManager(parent)

        # Variables de fecha
        self.dia_var = tk.StringVar()
        self.mes_var = tk.StringVar()
        self.ano_var = tk.StringVar()
        self.fecha_completa_var = tk.StringVar()

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        # Label superior
        label = tk.Label(self, text=self.label_text, font=self.fonts.normal)
        label.grid(row=0, column=0, sticky='w')

        # Frame para inputs
        inputs_frame = tk.Frame(self)
        inputs_frame.grid(row=1, column=0)

        # Entry día (2 chars)
        self.dia_entry = ttk.Entry(inputs_frame, textvariable=self.dia_var, width=3)
        self.dia_entry.grid(row=0, column=0)

        # Entry mes (2 chars)
        self.mes_entry = ttk.Entry(inputs_frame, textvariable=self.mes_var, width=3)
        self.mes_entry.grid(row=0, column=2)

        # Entry año (4 chars)
        self.ano_entry = ttk.Entry(inputs_frame, textvariable=self.ano_var, width=5)
        self.ano_entry.grid(row=0, column=4)

        # Campo completo (readonly)
        self.fecha_entry = ttk.Entry(self, textvariable=self.fecha_completa_var, state='readonly')
        self.fecha_entry.grid(row=2, column=0)

    def _bind_events(self):
        # Validación en tiempo real
        self.dia_var.trace_add('write', self._update_fecha_completa)
        self.mes_var.trace_add('write', self._update_fecha_completa)
        self.ano_var.trace_add('write', self._update_fecha_completa)

    def get_value(self):
        return self.fecha_completa_var.get()

    def set_value(self, fecha_str):
        # "15-02-2026" → día=15, mes=02, año=2026
        parts = fecha_str.split('-')
        if len(parts) == 3:
            self.dia_var.set(parts[0])
            self.mes_var.set(parts[1])
            self.ano_var.set(parts[2])

    def reset(self):
        self.dia_var.set("")
        self.mes_var.set("")
        self.ano_var.set("")
```

---

## Pattern Controlador

Los controladores UI **DEBEN** recibir `estado_app` y `event_bus` en el constructor y usar eventos para comunicarse.

### Código Completo del Pattern

```python
class MiControlador:
    """
    Descripción breve del controlador.

    Responsabilidades:
    - Responsabilidad 1
    - Responsabilidad 2
    - Responsabilidad 3
    """

    def __init__(self, estado_app, event_bus):
        """
        Inicializa el controlador.

        Args:
            estado_app: AppState - Estado centralizado de la aplicación
            event_bus: EventBus - Sistema de eventos pub/sub
        """
        self.estado_app = estado_app
        self.event_bus = event_bus

        # Suscribirse a eventos relevantes
        self.event_bus.on('evento_entrada_1', self.handler_1)
        self.event_bus.on('evento_entrada_2', self.handler_2)

    def handler_1(self, data):
        """
        Maneja evento_entrada_1.

        Args:
            data: Datos del evento (puede ser None, str, dict, etc.)
        """
        # Procesar datos
        resultado = self._procesar(data)

        # Actualizar estado si es necesario
        self.estado_app.variable.set(resultado)

        # Emitir evento de salida
        self.event_bus.emit('evento_salida_1', resultado)

    def handler_2(self, data):
        """Maneja evento_entrada_2."""
        # ...
        pass

    def _procesar(self, data):
        """Método privado de procesamiento."""
        # Lógica de negocio
        return data_procesada

    # Métodos públicos para uso directo desde UI (opcional)
    def metodo_publico(self):
        """Método público que puede ser llamado directamente."""
        # ...
        pass
```

### Checklist de Implementación

Al crear un nuevo controlador, verificar:

- [ ] ✅ Constructor recibe `estado_app` y `event_bus`
- [ ] ✅ Se suscribe a eventos relevantes en `__init__`
- [ ] ✅ Handlers de eventos tienen firma `handler(self, data)`
- [ ] ✅ Emite eventos de salida cuando corresponde
- [ ] ✅ Usa `event_bus.emit(evento, data)` para emitir
- [ ] ✅ Usa `event_bus.on(evento, callback)` para suscribirse
- [ ] ✅ NO importa módulos de Tkinter (mantener desacoplado)
- [ ] ✅ Tiene docstrings en clase y métodos públicos

### Ejemplo Real: ControladorHotel

```python
class ControladorHotel:
    """
    Controlador para gestión de hoteles y habitaciones.

    Responsabilidades:
    - Cargar hoteles desde Excel
    - Cargar edificios según hotel seleccionado
    - Cargar habitaciones según hotel/edificio
    - Agrupar habitaciones por periodos
    """

    def __init__(self, estado_app, event_bus):
        self.estado_app = estado_app
        self.event_bus = event_bus

        # Suscribirse a eventos
        self.event_bus.on('hotel_changed', self.on_hotel_changed)
        self.event_bus.on('edificio_changed', self.on_edificio_changed)

    def cargar_hoteles(self):
        """
        Carga la lista de hoteles desde el estado.

        Returns:
            list[str]: Nombres de hoteles sin sufijo "(A)"
        """
        hoteles = self.estado_app.hoteles_excel
        nombres = [h.nombre.replace(" (A)", "").strip() for h in hoteles]
        return list(set(nombres))  # Sin duplicados

    def cargar_edificios(self, hotel_nombre):
        """
        Carga edificios de un hotel.

        Args:
            hotel_nombre: Nombre del hotel

        Returns:
            list[str]: Nombres únicos de edificios/tipos
        """
        # Buscar hotel en estado
        hotel = next((h for h in self.estado_app.hoteles_excel
                     if hotel_nombre in h.nombre), None)

        if not hotel or not hotel.tipos:
            return []

        # Extraer nombres únicos
        return list(set([t.nombre for t in hotel.tipos]))

    def cargar_habitaciones(self, hotel_nombre, edificio_nombre=None):
        """
        Carga habitaciones unificadas.

        Args:
            hotel_nombre: Nombre del hotel
            edificio_nombre: Nombre del edificio (opcional)

        Returns:
            list[str]: Nombres de habitaciones unificadas (sin duplicados)
        """
        # Implementación...
        pass

    def on_hotel_changed(self, hotel_nombre):
        """
        Handler cuando cambia la selección de hotel.

        Args:
            hotel_nombre: Nombre del hotel seleccionado
        """
        # Buscar hotel en estado
        hotel = next((h for h in self.estado_app.hoteles_excel
                     if hotel_nombre in h.nombre), None)

        if not hotel:
            return

        # Determinar si tiene tipos
        tiene_tipos = bool(hotel.tipos)

        # Emitir evento con datos del hotel
        self.event_bus.emit('hotel_cargado', {
            'hotel': hotel,
            'tiene_tipos': tiene_tipos
        })

        # Si no tiene tipos, cargar habitaciones directas
        if not tiene_tipos:
            habitaciones = self.cargar_habitaciones(hotel_nombre)
            self.event_bus.emit('habitaciones_cargadas', habitaciones)

    def on_edificio_changed(self, edificio_nombre):
        """Handler cuando cambia la selección de edificio."""
        hotel_nombre = self.estado_app.hotel.get()
        habitaciones = self.cargar_habitaciones(hotel_nombre, edificio_nombre)
        self.event_bus.emit('habitaciones_cargadas', habitaciones)
```

### Tabla de Eventos Comunes

| Evento | Emitido Por | Escuchado Por | Data |
|--------|-------------|---------------|------|
| `hotel_changed` | AppState (trace) | ControladorHotel | `str` (nombre hotel) |
| `edificio_changed` | AppState (trace) | ControladorHotel | `str` (nombre edificio) |
| `habitacion_changed` | AppState (trace) | ControladorPrecios | `str` (nombre habitación) |
| `comparison_started` | ControladorComparacion | InterfazApp | `None` |
| `comparison_completed` | ControladorComparacion | InterfazApp | `ResultadoComparacionMultiperiodo` |
| `comparison_error` | ControladorComparacion | InterfazApp | `str` (mensaje error) |
| `hotel_cargado` | ControladorHotel | InterfazApp | `dict` `{hotel, tiene_tipos}` |
| `habitaciones_cargadas` | ControladorHotel | InterfazApp | `list[str]` (nombres) |
| `precios_actualizados` | ControladorPrecios | InterfazApp | `dict` `{tipo, ...}` |

---

## Pattern Modelos Pydantic

Los modelos usan Pydantic v2 para validación de datos.

### Código Completo del Pattern

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import date

class MiModelo(BaseModel):
    """
    Descripción breve del modelo.

    Representa X con Y campos.
    """

    # Campos obligatorios
    nombre: str
    precio: float

    # Campos opcionales
    descripcion: Optional[str] = None

    # Campos con default
    activo: bool = True

    # Campos con default_factory (para mutables)
    tags: List[str] = Field(default_factory=list)

    # Campos auto-calculados (no en __init__)
    id: int = Field(init=False)

    # Validadores de campo
    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, v):
        """Limpia el nombre antes de asignar."""
        return str(v).strip().lower()

    @field_validator("precio")
    @classmethod
    def validar_precio(cls, v):
        """Valida que el precio sea positivo."""
        if v < 0:
            raise ValueError("Precio debe ser >= 0")
        return v

    # Validador de modelo (después de todos los campos)
    @model_validator(mode="after")
    def validar_coherencia(self):
        """Valida coherencia entre campos."""
        if self.activo and self.precio == 0:
            raise ValueError("Producto activo debe tener precio > 0")
        return self

    # Métodos de conveniencia
    def __str__(self):
        return f"{self.nombre} - ${self.precio:.2f}"
```

### Checklist de Implementación

- [ ] ✅ Hereda de `BaseModel`
- [ ] ✅ Usa type hints en todos los campos
- [ ] ✅ Usa `Optional[T]` para campos opcionales
- [ ] ✅ Usa `Field(default_factory=...)` para valores mutables (list, dict, set)
- [ ] ✅ Usa `Field(init=False)` para campos auto-calculados
- [ ] ✅ Usa `@field_validator` para validación por campo
- [ ] ✅ Usa `@model_validator(mode="after")` para validación global
- [ ] ✅ Tiene docstrings en clase y métodos públicos

### Ejemplo Real: HabitacionExcel

```python
class HabitacionExcel(BaseModel):
    """Habitación extraída de Excel con precio y periodos."""

    nombre: str
    precio: Optional[Union[float, str]] = None  # Número o leyenda
    precio_string: Optional[str] = None
    row_idx: int
    periodo_ids: set[int] = Field(default_factory=set)

    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, v):
        return str(v).strip().lower()

    @field_validator("precio", mode="before")
    @classmethod
    def procesar_precio(cls, v):
        # Validar números o leyendas especiales
        if v in ["closing agreement", "on request"]:
            return v

        # Normalizar precio numérico
        valor = normalizar_precio_str(v)
        if valor is None:
            raise ValueError(f"Precio inválido: '{v}'")
        return valor

    @model_validator(mode="after")
    def validar_coherencia(self):
        # Si precio es leyenda, guardar en precio_string
        if isinstance(self.precio, str):
            self.precio_string = self.precio
            self.precio = None
        return self

    def precio_para_periodo(self, periodo_id: int) -> Optional[Union[float, str]]:
        """Retorna precio si el periodo es aplicable."""
        if periodo_id in self.periodo_ids:
            return self.precio or self.precio_string
        return None
```

---

## Componentes UI — Reglas de Uso

### Visibilidad dinámica: mostrar() / ocultar()

Si un componente puede aparecer y desaparecer en runtime **sin ocupar espacio** cuando está oculto, debe encapsular su propia lógica de grid:

- Recibe `grid_kwargs: dict` en el constructor y lo guarda en `self._grid_kwargs`
- Expone `mostrar()` → llama `self.grid(**self._grid_kwargs)`
- Expone `ocultar()` → llama `self.grid_forget()`
- **No** llamar `.grid()` en el constructor: el componente arranca sin slot registrado

```python
# ✅ Correcto — el componente encapsula su posición
class MiPanel(ctk.CTkFrame):
    def __init__(self, master, grid_kwargs: dict | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self._grid_kwargs = grid_kwargs or {}

    def mostrar(self):
        self.grid(**self._grid_kwargs)

    def ocultar(self):
        self.grid_forget()

# En la interfaz:
self.panel = MiPanel(
    parent,
    grid_kwargs={"row": 0, "column": 0, "sticky": "ew", "pady": (0, 4)},
)
# panel arranca invisible, sin ocupar espacio
self.panel.mostrar()   # aparece ocupando su slot
self.panel.ocultar()   # desaparece, libera espacio

# ❌ Incorrecto — la interfaz maneja el grid directamente
self.panel.grid(row=0, column=0)
self.panel.grid_remove()   # no libera espacio
self.panel.grid_forget()   # pierde la config del slot
```

**Razón**: `grid_remove()` oculta el widget pero reserva el espacio del row. `grid_forget()` libera el espacio pero borra la config del slot. Al encapsular con `mostrar()`/`ocultar()` + `_grid_kwargs`, el componente maneja el ciclo completo internamente y la interfaz solo llama métodos semánticos.

> Ver gotcha técnico de `grid_remove()` en el constructor: [troubleshooting-ctk.md — Layout: grid_remove() en constructor no tiene efecto](../ui/troubleshooting-ctk.md#layout--grid_remove-en-constructor-no-tiene-efecto)

---

### Siempre usar `CTkCustomDropdown` para listas de opciones

**NUNCA** usar `ctk.CTkOptionMenu`, `ctk.CTkComboBox` ni ningún dropdown nativo de CustomTkinter.
**SIEMPRE** usar `CTkCustomDropdown` (o su wrapper `CTkLabeledComboBox` cuando se necesita label).

```python
# ✅ Correcto
from UI.components import CTkCustomDropdown

dd = CTkCustomDropdown(
    parent,
    values=["Opción 1", "Opción 2"],
    command=mi_callback,
    placeholder_text="Seleccionar...",
)
dd.pack(side="left", padx=4)

# Con label arriba
from UI.components import CTkLabeledComboBox

combo = CTkLabeledComboBox(
    parent,
    label="Hotel",
    textvariable=self.state.hotel,
)
combo.pack(fill="x")
combo.combobox.configure(command=self._on_hotel_changed)

# ❌ Incorrecto — NUNCA usar esto
ctk.CTkOptionMenu(parent, values=[...]).pack()
ctk.CTkComboBox(parent, values=[...]).pack()
```

**Razón**: `CTkCustomDropdown` es un workaround que soluciona limitaciones del nativo (ancho al 100%, clickeabilidad completa, estilo consistente con el design system del proyecto). Usar el nativo rompe la consistencia visual y funcional.

---

## Commits Conventional

El proyecto usa **Conventional Commits en español** con Co-Authored-By automático.

### Formato

```
<tipo>(<scope>): <mensaje corto>

<descripción detallada opcional>
<multilínea>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Tipos Permitidos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat: sistema de comparación multi-periodo` |
| `fix` | Corrección de bug | `fix: actualización de precio en panel derecho` |
| `style` | Cambios visuales/UI | `style: mejoras visuales en formulario de reserva` |
| `refactor` | Reestructuración de código | `refactor: separación de lógica de scraping` |
| `test` | Agregado/modificación de tests | `test: tests para extractor de periodos` |
| `docs` | Documentación | `docs: documentación de arquitectura event-driven` |
| `chore` | Tareas de mantenimiento | `chore: actualización de dependencias` |

### Reglas

- **Mensaje corto**: < 70 caracteres, sin punto final
- **Idioma**: Español
- **Scope**: Opcional, área del código (ui, core, scraper, etc.)
- **Descripción**: Opcional, separada por línea en blanco
- **Co-Authored-By**: SIEMPRE al final

### Ejemplos Reales del Proyecto

```
feat: se implemento sistema de comparación multi-periodo completo

fix: se corrije la ejecucion de la comparacion de precios. Funciona con multiperiodos.

fix: grandes arreglos de la interfaz + extraccion de periodos 100% funcional

feat - style - refactor: # Se agrega la funcionalidad relacionada a los periodos de cada habitacion
## se modifica la visual de la interfaz y se planea la proxima refactorización de la misma.
## se crean carpetas tests y docs, se armonizan los nombres de todas las carpetas, faltan los archivos
```

### Uso del Skill /commit-custom

El proyecto tiene un skill `/commit-custom` que facilita crear commits siguiendo este formato:

```bash
# Modo interactivo (recomendado)
/commit-custom

# Modo directo
/commit-custom feat "nueva funcionalidad de X"
/commit-custom fix ui "corrección de actualización de precio"
```

Ver detalles en [/.claude/skills/commit-custom.md](../../.claude/skills/commit-custom.md)

---

## Resumen de Convenciones

| Aspecto | Convención | Ejemplo ✅ | Ejemplo ❌ |
|---------|-----------|-----------|-----------|
| **Archivos** | `snake_case` español | `controlador_hotel.py` | `hotel_controller.py` |
| **Clases** | `PascalCase` español | `ControladorHotel` | `HotelController` |
| **Funciones** | `snake_case` español | `cargar_hoteles()` | `loadHotels()` |
| **Variables** | `snake_case` español | `estado_app` | `appState` |
| **Constantes** | `UPPER_SNAKE_CASE` | `TIPOS_PERMITIDOS` | `allowedTypes` |
| **Privados** | `_snake_case` | `_setup_ui()` | `setupUI()` |
| **Componentes** | Heredan `BaseComponent` | `class MiComponente(BaseComponent)` | `class MiComponente(tk.Frame)` |
| **Controladores** | Constructor `(estado_app, event_bus)` | `def __init__(self, estado_app, event_bus)` | `def __init__(self, state)` |
| **Modelos** | Heredan `BaseModel` (Pydantic) | `class HotelExcel(BaseModel)` | `class HotelExcel` |
| **Commits** | Conventional en español | `feat: nueva funcionalidad` | `Add new feature` |

---

**Herramientas de Verificación**:
- Skill `/check-conventions` - Valida automáticamente estas convenciones
- Skill `/commit-custom` - Facilita commits con formato correcto

Ver skills en [/.claude/skills/](../../.claude/skills/)