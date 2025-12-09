# Plan de Reestructuración y Componentización de la Interfaz

## Análisis de Situación Actual

### Estado Actual del Código
- **Archivo principal**: `UI/interfaz.py` (784 líneas)
- **Clase monolítica**: `InterfazApp` con 20+ métodos
- **Componentes de interacción**: 18 widgets
- **Estilos de fuente**: 9 tipos diferentes
- **Variables de estado**: 15+ StringVar/IntVar
- **Nivel de componentización**: BAJO

### Problemas Identificados

1. **Falta de Separación de Responsabilidades**
   - Validación, UI, lógica de negocio y eventos mezclados
   - Método `__init__` con más de 100 líneas
   - Métodos que hacen múltiples cosas

2. **Código Duplicado**
   - Widgets de fecha entrada/salida (líneas 256-287 y 296-326)
   - Lógica de validación repetida
   - Construcción de frames similar

3. **Gestión de Estado Desorganizada**
   - 15+ variables de control dispersas
   - No hay un punto central de verdad
   - Difícil rastrear cambios de estado

4. **Widgets Dinámicos Manuales**
   - Lista `widgets_dinamicos` para tracking
   - Creación/destrucción manual de widgets
   - Lógica de grid layout dispersa

---

## Arquitectura Propuesta

### Patrón MVC Adaptado para Tkinter

```
┌─────────────────────────────────────────────────────────┐
│                    InterfazApp                          │
│              (Main Controller/Coordinator)              │
│  - Inicialización de la aplicación                     │
│  - Orquestación de vistas y controladores               │
│  - Gestión del ciclo de vida                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼─────────┐      ┌────────▼──────────┐
│   VIEWS LAYER   │      │ CONTROLLERS LAYER │
│─────────────────│      │───────────────────│
│                 │      │                   │
│ - Forms         │◄─────│ - HotelController │
│ - Panels        │      │ - FormController  │
│ - Modals        │      │ - ValidationCtrl  │
│                 │      │                   │
└────────┬────────┘      └───────────────────┘
         │
┌────────▼─────────────┐
│   COMPONENTS LAYER   │
│──────────────────────│
│                      │
│ - DateInputWidget    │
│ - LabeledComboBox    │
│ - PeriodosPanel      │
│ - PrecioPanel        │
│ - ResultsView        │
│                      │
└──────────────────────┘
         │
┌────────▼─────────────┐
│    STATE LAYER       │
│──────────────────────│
│                      │
│ - AppState           │
│ - EventBus           │
│                      │
└──────────────────────┘
```

### Capas de la Arquitectura

#### 1. **Components Layer** (Capa de Componentes)
Widgets reutilizables, autocontenidos, sin lógica de negocio.

**Responsabilidades:**
- Renderizar UI
- Manejar interacciones locales
- Emitir eventos para comunicación
- Validación de formato (no de negocio)

**Componentes identificados:**
- `DateInputWidget`: Input de fecha con validación
- `LabeledComboBox`: Combobox con label superior
- `LabeledEntry`: Entry con label superior
- `PeriodosPanel`: Panel de visualización de periodos
- `PrecioPanel`: Panel de visualización de precio
- `ScrollableText`: Text widget con scrollbar

#### 2. **Views Layer** (Capa de Vistas)
Agrupaciones lógicas de componentes que forman secciones completas.

**Responsabilidades:**
- Componer componentes
- Gestionar layout de secciones
- Proporcionar interfaz de acceso a datos

**Vistas identificadas:**
- `HotelSelectionForm`: Hotel + Edificio + Habitación
- `ReservationForm`: Fechas + Adultos + Niños
- `ResultsView`: Visualización de resultados de comparación
- `EmailView`: Modal de envío de email

#### 3. **Controllers Layer** (Capa de Controladores)
Lógica de negocio, orquestación de datos, manejo de eventos.

**Responsabilidades:**
- Cargar datos desde fuentes externas
- Validación de reglas de negocio
- Coordinación entre vistas
- Manejo de eventos complejos

**Controladores identificados:**
- `HotelController`: Carga de hoteles, edificios, habitaciones
- `ValidationController`: Validaciones de negocio
- `ComparisonController`: Ejecución de comparación y scraping
- `EmailController`: Generación y envío de emails

#### 4. **State Layer** (Capa de Estado)
Gestión centralizada del estado de la aplicación.

**Responsabilidades:**
- Almacenar estado de la aplicación
- Notificar cambios (Observer pattern)
- Proporcionar acceso controlado al estado

**Componentes de estado:**
- `AppState`: Estado global de la aplicación
- `EventBus`: Sistema de eventos pub/sub

---

## Patrones de Diseño Aplicables

### 1. **Component Pattern** (Composición)

```python
class BaseComponent(ttk.Frame):
    """Clase base para todos los componentes reutilizables"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Override: Construir widgets internos"""
        raise NotImplementedError

    def _bind_events(self):
        """Override: Conectar eventos internos"""
        pass

    def get_value(self):
        """Override: Obtener valor del componente"""
        raise NotImplementedError

    def set_value(self, value):
        """Override: Establecer valor del componente"""
        raise NotImplementedError

    def reset(self):
        """Override: Resetear componente a estado inicial"""
        pass
```

**Ventajas:**
- Reutilización de código
- Testeable de forma aislada
- Encapsulación de comportamiento
- Fácil mantenimiento

### 2. **Observer Pattern** (Eventos)

```python
class EventBus:
    """Sistema centralizado de eventos pub/sub"""

    def __init__(self):
        self._listeners = {}

    def on(self, event_name, callback):
        """Suscribirse a un evento"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def off(self, event_name, callback):
        """Desuscribirse de un evento"""
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)

    def emit(self, event_name, data=None):
        """Emitir un evento con datos opcionales"""
        for callback in self._listeners.get(event_name, []):
            callback(data)
```

**Eventos identificados:**
- `hotel_changed`: Cuando cambia la selección de hotel
- `edificio_changed`: Cuando cambia la selección de edificio
- `habitacion_changed`: Cuando cambia la selección de habitación
- `comparison_started`: Cuando inicia la comparación
- `comparison_completed`: Cuando finaliza la comparación
- `comparison_error`: Cuando hay error en la comparación

**Ventajas:**
- Desacoplamiento de componentes
- Escalabilidad
- Fácil debugging
- Múltiples listeners por evento

### 3. **State Management Pattern**

```python
class AppState:
    """Estado centralizado de la aplicación"""

    def __init__(self, event_bus):
        self._event_bus = event_bus

        # Variables de estado
        self.hotel = tk.StringVar()
        self.edificio = tk.StringVar()
        self.habitacion = tk.StringVar()
        self.fecha_entrada = tk.StringVar()
        self.fecha_salida = tk.StringVar()
        self.adultos = tk.IntVar(value=1)
        self.ninos = tk.IntVar(value=0)
        self.precio = tk.StringVar()

        # Datos cargados
        self.hoteles_excel = []
        self.habitaciones_excel = []
        self.habitacion_web = None

        # Conectar traces para emitir eventos
        self._setup_traces()

    def _setup_traces(self):
        """Configurar traces para emitir eventos cuando cambia el estado"""
        self.hotel.trace_add('write', lambda *args:
            self._event_bus.emit('hotel_changed', self.hotel.get()))
        self.edificio.trace_add('write', lambda *args:
            self._event_bus.emit('edificio_changed', self.edificio.get()))
        self.habitacion.trace_add('write', lambda *args:
            self._event_bus.emit('habitacion_changed', self.habitacion.get()))

    def reset_edificio(self):
        """Resetear selección de edificio"""
        self.edificio.set("")

    def reset_habitacion(self):
        """Resetear selección de habitación"""
        self.habitacion.set("")
        self.precio.set("")
```

