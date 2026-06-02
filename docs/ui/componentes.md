# Componentes UI

Documentación completa de todos los componentes reutilizables de la interfaz.

El proyecto tiene **dos familias** de componentes:

| Familia | Base | Framework | Uso |
|---------|------|-----------|-----|
| **Legacy** | `BaseComponent` | Tkinter clásico | `interfaz.py` (InterfazApp) |
| **CTk** | `CTkBaseComponent` | CustomTkinter | `interfaz_ctk.py` (CrawlCompareGUI) ← **actual** |

---

## Tabla de Contenidos

**Familia CTk (actual)**
- [CTkBaseComponent](#ctkbasecomponent-clase-base-ctk)
- [CTkCard](#ctkcard)
- [CTkLabeledComboBox](#ctklabeledcombobox)
- [CTkDateInput](#ctkdateinput)
- [CTkLabeledEntry](#ctklabeledentry)
- [CTkPrecioPanel](#ctkpreciopanel)
- [CTkPeriodosPanel](#ctkperiodospanel)
- [CTkCustomDropdown](#ctkcustomdropdown)

**Familia Legacy (Tkinter)**
- [BaseComponent](#basecomponent-clase-base-legacy)
- [DateInputWidget](#dateinputwidget)
- [LabeledComboBox](#labeledcombobox)
- [EntradaEtiquetada](#entradaetiquetada)
- [PeriodosPanel](#periodospanel)
- [PrecioPanel](#preciopanel)

---

# Familia CTk (CustomTkinter)

## CTkBaseComponent (Clase Base CTk)

**Archivo**: [UI/components/ctk_base_component.py](../../Hoteles/UI/components/ctk_base_component.py)

### Propósito

Clase base para todos los componentes CustomTkinter. Hereda de `ctk.CTkFrame` y aplica los estilos del sistema por defecto.

### Defaults Aplicados

```python
fg_color      = Colors.SURFACE    # "#FFFFFF"
corner_radius = Spacing.RADIUS_MD # 8
border_width  = 0
```

### Métodos

| Método | Descripción |
|--------|-------------|
| `_setup_ui()` | Hook para construir la UI (sobreescribir en subclases) |
| `get_value()` | Obtener valor — lanza `NotImplementedError` si no se sobreescribe |
| `set_value(value)` | Establecer valor — lanza `NotImplementedError` si no se sobreescribe |
| `reset()` | Resetear a estado inicial (no-op por defecto) |

### Pattern de Implementación

```python
class MiComponente(CTkBaseComponent):
    def _setup_ui(self):
        label = ctk.CTkLabel(self, text="Hola")
        label.pack()

    def get_value(self):
        return self._valor

    def set_value(self, value):
        self._valor = value
```

---

## CTkCard

**Archivo**: [UI/components/ctk_card.py](../../Hoteles/UI/components/ctk_card.py)

### Propósito

Contenedor visual con borde, título opcional e ícono. Agrupa elementos relacionados con estilo consistente.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `title` | str | `None` | Texto del título en la parte superior |
| `icon` | str | `None` | Emoji/ícono junto al título |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

### Estructura Visual

```
╔══════════════════════════════╗
║ 🏨 SELECCIÓN DE RESERVA      ║  ← título (TEXT_SECONDARY, bold, small)
╠══════════════════════════════╣
║                              ║
║  [content_frame]             ║  ← padding CARD_PADDING (24px) lateral
║                              ║
╚══════════════════════════════╝
  border: 1px Colors.BORDER (#E2E8F0)
  corner_radius: RADIUS_MD (8px)
```

### Atributos Públicos

- `content_frame` — `CTkFrame` transparente donde agregar widgets hijos

### Métodos

| Método | Descripción |
|--------|-------------|
| `set_title(new_title)` | Actualiza texto del título |
| `clear_content()` | Destruye todos los widgets del `content_frame` |

### Uso en CrawlCompareGUI

```python
# Card de selección de reserva
card = CTkCard(parent, title="SELECCIÓN DE RESERVA", icon="🏨")
card.pack(fill="x", pady=(0, Spacing.MD))

CTkLabeledComboBox(card.content_frame, label="Hotel", ...).pack(fill="x")
```

---

## CTkLabeledComboBox

**Archivo**: [UI/components/ctk_labeled_combobox.py](../../Hoteles/UI/components/ctk_labeled_combobox.py)

### Propósito

ComboBox con label superior. Versión CTk de `LabeledComboBox`.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `label` | str | — | Texto del label (obligatorio) |
| `textvariable` | tk.StringVar | `None` | Variable vinculada al valor |
| `values` | list[str] | `[]` | Opciones iniciales |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

### Atributos Públicos

- `combobox` — el `CTkComboBox` interno (para configurar `command`, `values`, etc.)

### Métodos

| Método | Descripción |
|--------|-------------|
| `set_values(values: list[str])` | Actualiza las opciones del combobox |
| `get_value() → str` | Retorna opción seleccionada |
| `set_value(value: str)` | Establece opción seleccionada |

### Notas de Uso

`CTkComboBox` pasa el valor seleccionado como argumento al `command`:

```python
self.hotel_combo.combobox.configure(command=self._on_hotel_changed)

def _on_hotel_changed(self, value=None):
    hotel = value or self.state.hotel.get()
```

---

## CTkDateInput

**Archivo**: [UI/components/ctk_date_input.py](../../Hoteles/UI/components/ctk_date_input.py)

### Propósito

Entrada de fecha DD/MM/AAAA con tres campos separados. Versión CTk de `DateInputWidget`.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `label` | str | `"Fecha"` | Texto del label superior |
| `day_var` | tk.StringVar | — | Variable para el día |
| `month_var` | tk.StringVar | — | Variable para el mes |
| `year_var` | tk.StringVar | — | Variable para el año |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

### Diferencia con Legacy

La versión CTk recibe las `StringVar` del `AppState` directamente, en vez de crear las suyas propias. La consolidación en `fecha_entrada_completa` / `fecha_salida_completa` se hace en `CrawlCompareGUI._actualizar_fecha_entrada/salida()` via `trace_add`.

---

## CTkLabeledEntry

**Archivo**: [UI/components/ctk_labeled_entry.py](../../Hoteles/UI/components/ctk_labeled_entry.py)

### Propósito

Entry con label superior. Versión CTk de `EntradaEtiquetada`.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `label` | str | — | Texto del label (obligatorio) |
| `textvariable` | tk.Variable | `None` | Variable vinculada |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

> **Nota**: Los campos de Adultos/Niños en `CrawlCompareGUI` se construyen con `ctk.CTkEntry` directamente (sin CTkLabeledEntry) para controlar el layout en grilla.

---

## CTkPrecioPanel

**Archivo**: [UI/components/ctk_precio_panel.py](../../Hoteles/UI/components/ctk_precio_panel.py)

### Propósito

Panel para mostrar precio(s) de habitación. Soporta precio único o múltiples precios por periodo. Versión CTk de `PrecioPanel`.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `textvariable` | tk.StringVar | — | Variable para precio simple |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

### Atributos Públicos

- `content_frame` — frame interno donde se agrega dinámicamente el botón de Email

### Métodos

| Método | Descripción |
|--------|-------------|
| `mostrar_precios_multiples(precios_data: list[dict])` | Muestra precios por periodo |
| `_mostrar_mensaje(mensaje: str)` | Muestra mensaje de estado |
| `get_value() → str` | Retorna precio actual |
| `set_value(precio_str: str)` | Establece precio simple |

### Formato de `precios_data`

```python
[
    {
        'periodo': periodo_obj,     # objeto Periodo
        'precio': 450.0,            # float
        'nombre_grupo': 'low season'
    },
    ...
]
```

### Evento que lo alimenta

El `ControladorPrecios` emite `'precios_actualizados'` con:

```python
# tipo "precios_calculados"
data = {
    'tipo': 'precios_calculados',
    'precios': [...]  # lista de dicts como arriba
}

# tipo "sin_fechas" o "sin_periodos"
data = {
    'tipo': 'sin_fechas',
    'mensaje': 'Ingrese fechas para ver precios'
}
```

`CrawlCompareGUI._on_precios_actualizados()` despacha al método correspondiente.

---

## CTkPeriodosPanel

**Archivo**: [UI/components/ctk_periodos_panel.py](../../Hoteles/UI/components/ctk_periodos_panel.py)

### Propósito

Panel de visualización de periodos agrupados. Versión CTk de `PeriodosPanel`.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `**kwargs` | dict | — | Args adicionales para CTkFrame |

> A diferencia de la versión legacy, **no recibe `fonts`** — usa el sistema de estilos CTk directamente.

### Métodos

| Método | Descripción |
|--------|-------------|
| `actualizar_periodos(habitacion, hotel_excel)` | Carga y muestra periodos de la habitación |
| `limpiar()` | Borra todo el contenido |

---

## CTkCustomDropdown

**Archivo**: [UI/components/ctk_custom_dropdown.py](../../Hoteles/UI/components/ctk_custom_dropdown.py)

### Propósito

Dropdown personalizado (alternativa a `CTkComboBox` con mayor control visual).

### Problemas conocidos

Ver [troubleshooting-ctk.md](troubleshooting-ctk.md) para los siguientes casos ya investigados:
- **Scaling/DPI**: ancho del popup desborda — solución: dividir `winfo_width()` por `_get_widget_scaling()`
- **Scroll fantasma**: scrollear el dropdown también scrollea el panel de fondo — solución: `CTkToplevel(self.winfo_toplevel())`
- **Altura dinámica del popup**: última opción visualmente cortada — 🔬 en investigación

---

# Familia Legacy (Tkinter clásico)

> Estos componentes siguen en uso en `interfaz.py` (`InterfazApp`).
> Para nuevos desarrollos, usar la familia **CTk**.

---

## BaseComponent (Clase Base Legacy)

**Archivo**: [UI/components/base_component.py](../../Hoteles/UI/components/base_component.py)

### Métodos Obligatorios

Todas las subclases DEBEN implementar:

1. **`_setup_ui()`** — Construir interfaz
2. **`get_value()`** — Obtener valor actual
3. **`set_value(value)`** — Establecer valor

### Métodos Opcionales

- **`_bind_events()`** — Conectar eventos internos
- **`reset()`** — Resetear a estado inicial

### Métodos Provistos

- **`enable()`** — Habilita el componente y todos sus hijos
- **`disable()`** — Deshabilita el componente y todos sus hijos

---

## DateInputWidget

**Archivo**: [UI/components/date_input.py](../../Hoteles/UI/components/date_input.py)

### Propósito

Widget para entrada de fecha con validación en tiempo real. Formato: DD-MM-AAAA.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | — | Widget padre (obligatorio) |
| `label_text` | str | `"Fecha"` | Texto del label superior |
| `fonts` | FontManager | `None` | Gestor de fuentes |
| `**kwargs` | dict | — | Args adicionales para Frame |

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `get_value() → str` | Fecha en formato "DD-MM-AAAA" |
| `set_value(fecha_str: str)` | Establece fecha desde string "DD-MM-AAAA" |
| `get_dia_var() → tk.StringVar` | Acceso directo a variable día |
| `get_mes_var() → tk.StringVar` | Acceso directo a variable mes |
| `get_ano_var() → tk.StringVar` | Acceso directo a variable año |
| `on_change(callback)` | Registra callback que se llama cuando cambia la fecha |

---

## LabeledComboBox

**Archivo**: [UI/components/labeled_combobox.py](../../Hoteles/UI/components/labeled_combobox.py)

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `get_value() → str` | Retorna opción seleccionada |
| `set_value(value: str)` | Establece opción seleccionada |
| `set_values(values: list[str])` | Actualiza lista de opciones |
| `get_values() → tuple[str]` | Obtiene opciones actuales |
| `current() → int` | Índice de la opción seleccionada (-1 si ninguna) |
| `on_select(callback)` | Registra callback para selección |
| `set_state(state: str)` | Cambia estado ('readonly', 'normal', 'disabled') |

---

## EntradaEtiquetada

**Archivo**: [UI/components/entrada_etiquetada.py](../../Hoteles/UI/components/entrada_etiquetada.py)

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `get_value() → any` | Retorna valor de la variable vinculada |
| `set_value(value)` | Establece valor |
| `set_state(state: str)` | Cambia estado ('normal', 'disabled', 'readonly') |
| `focus()` | Pone foco en el entry |

---

## PeriodosPanel

**Archivo**: [UI/components/periodos_panel.py](../../Hoteles/UI/components/periodos_panel.py)

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `actualizar_periodos(habitacion, hotel_excel)` | Carga y muestra periodos |
| `limpiar()` | Borra todo el contenido |

---

## PrecioPanel

**Archivo**: [UI/components/precio_panel.py](../../Hoteles/UI/components/precio_panel.py)

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `mostrar_precios_multiples(precios_data: list[dict])` | Muestra precios por periodo |
| `get_value() → str` | Obtiene precio actual |
| `set_value(precio_str: str)` | Establece precio simple |

---

## Resumen de Componentes

### Familia CTk (actual)

| Componente | Propósito | Usado en |
|------------|-----------|----------|
| **CTkCard** | Contenedor visual con título e ícono | CrawlCompareGUI — cards de formulario |
| **CTkLabeledComboBox** | ComboBox con label | Hotel, edificio, habitación |
| **CTkDateInput** | Entrada fecha DD/MM/AAAA | Fechas entrada/salida |
| **CTkLabeledEntry** | Entry con label | Adultos, niños (via CTkEntry directo en CrawlCompareGUI) |
| **CTkPrecioPanel** | Mostrar precio(s) | Panel derecho |
| **CTkPeriodosPanel** | Mostrar periodos | Panel derecho |
| **CTkCustomDropdown** | Dropdown personalizado | Disponible |

### Familia Legacy

| Componente | Propósito | Equivalente CTk |
|------------|-----------|-----------------|
| **DateInputWidget** | Fecha DD-MM-AAAA | CTkDateInput |
| **LabeledComboBox** | ComboBox con label | CTkLabeledComboBox |
| **EntradaEtiquetada** | Entry con label | CTkLabeledEntry |
| **PeriodosPanel** | Periodos de habitación | CTkPeriodosPanel |
| **PrecioPanel** | Precio(s) | CTkPrecioPanel |

---

---

## Sistema de Íconos (`Icons`)

**Archivo**: [UI/styles/icons.py](../../Hoteles/UI/styles/icons.py)
**Assets**: [UI/assets/icons/](../../Hoteles/UI/assets/)

Singleton que carga todos los íconos como `CTkImage` una sola vez al arrancar la app. Los PNGs se generan desde SVGs de [Feather Icons](https://feathericons.com) vía `UI/assets/convert_icons.py`.

### Inicialización

```python
# En CrawlCompareGUI.__init__() — una sola vez
Icons.load()
```

### Uso en widgets

```python
from UI.styles.icons import Icons

# Botón con ícono
ctk.CTkButton(parent, text=" Historial", image=Icons.CLOCK, ...)

# Label con ícono a la izquierda
ctk.CTkLabel(parent, text=" archivo.xlsx", image=Icons.FOLDER_HEADER, compound="left", ...)

# CTkCard con ícono en el título
CTkCard(parent, title="SELECCIÓN", icon=Icons.HOME)
```

### Variantes disponibles

| Variante | Trazo | Cuándo usarla |
|----------|-------|---------------|
| `Icons.NOMBRE` | Gris oscuro `#374151` | Fondo claro o azul (cards, panels, botones) |
| `Icons.NOMBRE_HEADER` | Blanco `#F9FAFB` fijo | Header oscuro (`#1E293B`) — no swapea con el appearance mode |

### Íconos disponibles

| Constante | Feather Icon | Uso actual |
|-----------|-------------|------------|
| `CLOCK` / `CLOCK_HEADER` | `clock` | Botón Historial |
| `SETTINGS` / `SETTINGS_HEADER` | `settings` | Botón Configuración |
| `FOLDER` / `FOLDER_HEADER` | `folder` | Label Excel path |
| `HOME` / `HOME_HEADER` | `home` | CTkCard Selección de Reserva |
| `TRASH` / `TRASH_HEADER` | `trash-2` | Botón Limpiar |
| `DOLLAR` / `DOLLAR_HEADER` | `dollar-sign` | CTkPrecioPanel título |
| `ALERT` / `ALERT_HEADER` | `alert-triangle` | Advertencias de cobertura parcial |
| `X_CIRCLE` / `X_CIRCLE_HEADER` | `x-circle` | Disponible |
| `CHECK_CIRCLE` / `CHECK_CIRCLE_HEADER` | `check-circle` | Disponible |

### Agregar un nuevo ícono

1. Bajar el SVG de [feathericons.com](https://feathericons.com) a `UI/assets/icons/`
2. Correr `python Hoteles/UI/assets/convert_icons.py`
3. Agregar las constantes en `Icons` (`_load` + `_load_header`)

---

---

## CTkInlineSuggester

Popup de autocomplete que se activa mientras el usuario escribe dentro de un contexto delimitado (ej: `{`). No es un widget CTk sino una clase helper que se attachea a un `tk.Text` existente.

**Archivo**: `UI/components/ctk_inline_suggester.py`

### Uso

```python
from UI.components.ctk_inline_suggester import CTkInlineSuggester

suggester = CTkInlineSuggester(
    text_widget=my_textbox._textbox,   # tk.Text interno
    options=["hotel", "precio_excel", ...],
    trigger_char="{",   # default
    close_char="}",     # default
    n=1,                # letras mínimas para activar
)
suggester.attach()
```

### Integración vía CTkTextEditor

```python
CTkTextEditor(
    parent,
    autocomplete_options=["hotel", "precio_excel", ...],
    trigger_char="{",
    close_char="}",
    n=1,
)
```

### Navegación del popup

| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Moverse entre opciones |
| `Tab` / `Return` | Confirmar — reemplaza `{prefijo` por `{tag}` |
| `Escape` | Cerrar sin seleccionar |
| Click | Confirmar con el mouse |

---

Ver también:
- [../desarrollo/convenciones.md](../desarrollo/convenciones.md) — Pattern BaseComponent + helpers de botones + regla de íconos
- [vistas.md](vistas.md) — VistaResultados (compartida entre ambas familias)
- [pantallas.md](pantallas.md) — Layout general de la app
- [../arquitectura/event-driven-mvc.md](../arquitectura/event-driven-mvc.md) — Integración con EventBus
