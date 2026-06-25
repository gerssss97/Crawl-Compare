# Convenciones de Código

Guía de convenciones del proyecto **Crawl-Compare**. Consultá esto antes de escribir código nuevo.

---

## Tabla de Contenidos

- [Nombres en Español](#nombres-en-español)
- [Pattern BaseComponent](#pattern-basecomponent)
- [Pattern Controlador](#pattern-controlador)
- [Pattern Modelos Pydantic](#pattern-modelos-pydantic)
- [Componentes UI](#componentes-ui--reglas-de-uso)
- [Design Tokens](#design-tokens--constantes-visuales)
- [Flags de Debug](#flags-de-debug)
- [Commits Conventional](#commits-conventional)
- [Resumen de Convenciones](#resumen-de-convenciones)

---

## Nombres en Español

El proyecto usa **español consistentemente** en nombres de archivos, clases, variables y funciones.

| Elemento | ✅ Correcto | ❌ Incorrecto |
|----------|-------------|---------------|
| Archivos | `controlador_hotel.py` | `hotel_controller.py` |
| Clases | `ControladorHotel` | `HotelController` |
| Funciones | `cargar_hoteles()` | `loadHotels()` |
| Variables | `estado_app` | `appState` |
| Constantes | `TIPOS_PERMITIDOS` | `allowedTypes` |

**Patrones de nombres**:
- Controladores: `Controlador` + Sustantivo → `ControladorHotel`
- Vistas/Componentes: Sustantivo + `Panel/Widget/Vista` → `PeriodosPanel`
- Modelos: Sustantivo + `Excel/Web` → `HabitacionExcel`
- snake_case en español para variables y funciones
- `UPPER_SNAKE_CASE` para constantes; env vars pueden ser en inglés

**Excepción**: `date_input.py` (legacy, se mantiene por compatibilidad)

---

## Pattern BaseComponent

Todos los componentes UI **DEBEN** heredar de `BaseComponent` e implementar los métodos obligatorios.

### Checklist de Implementación

- [ ] ✅ Hereda de `BaseComponent` (Qt: subclase de `QWidget`)
- [ ] ✅ Implementa `_setup_ui()` — construye la interfaz
- [ ] ✅ Implementa `get_value()` — retorna el valor actual
- [ ] ✅ Implementa `set_value(value)` — establece el valor
- [ ] ⚠️ Implementa `reset()` — opcional pero recomendado
- [ ] ⚠️ Implementa `_bind_events()` — si tiene eventos internos
- [ ] ✅ Guarda parámetros ANTES de llamar `super().__init__()`
- [ ] ✅ Tiene docstrings en clase y métodos públicos

Ver implementación de referencia: [UI_qt/widgets/qt_spin_stepper.py](../../Hoteles/UI_qt/widgets/qt_spin_stepper.py)

---

## Pattern Controlador

Los controladores **DEBEN** recibir `estado_app` y `event_bus` en el constructor y comunicarse exclusivamente a través de eventos.

### Checklist de Implementación

- [ ] ✅ Constructor recibe `estado_app` y `event_bus`
- [ ] ✅ Se suscribe a eventos en `__init__`
- [ ] ✅ Handlers tienen firma `handler(self, data)`
- [ ] ✅ Usa `event_bus.emit(evento, data)` para emitir
- [ ] ✅ Usa `event_bus.on(evento, callback)` para suscribirse
- [ ] ✅ NO importa módulos de UI (mantener desacoplado)
- [ ] ✅ Tiene docstrings en clase y métodos públicos

### Tabla de Eventos Comunes

| Evento | Emitido Por | Escuchado Por | Data |
|--------|-------------|---------------|------|
| `hotel_changed` | AppState (trace) | ControladorHotel | `str` |
| `edificio_changed` | AppState (trace) | ControladorHotel | `str` |
| `habitacion_changed` | AppState (trace) | ControladorPrecios | `str` |
| `comparison_started` | ControladorComparacion | InterfazApp | `None` |
| `comparison_completed` | ControladorComparacion | InterfazApp | `ResultadoComparacionMultiperiodo` |
| `comparison_error` | ControladorComparacion | InterfazApp | `str` |
| `hotel_cargado` | ControladorHotel | InterfazApp | `dict {hotel, tiene_tipos}` |
| `habitaciones_cargadas` | ControladorHotel | InterfazApp | `list[str]` |
| `precios_actualizados` | ControladorPrecios | InterfazApp | `dict` |

---

## Pattern Modelos Pydantic

Los modelos usan Pydantic v2 para validación de datos.

### Checklist de Implementación

- [ ] ✅ Hereda de `BaseModel`
- [ ] ✅ Usa type hints en todos los campos
- [ ] ✅ Usa `Optional[T]` para campos opcionales
- [ ] ✅ Usa `Field(default_factory=...)` para valores mutables (list, dict, set)
- [ ] ✅ Usa `Field(init=False)` para campos auto-calculados
- [ ] ✅ Usa `@field_validator` para validación por campo
- [ ] ✅ Usa `@model_validator(mode="after")` para validación global

### Ejemplo: HabitacionExcel

```python
class HabitacionExcel(BaseModel):
    nombre: str
    precio: Optional[Union[float, str]] = None
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
        if v in ["closing agreement", "on request"]:
            return v
        valor = normalizar_precio_str(v)
        if valor is None:
            raise ValueError(f"Precio inválido: '{v}'")
        return valor

    @model_validator(mode="after")
    def validar_coherencia(self):
        if isinstance(self.precio, str):
            self.precio_string = self.precio
            self.precio = None
        return self
```

---

## Componentes UI — Reglas de Uso

### Visibilidad dinámica: mostrar() / ocultar()

Si un componente puede aparecer y desaparecer en runtime sin ocupar espacio, encapsular la lógica en el propio componente:

```python
# ✅ Correcto — el componente encapsula su visibilidad
class MiWidget(QWidget):
    def mostrar(self):
        self.show()

    def ocultar(self):
        self.hide()

# En la interfaz — solo métodos semánticos
self.panel.mostrar()
self.panel.ocultar()

# ❌ Incorrecto — la interfaz maneja la visibilidad directamente
self.panel.show()
self.panel.hide()
```

**Razón**: el componente es autónomo; la interfaz solo llama métodos semánticos.

> Problemas visuales de Qt: [docs/ui/troubleshooting-qt.md](../ui/troubleshooting-qt.md)

### Listas de opciones UI

Usar **siempre** `QComboBox` con el stylesheet de `UI_qt/styles/`. No crear dropdowns custom ad-hoc.

### Estilos de Botones

No hardcodear colores inline. Usar `objectName` + QSS en `UI_qt/styles/stylesheet.py`.

```python
# ✅ Correcto — clase CSS definida en stylesheet.py
boton.setObjectName("primaryButton")

# ❌ Incorrecto — color hardcodeado
boton.setStyleSheet("background-color: #2563EB;")
```

---

## Design Tokens — Constantes Visuales

**Regla**: ningún widget, componente ni stylesheet hardcodea valores visuales (px, colores, tamaños) directamente. Todo va en el archivo de constantes del layer Qt.

```python
# ✅ Correcto
from UI_qt.styles.constants import HEADER_HEIGHT
from UI_qt.styles.palette import APP_ICON_TINT
header.setFixedHeight(HEADER_HEIGHT)

# ❌ Incorrecto
header.setFixedHeight(60)
p.fillRect(rect, "#DDD5C8")
```

### Mapa de archivos (layer Qt)

| Tipo | Archivo |
|------|---------|
| Colores / paleta (varía por tema) | `UI_qt/styles/palette.py` |
| Tamaños / ícono (fijos) | `UI_qt/styles/constants.py` |
| QSS stylesheet | `UI_qt/styles/stylesheet.py` |

**`palette.py`** — tokens de color por tema:
```python
LIGHT = Palette(bg="#E2E8F0", header_bg="#1E293B", ...)
DARK  = Palette(bg="#0F172A", header_bg="#0B1220", ...)
```

**`constants.py`** — tamaños que no varían por tema:
```python
HEADER_HEIGHT = 60
BUTTON_HEIGHT_PRIMARY = 44
APP_ICON_TINT = "#DDD5C8"
```

**`stylesheet.py`** — solo `build_qss()`, importa de los dos anteriores. Sin literales hardcodeados.

### ¿Cuándo NO hace falta una constante?

- Valores de una sola ocurrencia sin significado semántico (ej: `margin: 2px` en un ítem puntual)
- Paddings de layout muy locales que no se repiten

Ante la duda: **si el valor es un tamaño de widget, altura, color o tamaño de ícono → va en constantes**.

---

## Flags de Debug

Todos los flags se centralizan en `Hoteles/debug_config.py`. Nunca declarar flags locales en módulos.

### Convención de nombres

```
DEBUG_<AREA>_<DETALLE>
```

El nombre describe **qué loguea**, no dónde se usa.

| ✅ Correcto | ❌ Incorrecto | Por qué |
|-------------|---------------|---------|
| `DEBUG_FUZZY_MATCHING` | `DEBUG_HABITACIONES_WEB` | Describe el algoritmo, no el módulo |
| `DEBUG_EXCEL_PARSING` | `DEBUG_EXTRACTOR` | Describe qué se parsea, no la carpeta |
| `DEBUG_CRAWL4AI_VERBOSE` | `DEBUG_SCRAPER` | Aclara que es el verbose interno de Crawl4AI |

### Flags actuales

| Flag | Default | Qué loguea |
|------|---------|-----------|
| `DEBUG_SCRAPING_PIPELINE` | `True` | Pipeline en 3 niveles (L1-Crawl / L2-Markdown / L3-Groq) en `scraper_utils.py` |
| `DEBUG_LLM_MARKDOWN` | `False` | Guarda `debug_llm_input_*.txt` con el markdown enviado a Groq |
| `DEBUG_CRAWL4AI_VERBOSE` | `False` | `verbose=True` interno de Crawl4AI + prints de cache/pickle en `gestor_datos.py` |
| `DEBUG_FUZZY_MATCHING` | `False` | Fuzzy matching Excel↔Web en `comparador.py` y `gestor_datos.py` |
| `DEBUG_EXCEL_PARSING` | `False` | Parseo de fechas y nombres en `ExtractorDatos/utils.py` |

```python
# ✅ Correcto
from debug_config import DEBUG_FUZZY_MATCHING
if DEBUG_FUZZY_MATCHING:
    print(f"  Score: {score:.2f}")

# ❌ Incorrecto
DEBUG = True  # ¿qué loguea? ¿dónde más se usa?
```

> Ver cuándo activar cada flag: [debugging.md](debugging.md)

---

## Commits Conventional

El proyecto usa **Conventional Commits en español** con Co-Authored-By automático.

### Formato

```
<tipo>(<scope>): <mensaje corto>

<descripción detallada opcional>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Tipos Permitidos

| Tipo | Descripción |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `style` | Cambios visuales/UI |
| `refactor` | Reestructuración de código |
| `test` | Agregado/modificación de tests |
| `docs` | Documentación |
| `chore` | Tareas de mantenimiento |

**Reglas**: < 70 caracteres, sin punto final, en español. Scope opcional (ui, core, scraper, etc.).

Ver skill `/commit-custom` en [/.claude/skills/](../../.claude/skills/)

---

## Resumen de Convenciones

| Aspecto | Convención | ✅ | ❌ |
|---------|-----------|----|----|
| Archivos | `snake_case` español | `controlador_hotel.py` | `hotel_controller.py` |
| Clases | `PascalCase` español | `ControladorHotel` | `HotelController` |
| Funciones | `snake_case` español | `cargar_hoteles()` | `loadHotels()` |
| Variables | `snake_case` español | `estado_app` | `appState` |
| Constantes | `UPPER_SNAKE_CASE` | `TIPOS_PERMITIDOS` | `allowedTypes` |
| Privados | `_snake_case` | `_setup_ui()` | `setupUI()` |
| Componentes | Heredan `BaseComponent` | `class MiComp(BaseComponent)` | `class MiComp(QWidget)` directamente |
| Controladores | Constructor `(estado_app, event_bus)` | ✅ | sin `event_bus` |
| Modelos | Heredan `BaseModel` (Pydantic) | `class HotelExcel(BaseModel)` | `class HotelExcel` |
| Tokens visuales | Constantes en `UI_qt/styles/` | `HEADER_HEIGHT` | `60` hardcodeado |
| Commits | Conventional en español | `feat: nueva funcionalidad` | `Add new feature` |

---

**Herramientas**:
- Skill `/check-conventions` — valida estas convenciones
- Skill `/commit-custom` — facilita commits con formato correcto

Ver skills en [/.claude/skills/](../../.claude/skills/)