**Ventajas:**
- Único punto de verdad
- Fácil sincronización
- Debugging simplificado
- Testing facilitado

### 4. **Factory Pattern** (Creación de Componentes)

```python
class ComponentFactory:
    """Factory para crear componentes estandarizados"""

    @staticmethod
    def create_labeled_combobox(parent, label_text, textvariable,
                                state="readonly", **kwargs):
        """Crea un combobox con label estandarizado"""
        return LabeledComboBox(
            parent,
            label_text=label_text,
            textvariable=textvariable,
            state=state,
            **kwargs
        )

    @staticmethod
    def create_date_input(parent, label_text, **kwargs):
        """Crea un widget de fecha estandarizado"""
        return DateInputWidget(
            parent,
            label_text=label_text,
            **kwargs
        )
```

**Ventajas:**
- Consistencia visual
- Configuración centralizada
- Fácil cambio de estilos globales

### 5. **Strategy Pattern** (Validaciones)

```python
class ValidationStrategy:
    """Estrategia base de validación"""

    def validate(self, value):
        raise NotImplementedError

    def get_error_message(self):
        raise NotImplementedError

class DateRangeValidation(ValidationStrategy):
    """Validación de rango de fechas"""

    def validate(self, fecha_entrada, fecha_salida):
        try:
            entrada = datetime.strptime(fecha_entrada, "%d-%m-%Y")
            salida = datetime.strptime(fecha_salida, "%d-%m-%Y")
            return salida > entrada
        except ValueError:
            return False

    def get_error_message(self):
        return "La fecha de salida debe ser posterior a la de entrada"

class FutureDateValidation(ValidationStrategy):
    """Validación de fecha futura"""

    def validate(self, fecha):
        try:
            fecha_dt = datetime.strptime(fecha, "%d-%m-%Y")
            return fecha_dt >= datetime.now()
        except ValueError:
            return False

    def get_error_message(self):
        return "La fecha debe ser mayor o igual a la actual"
```

**Ventajas:**
- Validaciones reutilizables
- Fácil agregar nuevas validaciones
- Testing individual
- Separación de concerns

---

## Plan de Implementación

### Estructura de Archivos Propuesta

```
UI/
├── interfaz.py                    # Main app (refactorizada)
├── components/
│   ├── __init__.py
│   ├── base_component.py          # Clase base de componentes
│   ├── date_input.py              # DateInputWidget
│   ├── labeled_combobox.py        # LabeledComboBox
│   ├── labeled_entry.py           # LabeledEntry
│   ├── periodos_panel.py          # PeriodosPanel
│   ├── precio_panel.py            # PrecioPanel
│   └── scrollable_text.py         # ScrollableText
├── views/
│   ├── __init__.py
│   ├── hotel_selection_form.py    # Formulario de selección
│   ├── reservation_form.py        # Formulario de reserva
│   ├── results_view.py            # Vista de resultados
│   └── email_view.py              # Modal de email
├── controllers/
│   ├── __init__.py
│   ├── hotel_controller.py        # Lógica de hoteles
│   ├── validation_controller.py   # Validaciones
│   ├── comparison_controller.py   # Comparación
│   └── email_controller.py        # Emails
├── state/
│   ├── __init__.py
│   ├── app_state.py               # Estado de la aplicación
│   └── event_bus.py               # Sistema de eventos
├── validators/
│   ├── __init__.py
│   ├── base_validator.py          # Clase base
│   ├── date_validators.py         # Validadores de fecha
│   └── form_validators.py         # Validadores de formulario
└── styles/
    ├── __init__.py
    └── fonts.py                   # Configuración de fuentes
```

### Fases de Implementación

---

## FASE 1: Infraestructura Base (1-2 días)

### Objetivo
Crear la infraestructura fundamental sin romper funcionalidad existente.

### Tareas

#### 1.1 Crear EventBus
**Archivo**: `UI/state/event_bus.py`

```python
class EventBus:
    """Sistema de eventos pub/sub para comunicación entre componentes"""

    def __init__(self):
        self._listeners = {}
        self._debug = False

    def on(self, event_name, callback):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def off(self, event_name, callback):
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)

    def emit(self, event_name, data=None):
        if self._debug:
            print(f"[EventBus] Emitiendo: {event_name} con data: {data}")

        for callback in self._listeners.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                print(f"[EventBus] Error en listener de {event_name}: {e}")

    def enable_debug(self):
        self._debug = True
```

**Prueba inicial**: Agregar en `interfaz.py`:
```python
from UI.state.event_bus import EventBus

# En __init__
self.event_bus = EventBus()
self.event_bus.enable_debug()

# Probar con un evento existente
self.event_bus.on('hotel_changed', lambda data: print(f"Hotel cambió a: {data}"))
self.event_bus.emit('hotel_changed', self.seleccion_hotel.get())
```

#### 1.2 Crear AppState
**Archivo**: `UI/state/app_state.py`

```python
import tkinter as tk

class AppState:
    """Estado centralizado de la aplicación"""

    def __init__(self, event_bus):
        self._event_bus = event_bus

        # Variables de selección
        self.hotel = tk.StringVar()
        self.edificio = tk.StringVar()
        self.habitacion = tk.StringVar()

        # Variables de fecha
        self.fecha_entrada_completa = tk.StringVar()
        self.fecha_salida_completa = tk.StringVar()

        # Variables de huéspedes
        self.adultos = tk.IntVar(value=1)
        self.ninos = tk.IntVar(value=0)

        # Variables de resultado
        self.precio = tk.StringVar(value="(ninguna seleccionada)")

        # Datos cargados
        self.hoteles_excel = []
        self.habitaciones_excel = []
        self.habitacion_web = None

        # Configurar traces
        self._setup_traces()

    def _setup_traces(self):
        """Configurar traces para emitir eventos"""
        self.hotel.trace_add('write', lambda *args:
            self._event_bus.emit('hotel_changed', self.hotel.get()))

        self.edificio.trace_add('write', lambda *args:
            self._event_bus.emit('edificio_changed', self.edificio.get()))

        self.habitacion.trace_add('write', lambda *args:
            self._event_bus.emit('habitacion_changed', self.habitacion.get()))

    def reset_edificio(self):
        self.edificio.set("")

    def reset_habitacion(self):
        self.habitacion.set("")
        self.precio.set("(ninguna seleccionada)")
```

**Migración en `interfaz.py`**:
```python
# Reemplazar las líneas 91-108 con:
from UI.state.app_state import AppState

# En __init__:
self.state = AppState(self.event_bus)

# Luego actualizar todas las referencias:
# self.seleccion_hotel -> self.state.hotel
# self.adultos -> self.state.adultos
# etc.
```

#### 1.3 Crear BaseComponent
**Archivo**: `UI/components/base_component.py`

```python
from tkinter import ttk

class BaseComponent(ttk.Frame):
    """Clase base para componentes reutilizables"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Override: Construir la interfaz del componente"""
        raise NotImplementedError("Subclases deben implementar _setup_ui")

    def _bind_events(self):
        """Override: Conectar eventos internos del componente"""
        pass

    def get_value(self):
        """Override: Obtener el valor actual del componente"""
        raise NotImplementedError("Subclases deben implementar get_value")

    def set_value(self, value):
        """Override: Establecer el valor del componente"""
        raise NotImplementedError("Subclases deben implementar set_value")

    def reset(self):
        """Override: Resetear el componente a su estado inicial"""
        pass

    def enable(self):
        """Habilitar el componente"""
        for child in self.winfo_children():
            try:
                child.configure(state='normal')
            except:
                pass

    def disable(self):
        """Deshabilitar el componente"""
        for child in self.winfo_children():
            try:
                child.configure(state='disabled')
            except:
                pass
```

#### 1.4 Crear Gestión de Fuentes
**Archivo**: `UI/styles/fonts.py`

```python
from tkinter import font

class FontManager:
    """Gestor centralizado de fuentes de la aplicación"""

    def __init__(self, root):
        self.normal = font.Font(family="Helvetica", size=12)
        self.negrita = font.Font(family="Helvetica", size=12, weight="bold")
        self.grande_negrita = font.Font(family="Helvetica", size=16, weight="bold")
        self.resultado = font.Font(family="Helvetica", size=12, weight="normal")
        self.periodos_titulo = font.Font(family="Helvetica", size=11, weight="bold")
        self.periodos_contenido = font.Font(family="Helvetica", size=11)
        self.precio = font.Font(family="Helvetica", size=14, weight="bold")
        self.combobox = font.Font(family="Helvetica", size=12)
        self.combo = font.Font(family="Helvetica", size=20)
        self.boton = font.Font(family="Helvetica", size=13, weight="bold")
```

**Migración en `interfaz.py`**:
```python
from UI.styles.fonts import FontManager

# Reemplazar líneas 110-119 con:
self.fonts = FontManager(self.root)

# Actualizar todas las referencias:
# self.fuente_normal -> self.fonts.normal
# self.fuente_negrita -> self.fonts.negrita
# etc.
```

**Testing Fase 1**:
- [ ] EventBus emite y recibe eventos correctamente
- [ ] AppState reemplaza las variables de estado existentes
- [ ] FontManager reemplaza las fuentes existentes
- [ ] La aplicación sigue funcionando igual que antes

---

## FASE 2: Componentes Base (2-3 días)

### Objetivo
Crear los componentes reutilizables más básicos.

### 2.1 DateInputWidget

**Archivo**: `UI/components/date_input.py`

**Funcionalidad**:
- Tres campos de entrada (DD, MM, AAAA)
- Validación en tiempo real
- Campo de solo lectura mostrando fecha completa
- Emite evento cuando la fecha es válida

**Código completo**:
```python
import tkinter as tk
from tkinter import ttk
from UI.components.base_component import BaseComponent

class DateInputWidget(BaseComponent):
    """Widget de entrada de fecha con validación (DD-MM-AAAA)"""

    def __init__(self, parent, label_text="Fecha", fonts=None, **kwargs):
        self.label_text = label_text
        self.fonts = fonts

        # Variables internas
        self._dia = tk.StringVar()
        self._mes = tk.StringVar()
        self._ano = tk.StringVar()
        self._fecha_completa = tk.StringVar()

        # Callback externo
        self._on_change_callback = None

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construir la interfaz del componente"""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Label
        font_label = self.fonts.normal if self.fonts else None
        label = tk.Label(self, text=self.label_text, bg=bg_color, font=font_label)
        label.grid(row=0, column=0, sticky='w', pady=(0, 4))

        # Frame de inputs
        input_frame = tk.Frame(self, bg=bg_color)
        input_frame.grid(row=1, column=0, sticky='ew')

        # DD
        tk.Label(input_frame, text="DD", bg=bg_color, font=font_label).grid(row=0, column=0, padx=(0,2))
        self._entry_dia = ttk.Entry(input_frame, width=3, textvariable=self._dia,
                                    validate='key', validatecommand=self._get_dia_validation())
        self._entry_dia.grid(row=0, column=1, padx=2)

        tk.Label(input_frame, text="-", bg=bg_color).grid(row=0, column=2, padx=2)

        # MM
        tk.Label(input_frame, text="MM", bg=bg_color, font=font_label).grid(row=0, column=3, padx=2)
        self._entry_mes = ttk.Entry(input_frame, width=3, textvariable=self._mes,
                                    validate='key', validatecommand=self._get_mes_validation())
        self._entry_mes.grid(row=0, column=4, padx=2)

        tk.Label(input_frame, text="-", bg=bg_color).grid(row=0, column=5, padx=2)

        # AAAA
        tk.Label(input_frame, text="AAAA", bg=bg_color, font=font_label).grid(row=0, column=6, padx=2)
        self._entry_ano = ttk.Entry(input_frame, width=5, textvariable=self._ano,
                                   validate='key', validatecommand=self._get_ano_validation())
        self._entry_ano.grid(row=0, column=7, padx=2)

        # Entry completa (readonly)
        self._entry_completa = ttk.Entry(input_frame, textvariable=self._fecha_completa,
                                        state='readonly', width=12)
        self._entry_completa.grid(row=0, column=8, padx=(10,0))

    def _bind_events(self):
        """Conectar eventos de trace"""
        self._dia.trace_add("write", self._actualizar_fecha_completa)
        self._mes.trace_add("write", self._actualizar_fecha_completa)
        self._ano.trace_add("write", self._actualizar_fecha_completa)

    def _get_dia_validation(self):
        """Comando de validación para día"""
        return (self.register(self._validar_dia), "%P")

    def _get_mes_validation(self):
        """Comando de validación para mes"""
        return (self.register(self._validar_mes), "%P")

    def _get_ano_validation(self):
        """Comando de validación para año"""
        return (self.register(self._validar_ano), "%P")

    def _validar_dia(self, valor):
        if valor == "":
            return True
        if valor.isdigit():
            n = int(valor)
            return 1 <= n <= 31
        return False

    def _validar_mes(self, valor):
        if valor == "":
            return True
        if valor.isdigit():
            n = int(valor)
            return 1 <= n <= 12
        return False

    def _validar_ano(self, valor):
        if valor == "":
            return True
        if valor.isdigit():
            return 1 <= len(valor) <= 4
        return False

    def _actualizar_fecha_completa(self, *args):
        """Actualizar campo de fecha completa"""
        dia = self._dia.get().zfill(2)
        mes = self._mes.get().zfill(2)
        ano = self._ano.get()

        if dia and mes and ano:
            fecha = f"{dia}-{mes}-{ano}"
            self._fecha_completa.set(fecha)

            # Llamar callback si existe
            if self._on_change_callback:
                self._on_change_callback(fecha)
        else:
            self._fecha_completa.set("")

    def get_value(self):
        """Obtener fecha completa en formato DD-MM-AAAA"""
        return self._fecha_completa.get()

    def set_value(self, fecha_str):
        """Establecer fecha desde string DD-MM-AAAA"""
        if not fecha_str:
            self.reset()
            return

        try:
            partes = fecha_str.split('-')
            if len(partes) == 3:
                self._dia.set(partes[0])
                self._mes.set(partes[1])
                self._ano.set(partes[2])
        except:
            pass

    def reset(self):
        """Resetear a vacío"""
        self._dia.set("")
        self._mes.set("")
        self._ano.set("")
        self._fecha_completa.set("")

    def on_change(self, callback):
        """Registrar callback para cuando cambia la fecha"""
        self._on_change_callback = callback

    def get_fecha_completa_var(self):
        """Obtener StringVar de fecha completa para binding externo"""
        return self._fecha_completa
```

**Migración en `interfaz.py`**:

Reemplazar líneas 256-294 (fecha entrada):
```python
from UI.components.date_input import DateInputWidget

# En crear_campos_estaticos():
self.fecha_entrada_widget = DateInputWidget(
    self.principal_frame,
    label_text="Fecha de entrada (DD-MM-AAAA):",
    fonts=self.fonts
)
self.fecha_entrada_widget.grid(row=i, column=0, sticky='ew', pady=(0, 10))
self.widgets_dinamicos.append(self.fecha_entrada_widget)

# Vincular con AppState
self.state.fecha_entrada_completa = self.fecha_entrada_widget.get_fecha_completa_var()
i += 1
```

Repetir para fecha salida (reemplazar líneas 296-333).

**Testing**:
- [ ] Validación de DD (1-31)
- [ ] Validación de MM (1-12)
- [ ] Validación de AAAA (1-4 dígitos)
- [ ] Actualización automática de campo completo
- [ ] Reset funciona correctamente
- [ ] get_value() y set_value() funcionan

### 2.2 LabeledComboBox

**Archivo**: `UI/components/labeled_combobox.py`

```python
import tkinter as tk
from tkinter import ttk
from UI.components.base_component import BaseComponent

class LabeledComboBox(BaseComponent):
    """Combobox con label superior estandarizado"""

    def __init__(self, parent, label_text="", textvariable=None,
                 values=None, state="readonly", fonts=None, **kwargs):
        self.label_text = label_text
        self.textvariable = textvariable or tk.StringVar()
        self.initial_values = values or []
        self.state = state
        self.fonts = fonts
        self._on_select_callback = None

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Label
        font_label = self.fonts.negrita if self.fonts else None
        label = tk.Label(self, text=self.label_text, bg=bg_color, font=font_label)
        label.grid(row=0, column=0, sticky='w', pady=(0, 4))

        # Combobox
        style = ttk.Style()
        font_combo = self.fonts.combo if self.fonts else None
        style.configure('Custom.TCombobox', font=font_combo)

        self._combobox = ttk.Combobox(
            self,
            textvariable=self.textvariable,
            state=self.state,
            style='Custom.TCombobox'
        )
        self._combobox.grid(row=1, column=0, sticky='ew', pady=(0, 10))

        if self.initial_values:
            self._combobox['values'] = self.initial_values

        # Expandir combobox
        self.grid_columnconfigure(0, weight=1)

    def _bind_events(self):
        self._combobox.bind("<<ComboboxSelected>>", self._on_selected)

    def _on_selected(self, event):
        if self._on_select_callback:
            self._on_select_callback(self.textvariable.get())

    def get_value(self):
        return self.textvariable.get()

    def set_value(self, value):
        self.textvariable.set(value)

    def set_values(self, values):
        """Actualizar lista de opciones"""
        self._combobox['values'] = values

    def get_values(self):
        """Obtener lista de opciones actual"""
        return self._combobox['values']

    def reset(self):
        self.textvariable.set("")

    def on_select(self, callback):
        """Registrar callback para selección"""
        self._on_select_callback = callback

    def current(self):
        """Obtener índice actual seleccionado"""
        return self._combobox.current()
```

**Migración en `interfaz.py`**:

Reemplazar líneas 141-144 (hotel combobox):
```python
from UI.components.labeled_combobox import LabeledComboBox

# En __init__:
self.hotel_cb_widget = LabeledComboBox(
    self.principal_frame,
    label_text="Selección hotel:",
    textvariable=self.state.hotel,
    fonts=self.fonts
)
self.hotel_cb_widget.grid(row=1, column=0, sticky='ew', pady=(0, 10))
self.hotel_cb_widget.on_select(self.on_hotel_cambiado)
```

Repetir para edificio y habitación.

**Testing**:
- [ ] Muestra label correctamente
- [ ] Permite seleccionar valores
- [ ] Callback on_select funciona
- [ ] set_values actualiza opciones
- [ ] current() retorna índice correcto

### 2.3 PeriodosPanel

**Archivo**: `UI/components/periodos_panel.py`

```python
import tkinter as tk
from tkinter import ttk
from collections import OrderedDict
from UI.components.base_component import BaseComponent

class PeriodosPanel(BaseComponent):
    """Panel de visualización de periodos de habitación"""

    def __init__(self, parent, fonts=None, **kwargs):
        self.fonts = fonts
        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        # Label título
        font_titulo = self.fonts.negrita if self.fonts else None
        ttk.Label(self, text="Periodos de la habitación", font=font_titulo).grid(
            row=0, column=0, sticky='w', pady=(10,5), padx=(0,10)
        )

        # Frame contenedor con borde
        container = tk.Frame(self, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        container.grid(row=1, column=0, sticky='nsew', pady=(0,10), padx=(0,10))

        # Text widget
        font_contenido = self.fonts.periodos_contenido if self.fonts else None
        self._text = tk.Text(
            container,
            height=15,
            width=38,
            wrap="word",
            font=font_contenido,
            bg='#FAFAFA',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor='arrow'
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=scrollbar.set)

        # Configurar como readonly
        self._text.config(state='disabled')

        # Configurar tags
        font_titulo_periodo = self.fonts.periodos_titulo if self.fonts else None
        self._text.tag_configure("advertencia", foreground="#C0392B",
                                font=font_titulo if self.fonts else None)
        self._text.tag_configure("grupo", foreground="#34495E",
                                font=font_titulo_periodo, spacing1=6, spacing3=3)
        self._text.tag_configure("periodo", foreground="#555555",
                                font=font_contenido, lmargin1=20, lmargin2=20)

        # Configurar expansión
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def get_value(self):
        return self._text.get('1.0', tk.END)

    def set_value(self, value):
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)
        self._text.insert(tk.END, value)
        self._text.config(state='disabled')

    def actualizar_periodos(self, habitacion, hotel_excel):
        """Actualizar periodos de una habitación"""
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)

        # Verificar si hay periodos
        if not habitacion.periodo_ids:
            self._text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self._text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self._text.config(state='disabled')
            return

        # Agrupar periodos por grupo
        grupos_periodos = OrderedDict()

        for pid in habitacion.periodo_ids:
            periodo = hotel_excel.periodo_por_id(pid)
            if periodo:
                # Buscar grupo
                nombre_grupo = None
                for grupo in hotel_excel.periodos_group:
                    if periodo in grupo.periodos:
                        nombre_grupo = grupo.nombre
                        break

                if nombre_grupo:
                    if nombre_grupo not in grupos_periodos:
                        grupos_periodos[nombre_grupo] = []
                    grupos_periodos[nombre_grupo].append(periodo)

        if not grupos_periodos:
            self._text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self._text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self._text.config(state='disabled')
            return

        # Insertar con formato
        for i, (nombre_grupo, periodos) in enumerate(grupos_periodos.items()):
            if i > 0:
                self._text.insert(tk.END, "\n")

            # Nombre del grupo
            self._text.insert(tk.END, f"{nombre_grupo}\n", "grupo")

            # Periodos
            for periodo in periodos:
                inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")

                if periodo.nombresito:
                    self._text.insert(tk.END,
                        f"  • {periodo.nombresito}: {inicio_str} - {fin_str}\n",
                        "periodo")
                else:
                    self._text.insert(tk.END,
                        f"  • {inicio_str} - {fin_str}\n",
                        "periodo")

        self._text.config(state='disabled')

    def limpiar(self):
        """Limpiar el panel"""
        self._text.config(state='normal')
        self._text.delete('1.0', tk.END)
        self._text.config(state='disabled')

    def reset(self):
        self.limpiar()
```

**Migración en `interfaz.py`**:

Reemplazar líneas 172-208:
```python
from UI.components.periodos_panel import PeriodosPanel

# En __init__ (después de crear precio_frame):
self.periodos_panel = PeriodosPanel(self.precio_frame, fonts=self.fonts)
self.periodos_panel.grid(row=2, column=0, sticky='nsew', pady=(0, 10))

# Actualizar método actualizar_periodos_habitacion() línea 618:
def actualizar_periodos_habitacion(self, habitacion):
    hotel_nombre = self.state.hotel.get().lower() + " (a)"
    hotel_actual = None
    for hotel_excel in self.state.hoteles_excel:
        if hotel_excel.nombre.lower() == hotel_nombre:
            hotel_actual = hotel_excel
            break

    if not hotel_actual:
        self.periodos_panel.limpiar()
        return

    self.periodos_panel.actualizar_periodos(habitacion, hotel_actual)

# Actualizar limpiar_periodos() línea 688:
def limpiar_periodos(self):
    self.periodos_panel.limpiar()
```

**Testing**:
- [ ] Muestra periodos correctamente
- [ ] Muestra advertencia si no hay periodos
- [ ] Agrupa por nombre de grupo
- [ ] Scrollbar funciona
- [ ] limpiar() funciona

### 2.4 PrecioPanel

**Archivo**: `UI/components/precio_panel.py`

```python
import tkinter as tk
from tkinter import ttk
from UI.components.base_component import BaseComponent

class PrecioPanel(BaseComponent):
    """Panel de visualización del precio de habitación"""

    def __init__(self, parent, textvariable=None, fonts=None, **kwargs):
        self.textvariable = textvariable or tk.StringVar(value="(ninguna seleccionada)")
        self.fonts = fonts
        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        # Título
        font_titulo = self.fonts.negrita if self.fonts else None
        ttk.Label(self, text="Precio de la habitación", font=font_titulo).grid(
            row=0, column=0, sticky='w', pady=(0,5), padx=(0,10)
        )

        # Contenedor del precio
        precio_container = tk.Frame(self, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        precio_container.grid(row=1, column=0, sticky='ew', pady=(0,15), padx=(0,10))

        # Label del precio
        font_precio = self.fonts.precio if self.fonts else None
        self._label_precio = tk.Label(
            precio_container,
            textvariable=self.textvariable,
            font=font_precio,
            bg='#F5F5F5',
            fg='#2C3E50',
            padx=12,
            pady=8,
            anchor='w'
        )
        self._label_precio.pack(fill='both', expand=True)

    def get_value(self):
        return self.textvariable.get()

    def set_value(self, precio):
        self.textvariable.set(precio)

    def reset(self):
        self.textvariable.set("(ninguna seleccionada)")
```

**Migración en `interfaz.py`**:

Reemplazar líneas 150-170:
```python
from UI.components.precio_panel import PrecioPanel

# En __init__:
self.precio_panel = PrecioPanel(
    self.precio_frame,
    textvariable=self.state.precio,
    fonts=self.fonts
)
self.precio_panel.grid(row=0, column=0, sticky='ew')
```

**Testing**:
- [ ] Muestra precio correctamente
- [ ] Actualiza cuando cambia textvariable
- [ ] reset() funciona

**Testing Fase 2**:
- [ ] DateInputWidget funciona correctamente
- [ ] LabeledComboBox funciona correctamente
- [ ] PeriodosPanel funciona correctamente
- [ ] PrecioPanel funciona correctamente
- [ ] La aplicación mantiene funcionalidad original
- [ ] Menos líneas en interfaz.py

---

## FASE 3: Vistas/Formularios (2 días)

### Objetivo
Agrupar componentes en vistas lógicas.

### 3.1 HotelSelectionForm

**Archivo**: `UI/views/hotel_selection_form.py`

```python
import tkinter as tk
from UI.components.labeled_combobox import LabeledComboBox

class HotelSelectionForm(tk.Frame):
    """Formulario de selección de hotel, edificio y habitación"""

    def __init__(self, parent, app_state, fonts, **kwargs):
        super().__init__(parent, **kwargs)
        self.app_state = app_state
        self.fonts = fonts

        # Componentes
        self.hotel_cb = None
        self.edificio_cb = None
        self.habitacion_cb = None

        self._setup_ui()

    def _setup_ui(self):
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Hotel (siempre visible)
        self.hotel_cb = LabeledComboBox(
            self,
            label_text="Selección hotel:",
            textvariable=self.app_state.hotel,
            fonts=self.fonts
        )
        self.hotel_cb.grid(row=0, column=0, sticky='ew')

        # Expandir
        self.grid_columnconfigure(0, weight=1)

    def mostrar_edificio(self, valores):
        """Mostrar combobox de edificio con valores"""
        if self.edificio_cb:
            self.edificio_cb.destroy()

        self.edificio_cb = LabeledComboBox(
            self,
            label_text="Edificio:",
            textvariable=self.app_state.edificio,
            fonts=self.fonts
        )
        self.edificio_cb.set_values(valores)
        self.edificio_cb.grid(row=1, column=0, sticky='ew')

    def ocultar_edificio(self):
        """Ocultar combobox de edificio"""
        if self.edificio_cb:
            self.edificio_cb.destroy()
            self.edificio_cb = None

    def mostrar_habitacion(self, valores):
        """Mostrar combobox de habitación con valores"""
        if self.habitacion_cb:
            self.habitacion_cb.destroy()

        row = 2 if self.edificio_cb else 1

        self.habitacion_cb = LabeledComboBox(
            self,
            label_text="Selección habitación Excel:",
            textvariable=self.app_state.habitacion,
            fonts=self.fonts
        )
        self.habitacion_cb.set_values(valores)
        self.habitacion_cb.grid(row=row, column=0, sticky='ew')
```

**Migración**: Simplifica la creación dinámica de widgets en `crear_campos_estaticos()`.

### 3.2 ReservationForm

**Archivo**: `UI/views/reservation_form.py`

```python
import tkinter as tk
from tkinter import ttk
from UI.components.date_input import DateInputWidget
from UI.components.labeled_entry import LabeledEntry

class ReservationForm(tk.Frame):
    """Formulario de datos de reserva (fechas y huéspedes)"""

    def __init__(self, parent, app_state, fonts, on_submit=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self.on_submit = on_submit

        self._setup_ui()

    def _setup_ui(self):
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Fecha entrada
        self.fecha_entrada = DateInputWidget(
            self,
            label_text="Fecha de entrada (DD-MM-AAAA):",
            fonts=self.fonts
        )
        self.fecha_entrada.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        self.app_state.fecha_entrada_completa = self.fecha_entrada.get_fecha_completa_var()

        # Fecha salida
        self.fecha_salida = DateInputWidget(
            self,
            label_text="Fecha de salida (DD-MM-AAAA):",
            fonts=self.fonts
        )
        self.fecha_salida.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.app_state.fecha_salida_completa = self.fecha_salida.get_fecha_completa_var()

        # Adultos
        self.adultos_entry = LabeledEntry(
            self,
            label_text="Cantidad de adultos:",
            textvariable=self.app_state.adultos,
            fonts=self.fonts
        )
        self.adultos_entry.grid(row=2, column=0, sticky='ew', pady=(0, 10))

        # Niños
        self.ninos_entry = LabeledEntry(
            self,
            label_text="Cantidad de niños:",
            textvariable=self.app_state.ninos,
            fonts=self.fonts
        )
        self.ninos_entry.grid(row=3, column=0, sticky='ew', pady=(0, 10))

        # Botón ejecutar
        style = ttk.Style()
        style.configure('Boton.TButton', font=self.fonts.boton)
        self.boton_ejecutar = ttk.Button(
            self,
            text="Ejecutar comparación",
            command=self._on_submit_clicked,
            style='Boton.TButton'
        )
        self.boton_ejecutar.grid(row=4, column=0, sticky='ew', pady=(10, 10))

        # Expandir
        self.grid_columnconfigure(0, weight=1)

    def _on_submit_clicked(self):
        if self.on_submit:
            self.on_submit()
```

### 3.3 ResultsView

**Archivo**: `UI/views/results_view.py`

```python
import tkinter as tk
from tkinter import ttk

class ResultsView(tk.Frame):
    """Vista de resultados de la comparación"""

    def __init__(self, parent, fonts, **kwargs):
        super().__init__(parent, **kwargs)
        self.fonts = fonts
        self._setup_ui()

    def _setup_ui(self):
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Frame contenedor
        frame_resultado = tk.Frame(self, bg=bg_color)
        frame_resultado.grid(row=0, column=0, sticky='nsew')
        frame_resultado.rowconfigure(0, weight=1)
        frame_resultado.columnconfigure(0, weight=1)

        # Text widget
        self._text = tk.Text(
            frame_resultado,
            height=20,
            width=80,
            font=self.fonts.resultado,
            wrap="word"
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_resultado, orient="vertical", command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=scrollbar.set)

        # Tags
        self._text.tag_configure("bold", font=self.fonts.negrita)
        self._text.tag_configure("grande y negra", font=self.fonts.grande_negrita)

        # Expandir
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def append(self, texto, tags=None):
        """Agregar texto al resultado"""
        if tags:
            self._text.insert(tk.END, texto, tags)
        else:
            self._text.insert(tk.END, texto)

    def clear(self):
        """Limpiar resultados"""
        self._text.delete('1.0', tk.END)

    def get_text_widget(self):
        """Obtener widget Text para acceso directo"""
        return self._text
```

**Testing Fase 3**:
- [ ] HotelSelectionForm muestra/oculta edificio correctamente
- [ ] ReservationForm valida fechas
- [ ] ResultsView muestra resultados con formato
- [ ] Todas las vistas se integran en interfaz.py

---

## FASE 4: Controladores (2 días)

### Objetivo
Extraer lógica de negocio a controladores.

### 4.1 HotelController

**Archivo**: `UI/controllers/hotel_controller.py`

```python
from Core.controller import dar_hoteles_excel

class HotelController:
    """Controlador de lógica de hoteles"""

    def __init__(self, app_state, event_bus):
        self.app_state = app_state
        self.event_bus = event_bus

        # Suscribirse a eventos
        self.event_bus.on('hotel_changed', self.on_hotel_changed)
        self.event_bus.on('edificio_changed', self.on_edificio_changed)

    def cargar_hoteles(self):
        """Cargar hoteles desde Excel"""
        self.app_state.hoteles_excel = dar_hoteles_excel()
        hoteles = [h.nombre for h in self.app_state.hoteles_excel]

        # Limpiar sufijo (A)
        hoteles = [h.replace("(A)", "").strip() for h in hoteles]

        return hoteles

    def cargar_edificios(self, hotel_nombre):
        """Cargar edificios de un hotel"""
        hotel = hotel_nombre.lower() + " (a)"

        for hotel_excel in self.app_state.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                edificios = []
                for tipo in hotel_excel.tipos:
                    nombre_edificio = tipo.nombre
                    nombre_grupo = self._obtener_grupo_periodo_edificio(hotel_excel, tipo)

                    if nombre_grupo:
                        edificios.append(f"{nombre_edificio} - {nombre_grupo}")
                    else:
                        edificios.append(nombre_edificio)

                return edificios

        return []

    def cargar_habitaciones(self, hotel_nombre, edificio_nombre=None):
        """Cargar habitaciones de un hotel/edificio"""
        hotel = hotel_nombre.lower() + " (a)"
        hotel_excel = None

        for h in self.app_state.hoteles_excel:
            if h.nombre.lower() == hotel:
                hotel_excel = h
                break

        if not hotel_excel:
            return []

        # Sin edificio: habitaciones directas
        if edificio_nombre is None:
            habitaciones = hotel_excel.habitaciones_directas
        else:
            # Con edificio: buscar tipo
            nombre_tipo_base = edificio_nombre.split(' - ')[0] if ' - ' in edificio_nombre else edificio_nombre

            for tipo in hotel_excel.tipos:
                if tipo.nombre == nombre_tipo_base:
                    habitaciones = tipo.habitaciones
                    break
            else:
                return []

        # Crear nombres con grupo de periodo
        nombres = []
        for hab in habitaciones:
            nombre_grupo = self._obtener_grupo_periodo_habitacion(hotel_excel, hab)
            if nombre_grupo:
                nombres.append(f"{hab.nombre} - {nombre_grupo}")
            else:
                nombres.append(hab.nombre)

        # Guardar habitaciones en estado
        self.app_state.habitaciones_excel = habitaciones

        return nombres

    def on_hotel_changed(self, hotel_nombre):
        """Callback cuando cambia el hotel"""
        if not hotel_nombre:
            return

        hotel = hotel_nombre.lower() + " (a)"

        for hotel_excel in self.app_state.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                # Emitir evento con información del hotel
                tiene_tipos = bool(hotel_excel.tipos)
                self.event_bus.emit('hotel_loaded', {
                    'hotel': hotel_excel,
                    'tiene_tipos': tiene_tipos
                })
                break

    def on_edificio_changed(self, edificio_nombre):
        """Callback cuando cambia el edificio"""
        if not edificio_nombre:
            return

        hotel_nombre = self.app_state.hotel.get()
        habitaciones = self.cargar_habitaciones(hotel_nombre, edificio_nombre)

        self.event_bus.emit('habitaciones_loaded', habitaciones)

    def _obtener_grupo_periodo_edificio(self, hotel_excel, tipo):
        """Obtiene el nombre del grupo de periodo para un edificio"""
        if not tipo.habitaciones:
            return None

        primera_habitacion = tipo.habitaciones[0]
        if not primera_habitacion.periodo_ids:
            return None

        primer_periodo_id = next(iter(primera_habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None

    def _obtener_grupo_periodo_habitacion(self, hotel_excel, habitacion):
        """Obtiene el nombre del grupo de periodo para una habitación"""
        if not habitacion.periodo_ids:
            return None

        primer_periodo_id = next(iter(habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None
```

### 4.2 ValidationController

**Archivo**: `UI/controllers/validation_controller.py`

```python
from datetime import datetime
from tkinter import messagebox

class ValidationController:
    """Controlador de validaciones de negocio"""

    def __init__(self, app_state):
        self.app_state = app_state

    def validar_fecha(self, fecha_str, nombre_campo):
        """Validar formato y existencia de fecha"""
        try:
            fecha_dt = datetime.strptime(fecha_str, "%d-%m-%Y")
            fecha_actual = datetime.now()

            if fecha_actual > fecha_dt:
                messagebox.showerror(
                    "Error",
                    f"La fecha de {nombre_campo} debe ser mayor o igual a la actual."
                )
                return False

            return True
        except ValueError:
            messagebox.showerror(
                "Error",
                f"La fecha de {nombre_campo} debe tener formato DD-MM-AAAA y ser válida."
            )
            return False

    def validar_orden_fechas(self, fecha_entrada_str, fecha_salida_str):
        """Validar que salida sea posterior a entrada"""
        try:
            fecha_entrada = datetime.strptime(fecha_entrada_str, "%d-%m-%Y")
            fecha_salida = datetime.strptime(fecha_salida_str, "%d-%m-%Y")
        except ValueError:
            return False

        if fecha_salida <= fecha_entrada:
            messagebox.showerror(
                "Error",
                "La fecha de salida debe ser posterior a la de entrada."
            )
            return False

        return True

    def validar_campos_completos(self):
        """Validar que todos los campos requeridos estén completos"""
        campos = {
            "Fecha de entrada": self.app_state.fecha_entrada_completa.get(),
            "Fecha de salida": self.app_state.fecha_salida_completa.get(),
            "Número de adultos": self.app_state.adultos.get(),
            "Número de niños": self.app_state.ninos.get(),
            "Habitación Excel": self.app_state.habitacion.get(),
            "Precio": self.app_state.precio.get()
        }

        for nombre, valor in campos.items():
            if valor in ("", None, "(ninguna seleccionada)"):
                messagebox.showerror(
                    "Error",
                    f"El campo '{nombre}' no puede estar vacío."
                )
                return False

            if nombre == "Número de adultos" and valor <= 0:
                messagebox.showerror(
                    "Error",
                    "Debe haber al menos 1 adulto."
                )
                return False

        return True

    def validar_todo(self):
        """Ejecutar todas las validaciones"""
        if not self.validar_campos_completos():
            return False

        fecha_entrada = self.app_state.fecha_entrada_completa.get()
        fecha_salida = self.app_state.fecha_salida_completa.get()

        if not self.validar_fecha(fecha_entrada, "entrada"):
            return False

        if not self.validar_fecha(fecha_salida, "salida"):
            return False

        if not self.validar_orden_fechas(fecha_entrada, fecha_salida):
            return False

        return True
```

### 4.3 ComparisonController

**Archivo**: `UI/controllers/comparison_controller.py`

```python
import asyncio
import threading
from Core.controller import (
    dar_hotel_web,
    comparar_habitaciones,
    dar_habitacion_web,
    dar_mensaje,
    normalizar_precio_str,
    imprimir_habitacion_web
)

class ComparisonController:
    """Controlador de ejecución de comparación"""

    def __init__(self, app_state, event_bus):
        self.app_state = app_state
        self.event_bus = event_bus

    def ejecutar_comparacion_async(self):
        """Ejecutar comparación en thread separado"""
        threading.Thread(target=self._run_async, daemon=True).start()

    def _run_async(self):
        """Wrapper para asyncio.run"""
        asyncio.run(self._ejecutar_comparacion())

    async def _ejecutar_comparacion(self):
        """Lógica principal de comparación"""
        try:
            # Emitir evento de inicio
            self.event_bus.emit('comparison_started')

            # Obtener datos
            fecha_entrada = self.app_state.fecha_entrada_completa.get()
            fecha_salida = self.app_state.fecha_salida_completa.get()
            adultos = self.app_state.adultos.get()
            ninos = self.app_state.ninos.get()
            habitacion_excel = self.app_state.habitacion.get()
            precio_str = self.app_state.precio.get()

            # Web scraping
            hotel_web = await dar_hotel_web(fecha_entrada, fecha_salida, adultos, ninos)

            if not hotel_web or not hotel_web.habitacion:
                self.event_bus.emit('comparison_error', "No se pudieron obtener datos del hotel web")
                return

            # Comparación
            precio = normalizar_precio_str(precio_str)
            coincide = await comparar_habitaciones(habitacion_excel, precio)
            habitacion_web = dar_habitacion_web()
            mensaje_match = dar_mensaje()

            # Guardar resultado en estado
            self.app_state.habitacion_web = habitacion_web

            # Construir resultado
            resultado = {
                'habitacion_web': imprimir_habitacion_web(habitacion_web),
                'mensaje_match': mensaje_match,
                'coincide': coincide
            }

            # Emitir evento de finalización
            self.event_bus.emit('comparison_completed', resultado)

        except Exception as e:
            self.event_bus.emit('comparison_error', str(e))
```

**Testing Fase 4**:
- [ ] HotelController carga hoteles correctamente
- [ ] ValidationController valida todos los casos
- [ ] ComparisonController ejecuta comparación
- [ ] Eventos se emiten correctamente
- [ ] interfaz.py usa controladores en lugar de lógica directa

---

## FASE 5: Integración y Refactorización Final (1-2 días)

### Objetivo
Integrar todos los componentes y limpiar código legacy.

### 5.1 Refactorizar interfaz.py

**Estructura final de `interfaz.py`**:

```python
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

# Estado y eventos
from UI.state.event_bus import EventBus
from UI.state.app_state import AppState
from UI.styles.fonts import FontManager

# Componentes
from UI.components.periodos_panel import PeriodosPanel
from UI.components.precio_panel import PrecioPanel

# Vistas
from UI.views.hotel_selection_form import HotelSelectionForm
from UI.views.reservation_form import ReservationForm
from UI.views.results_view import ResultsView
from UI.views.email_view import EmailView

# Controladores
from UI.controllers.hotel_controller import HotelController
from UI.controllers.validation_controller import ValidationController
from UI.controllers.comparison_controller import ComparisonController
from UI.controllers.email_controller import EmailController


class InterfazApp:
    """Aplicación principal de comparación de precios"""

    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de precios")
        self.root.geometry("900x700")

        # Sistema de eventos
        self.event_bus = EventBus()

        # Estado
        self.state = AppState(self.event_bus)

        # Fuentes
        self.fonts = FontManager(self.root)

        # Controladores
        self.hotel_ctrl = HotelController(self.state, self.event_bus)
        self.validation_ctrl = ValidationController(self.state)
        self.comparison_ctrl = ComparisonController(self.state, self.event_bus)
        self.email_ctrl = EmailController(self.state, self.event_bus)

        # Suscribirse a eventos
        self._setup_event_listeners()

        # Construir UI
        self._setup_ui()

        # Cargar datos iniciales
        self._cargar_datos_iniciales()

    def _setup_event_listeners(self):
        """Configurar listeners de eventos"""
        self.event_bus.on('hotel_loaded', self._on_hotel_loaded)
        self.event_bus.on('habitaciones_loaded', self._on_habitaciones_loaded)
        self.event_bus.on('habitacion_changed', self._on_habitacion_changed)
        self.event_bus.on('comparison_started', self._on_comparison_started)
        self.event_bus.on('comparison_completed', self._on_comparison_completed)
        self.event_bus.on('comparison_error', self._on_comparison_error)

    def _setup_ui(self):
        """Construir interfaz de usuario"""
        # Configurar grid principal
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1)

        # Frame principal izquierdo
        principal_container = tk.Frame(self.root, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        principal_container.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=4, pady=4)

        principal_frame = tk.Frame(principal_container, bg='#F5F5F5')
        principal_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        principal_frame.columnconfigure(0, weight=1)
        principal_container.columnconfigure(0, weight=1)
        principal_container.rowconfigure(0, weight=1)

        # Vista de selección de hotel
        self.hotel_form = HotelSelectionForm(principal_frame, self.state, self.fonts, bg='#F5F5F5')
        self.hotel_form.grid(row=0, column=0, sticky='ew')

        # Vista de formulario de reserva
        self.reservation_form = ReservationForm(
            principal_frame,
            self.state,
            self.fonts,
            on_submit=self._on_submit_comparison,
            bg='#F5F5F5'
        )
        self.reservation_form.grid(row=1, column=0, sticky='ew')

        # Vista de resultados
        self.results_view = ResultsView(principal_frame, self.fonts, bg='#F5F5F5')
        self.results_view.grid(row=2, column=0, sticky='nsew')

        principal_frame.rowconfigure(2, weight=1)

        # Panel derecho (precio y periodos)
        precio_frame = ttk.Frame(self.root)
        precio_frame.grid(row=0, column=2, rowspan=3, sticky='nsew', padx=4, pady=2)

        # Panel de precio
        self.precio_panel = PrecioPanel(precio_frame, textvariable=self.state.precio, fonts=self.fonts)
        self.precio_panel.grid(row=0, column=0, sticky='ew')

        # Panel de periodos
        self.periodos_panel = PeriodosPanel(precio_frame, fonts=self.fonts)
        self.periodos_panel.grid(row=1, column=0, sticky='nsew')

        precio_frame.rowconfigure(1, weight=1)

    def _cargar_datos_iniciales(self):
        """Cargar datos iniciales"""
        hoteles = self.hotel_ctrl.cargar_hoteles()
        self.hotel_form.hotel_cb.set_values(hoteles)

        if hoteles:
            self.hotel_form.hotel_cb.set_value(hoteles[0])

    def _on_hotel_loaded(self, data):
        """Callback cuando se carga un hotel"""
        if data['tiene_tipos']:
            # Mostrar selector de edificio
            edificios = self.hotel_ctrl.cargar_edificios(self.state.hotel.get())
            self.hotel_form.mostrar_edificio(edificios)
        else:
            # Ocultar edificio y cargar habitaciones directas
            self.hotel_form.ocultar_edificio()
            habitaciones = self.hotel_ctrl.cargar_habitaciones(self.state.hotel.get())
            self.hotel_form.mostrar_habitacion(habitaciones)

        # Limpiar periodos
        self.periodos_panel.limpiar()

    def _on_habitaciones_loaded(self, habitaciones):
        """Callback cuando se cargan habitaciones"""
        self.hotel_form.mostrar_habitacion(habitaciones)
        self.periodos_panel.limpiar()

    def _on_habitacion_changed(self, habitacion_nombre):
        """Callback cuando cambia la habitación"""
        if not habitacion_nombre:
            return

        try:
            idx = self.hotel_form.habitacion_cb.current()
            habitacion = self.state.habitaciones_excel[idx]

            # Actualizar precio
            if habitacion.precio is not None:
                if isinstance(habitacion.precio, (int, float)):
                    precio_texto = f"${habitacion.precio:.2f}"
                else:
                    precio_texto = str(habitacion.precio)
            elif habitacion.precio_string:
                precio_texto = habitacion.precio_string
            else:
                precio_texto = "Sin precio"

            self.state.precio.set(precio_texto)

            # Actualizar periodos
            hotel_nombre = self.state.hotel.get().lower() + " (a)"
            hotel_actual = None
            for hotel_excel in self.state.hoteles_excel:
                if hotel_excel.nombre.lower() == hotel_nombre:
                    hotel_actual = hotel_excel
                    break

            if hotel_actual:
                self.periodos_panel.actualizar_periodos(habitacion, hotel_actual)

        except Exception as e:
            print(f"Error al actualizar habitación: {e}")

    def _on_submit_comparison(self):
        """Callback cuando se envía el formulario"""
        # Validar
        if not self.validation_ctrl.validar_todo():
            return

        # Ejecutar comparación
        self.comparison_ctrl.ejecutar_comparacion_async()

    def _on_comparison_started(self, data=None):
        """Callback cuando inicia la comparación"""
        self.results_view.clear()
        self.results_view.append("Ejecutando scraping...\n", ("bold",))

    def _on_comparison_completed(self, resultado):
        """Callback cuando finaliza la comparación"""
        self.results_view.append("\nHabitación web de mayor coincidencia:\n", ("bold",))
        self.results_view.append(f"{resultado['habitacion_web']}\n")

        if resultado['mensaje_match']:
            self.results_view.append(f"{resultado['mensaje_match']}\n", ("bold",))

        if resultado['coincide']:
            self.results_view.append("Se encontró diferencia de precio.\n")
            # Mostrar botón de email
            # TODO: implementar
        else:
            self.results_view.append("Las habitaciones coinciden en precio y nombre.\n")

    def _on_comparison_error(self, error_msg):
        """Callback cuando hay error en la comparación"""
        self.results_view.append(f"Error: {error_msg}\n", ("bold",))


def run_interfaz():
    """Ejecutar interfaz"""
    # Ejecutar testExtractor2 para generar archivo de validación
    print("\n" + "="*60)
    print("EJECUTANDO testExtractor2.py...")
    print("="*60 + "\n")

    try:
        subprocess.run([sys.executable, "testExtractor2.py"], check=True)
        print("\n" + "="*60)
        print("testExtractor2.py ejecutado exitosamente")
        print("="*60 + "\n")
    except subprocess.CalledProcessError as e:
        print(f"\nError al ejecutar testExtractor2.py: {e}\n")
    except FileNotFoundError:
        print("\nNo se encontró testExtractor2.py, continuando con la interfaz...\n")

    # Iniciar interfaz
    root = tk.Tk()
    app = InterfazApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_interfaz()
```

### 5.2 Métricas de Mejora

**Antes de la refactorización**:
- 1 archivo: 784 líneas
- 1 clase monolítica
- 20+ métodos mezclados
- Duplicación de código
- Testing difícil

**Después de la refactorización**:
- ~15 archivos organizados
- Interfaz principal: ~200 líneas
- Componentes reutilizables: 6
- Vistas: 4
- Controladores: 4
- Separación de concerns clara
- Testing modular

### 5.3 Testing Final

**Checklist de Testing**:
- [ ] Todas las funcionalidades originales funcionan
- [ ] Selección de hotel funciona
- [ ] Selección de edificio funciona (condicional)
- [ ] Selección de habitación funciona
- [ ] Fechas se validan correctamente
- [ ] Comparación se ejecuta correctamente
- [ ] Resultados se muestran correctamente
- [ ] Email se envía correctamente
- [ ] Periodos se muestran correctamente
- [ ] Precio se actualiza correctamente

---

## Beneficios Obtenidos

### 1. **Mantenibilidad**
- Código organizado en módulos pequeños
- Fácil localizar y arreglar bugs
- Cambios aislados no afectan todo el sistema

### 2. **Testabilidad**
- Componentes testeables de forma aislada
- Controladores sin dependencias de UI
- Validadores independientes

### 3. **Reutilización**
- Componentes pueden usarse en otras vistas
- Controladores reutilizables
- Validadores compartibles

### 4. **Escalabilidad**
- Fácil agregar nuevos componentes
- Nuevas vistas sin modificar existentes
- Nuevos controladores siguiendo patrón

### 5. **Colaboración**
- Estructura clara para múltiples desarrolladores
- Responsabilidades bien definidas
- Menos conflictos en git

---

## Próximos Pasos Recomendados

### 1. **Testing Automatizado**
Crear tests unitarios para:
- Validadores
- Componentes
- Controladores

### 2. **Documentación**
- Docstrings en todos los métodos
- Ejemplos de uso de componentes
- Diagramas de arquitectura

### 3. **Mejoras UI/UX**
- Feedback visual durante scraping
- Mensajes de error más informativos
- Animaciones de carga

### 4. **Performance**
- Cache de resultados de scraping
- Lazy loading de componentes
- Optimización de renders

### 5. **Features Adicionales**
- Historial de comparaciones
- Exportar resultados a PDF
- Configuración de preferencias

---

## Recursos y Referencias

### Documentación de Tkinter
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Tkinter ttk Themed Widgets](https://docs.python.org/3/library/tkinter.ttk.html)

### Patrones de Diseño
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://en.wikipedia.org/wiki/Design_Patterns)
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [MVC Pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

### Python Best Practices
- [PEP 8 – Style Guide for Python Code](https://pep8.org/)
- [Clean Code in Python](https://www.oreilly.com/library/view/clean-code-in/9781800560215/)

---

## Conclusión

Esta reestructuración transforma una interfaz monolítica de 784 líneas en una arquitectura modular, mantenible y escalable. El proceso es gradual y seguro, permitiendo mantener funcionalidad mientras se mejora la estructura.

La clave es **componentizar progresivamente**, empezando por los elementos más simples y duplicados, hasta llegar a una arquitectura completa con separación de responsabilidades.

**Tiempo estimado total**: 8-10 días de trabajo

**Riesgo**: Bajo (migración incremental)

**ROI**: Alto (código mantenible a largo plazo)
