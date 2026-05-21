# Feature: Selección de Excel + Validaciones desacopladas + Modal de configuración

> **Estado:** ✅ Implementado. Branch: `customTkinter`. Última actualización: 2026-05-21.

Este documento describe la feature tal como quedó implementada. Si vas a tocar
algo del flujo de carga del Excel, de validaciones, o de la topbar/modal de
configuración, leelo antes de meterte.

---

## Context

Antes:

- El path del Excel estaba hardcodeado en `Hoteles/Core/controller.py`
  (`_excel_path()` apuntaba a `Data/Extracto_prueba2.xlsx`) y `GestorDatos` se
  instanciaba a nivel de módulo (`gestor = GestorDatos(_excel_path())`). El
  usuario final del `.exe` no podía cambiar el archivo de datos sin recompilar.
- El `ControladorValidacion` ([Hoteles/UI/controllers/controlador_validacion.py](../../Hoteles/UI/controllers/controlador_validacion.py))
  mezclaba validación con presentación (`messagebox.showerror` adentro),
  devolvía `bool` (solo mostraba el primer error) y agregar validaciones
  nuevas exigía tocar el método central `validar_todo()`.

Outcome alcanzado:

1. ✅ El usuario selecciona cualquier `.xlsx` desde la topbar (file picker), la
   app recuerda el último usado en `config.json`.
2. ✅ Las validaciones siguen el patrón **Validator + ValidationResult**.
   Agregar uno nuevo es crear una clase sin tocar las existentes; el messagebox
   muestra **todos los errores juntos**.
3. ✅ Topbar con indicador del Excel siempre visible + botón **⚙** que abre un
   modal con `CTkTabview` de 4 pestañas (General + 3 placeholders).

Decisiones tomadas con el usuario:

| # | Decisión |
|---|----------|
| 1 | `config.json` vive **separado del `.exe`**: `%APPDATA%/CrawlCompare/config.json` (Windows .exe), `~/.config/CrawlCompare/config.json` (otros .exe) o `Hoteles/config.json` (modo dev). |
| 2 | El orquestador (`ControladorComparacion`) decide cómo mostrar los errores. Los validators son puros. Como el comparador corre en un daemon thread, emite un evento `validation_failed` que la UI escucha en el main thread. |
| 3 | El botón "Ejecutar Comparación" se **deshabilita** cuando no hay Excel cargado. `ExcelCargadoValidator` queda como red de seguridad defensiva. |

---

## Parte 1 — Carga del Excel

### 1.1. Diagrama de flujo

```
┌─────────────────────────────────────────────────────────────────────┐
│ APP ARRANCA  (CrawlCompareGUI.__init__)                             │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ConfigService()                                                     │
│ → Lee config.json del directorio adecuado (APPDATA / XDG / dev)     │
│ → Cachea en memoria; cualquier set() persiste a disco               │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ resolver_excel_inicial(config_service)                              │
│                                                                     │
│ 1. ¿config["last_excel_path"] existe en disco?  → ese path          │
│    Si el path está pero el archivo no, limpia el config.            │
│ 2. ¿Hay algún .xlsx en ./Data/ junto al .exe/script? → ese path     │
│ 3. → None                                                           │
└─────────────────────────────────────────────────────────────────────┘
   │
   ├──── path encontrado ────────────────────────────────────────┐
   │                                                              │
   ▼                                                              ▼
┌────────────────────────────────┐         ┌─────────────────────────────┐
│ GestorService.cargar(path)     │         │ Sin Excel cargado           │
│ → Crea GestorDatos(path)       │         │                             │
│ → Si OK:                       │         │ → Topbar: "📁 Sin Excel     │
│   - config.set_last_excel_path │         │    cargado" (rojo)          │
│ → Si error:                    │         │ → btn_ejecutar: disabled    │
│   - Path + mensaje en          │         │                             │
│     _error_excel_inicial       │         │                             │
│   - Diferido: messagebox       │         │                             │
│     después de armar la UI     │         │                             │
└────────────────────────────────┘         └─────────────────────────────┘
   │                                                              │
   └──────────────────────────────┬───────────────────────────────┘
                                  ▼
                  ┌───────────────────────────────────┐
                  │ UI completa cargada y funcional   │
                  │ Topbar: label_excel + Cambiar + ⚙ │
                  └───────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
                  EVENTO: Usuario clickea "Cambiar" en topbar
═══════════════════════════════════════════════════════════════════════
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ filedialog.askopenfilename(filetypes=[("Archivos Excel","*.xlsx")…])│
│ initialdir = parent del Excel actual, o Path.home() si no hay       │
└─────────────────────────────────────────────────────────────────────┘
   │
   ├── canceló ──→ no hacer nada
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ GestorService.cargar(nuevo_path)                                    │
│ → Si OK:                                                            │
│   - config_service.set_last_excel_path(nuevo_path)                  │
│   - _actualizar_label_excel(path)                                   │
│   - btn_ejecutar.configure(state="normal")                          │
│   - event_bus.emit("excel.loaded", {"path": …, "nombre": …})        │
│ → Si error:                                                         │
│   - messagebox.showerror(…)                                         │
│   - GestorService mantiene el Excel anterior intacto                │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ControladorHotel.on_excel_loaded (suscriptor de "excel.loaded")     │
│ → Limpia state.hotel, edificio, habitacion                          │
│ → state.habitaciones_unificadas = []                                │
│ → cargar_hoteles() repuebla desde GestorService.get()               │
│ → event_bus.emit("hoteles_recargados", nombres)                     │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CrawlCompareGUI._on_hoteles_recargados (main thread vía root.after) │
│ → hotel_combo.set_values(nombres)                                   │
│ → Limpia selecciones, oculta edificio si estaba visible             │
│ → periodos_panel.limpiar()                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2. Ubicación de `config.json`

[Hoteles/Core/services/config_service.py](../../Hoteles/Core/services/config_service.py):

```python
def _config_dir() -> Path:
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "CrawlCompare"
    return Path(__file__).parent.parent.parent  # Hoteles/
```

**Por qué `%APPDATA%` y no junto al `.exe`:**
- Persistente entre actualizaciones del binario: si el usuario reemplaza el `.exe`, la config sobrevive.
- En `.exe` empaquetado con PyInstaller, `sys._MEIPASS` es read-only y se borra al cerrar. No sirve para escribir.
- `%APPDATA%` es el estándar de Windows para configuración por-usuario.

**Modo dev:** el archivo cae en `Hoteles/config.json` (y está en `.gitignore`).

### 1.3. `ConfigService` — API

Clase en [Hoteles/Core/services/config_service.py](../../Hoteles/Core/services/config_service.py).

```python
config = ConfigService()
config.get_last_excel_path()           # Optional[str]
config.set_last_excel_path(path)        # str → persiste a disco
config.set_last_excel_path(None)        # Limpia la clave del JSON
config.get("user_email", default=None)  # API genérica para futuras claves
config.set("user_email", "x@y.com")
```

**Decisiones implementadas:**

- `_guardar()` se llama en cada `set()` — no perdemos cambios si la app crashea.
- Cache en memoria (`self._cache`) para evitar leer disco en cada `get()`.
- Errores de IO se loggean a stdout pero **NO se propagan** — si el disco está lleno o hay permisos raros, la app sigue funcionando con la config en memoria.
- `set(key, None)` elimina la clave del JSON (no la guarda como `null`). Esto sirve para limpiar paths fantasma.
- `ConfigService.path` expone el path absoluto del JSON (lo usa el modal para mostrarle al usuario dónde está su config).
- Sin pickle: JSON es legible y el usuario podría querer inspeccionar/editar el archivo manualmente.

### 1.4. `excel_resolver.py` — auto-detección del Excel inicial

[Hoteles/Core/excel_resolver.py](../../Hoteles/Core/excel_resolver.py):

```python
def resolver_excel_inicial(config: ConfigService) -> Optional[str]:
    # 1. Último Excel usado
    last_path_str = config.get_last_excel_path()
    if last_path_str:
        last_path = Path(last_path_str)
        if last_path.is_file():
            return str(last_path)
        # Archivo fantasma: limpiamos para no reintentar siempre
        print(f"[excel_resolver] Último Excel ({last_path}) ya no existe. Limpiando config.")
        config.set_last_excel_path(None)

    # 2. Fallback: ./Data/*.xlsx
    data_dir = _data_dir()
    if data_dir.is_dir():
        xlsx_files = sorted(data_dir.glob("*.xlsx"))
        if xlsx_files:
            return str(xlsx_files[0])

    # 3. Nada encontrado
    return None
```

### 1.5. `GestorService` — singleton recargable

[Hoteles/Core/controller.py](../../Hoteles/Core/controller.py):

```python
class GestorService:
    """Singleton recargable del GestorDatos.

    Reemplaza la instancia global `gestor` para permitir cambiar el Excel
    en runtime. Si la recarga falla, la instancia previa queda intacta
    (la asignación a `_instance` sólo ocurre si el constructor no lanza).

    Quien necesite el gestor debe llamar a ``GestorService.get()`` en el
    momento de uso, NO importar la instancia (eso traería stale references).
    """

    _instance: Optional[GestorDatos] = None
    _current_path: Optional[str] = None

    @classmethod
    def cargar(cls, path: str) -> GestorDatos:
        nuevo = GestorDatos(path)         # si falla, _instance queda intacta
        cls._instance = nuevo
        cls._current_path = path
        return nuevo

    @classmethod
    def get(cls) -> Optional[GestorDatos]: return cls._instance

    @classmethod
    def get_current_path(cls) -> Optional[str]: return cls._current_path

    @classmethod
    def esta_cargado(cls) -> bool: return cls._instance is not None

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._current_path = None
```

**Atomicidad ante fallo:** la línea `cls._instance = nuevo` SOLO se ejecuta si la línea anterior (`GestorDatos(path)`) no lanzó excepción. Si el Excel nuevo está corrupto, el viejo queda intacto. Esto se demostró en el smoke test.

**Regla de uso:** nunca hacer `from Core.controller import gestor` (no existe más). Siempre `GestorService.get()` en el momento de uso. Esto evita stale references descritas en la conversación.

### 1.6. Funciones legacy defensivas

Todas las funciones públicas de `controller.py` (`dar_hoteles_excel`, `dar_habitaciones_excel`, `dar_tipos_habitacion_excel`, `dar_habitacion_web`, `dar_mensaje`) se mantienen para compatibilidad con código existente (UI, tests, scripts), pero ahora son defensivas:

```python
def dar_hoteles_excel():
    g = GestorService.get()
    if g is None:
        return []           # Sin Excel cargado → lista vacía
    return g.hoteles_excel_get
```

Las funciones async (`comparar_habitaciones`, `dar_hotel_web`) lanzan `RuntimeError("No hay archivo Excel cargado.")` si se las llama sin Excel — esto NO debería pasar porque la UI deshabilita el botón Ejecutar y el `ExcelCargadoValidator` corta el flujo antes, pero queda como guard final.

**Eliminado:** la función `_excel_path()` ya no existe — su lógica frozen/dev se movió a `excel_resolver._data_dir()`.

### 1.7. Integración en el arranque (`interfaz_ctk.py.__init__`)

```python
# Config + carga inicial del Excel.
# GestorService.cargar puede fallar (Excel corrupto) — diferimos el
# mensaje hasta que la UI esté armada para mostrarlo con messagebox.
self.config_service = ConfigService()
self._error_excel_inicial = None
excel_path = resolver_excel_inicial(self.config_service)
if excel_path:
    try:
        GestorService.cargar(excel_path)
        self.config_service.set_last_excel_path(excel_path)
        print(f"[startup] Excel cargado: {excel_path}")
    except Exception as e:
        print(f"[startup] Error cargando Excel inicial: {e}")
        self._error_excel_inicial = (excel_path, str(e))
else:
    print("[startup] Sin Excel — arranque vacío.")

# ... resto del init (controladores, UI) ...

# Si no quedó un Excel cargado, ajustamos la UI a "modo vacío".
if not GestorService.esta_cargado():
    self._aplicar_modo_sin_excel()
else:
    self._actualizar_label_excel(GestorService.get_current_path())

# Mostrar error diferido después de pintar la UI
if self._error_excel_inicial:
    path, err = self._error_excel_inicial
    self.root.after(100, lambda: messagebox.showerror(
        "Error cargando Excel",
        f"No se pudo cargar el archivo configurado:\n{path}\n\n"
        f"Detalle: {err}\n\n"
        "Seleccioná un archivo Excel desde la barra superior."
    ))
```

### 1.8. Callback "Cambiar Excel"

```python
def _on_cambiar_excel(self):
    current = GestorService.get_current_path()
    initialdir = str(Path(current).parent) if current else str(Path.home())

    path = filedialog.askopenfilename(
        title="Seleccionar archivo Excel",
        filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
        initialdir=initialdir,
    )
    if not path:
        return

    try:
        GestorService.cargar(path)
    except Exception as e:
        messagebox.showerror(
            "Error al cargar Excel",
            f"No se pudo cargar el archivo:\n{path}\n\nDetalle: {e}"
        )
        return  # mantiene el Excel anterior

    self.config_service.set_last_excel_path(path)
    self._actualizar_label_excel(path)
    self.btn_ejecutar.configure(state="normal")
    self.event_bus.emit('excel.loaded', {
        'path': path,
        'nombre': Path(path).name,
    })

def _actualizar_label_excel(self, path):
    if path is None:
        self.label_excel.configure(text="📁 Sin Excel cargado", text_color=Colors.ERROR)
    else:
        nombre = Path(path).name
        display = nombre if len(nombre) <= 30 else nombre[:27] + "..."
        self.label_excel.configure(text=f"📁 {display}", text_color=Colors.HEADER_TEXT)
```

### 1.9. Refresco de combos al cambiar Excel

[ControladorHotel.on_excel_loaded](../../Hoteles/UI/controllers/controlador_hotel.py):

```python
def on_excel_loaded(self, payload=None):
    # Limpiar selecciones: el Excel anterior ya no aplica.
    try:
        self.estado_app.hotel.set("")
        self.estado_app.edificio.set("")
        self.estado_app.habitacion.set("")
    except Exception:
        pass

    self.estado_app.habitaciones_unificadas = []
    self.estado_app.habitaciones_excel = []

    nombres = self.cargar_hoteles()
    self.event_bus.emit('hoteles_recargados', nombres)
```

La UI (`interfaz_ctk._on_hoteles_recargados`) escucha y refresca el combo en el main thread con `root.after(0, …)`.

> **Nota sobre nomenclatura:** se usó `hoteles_recargados` (snake_case) en vez de `hoteles.updated` (dot-notation) para mantener consistencia con los demás eventos del EventBus que ya estaban con snake_case (`hotel_changed`, `comparison_started`, etc.).

---

## Parte 2 — Validaciones desacopladas

### 2.1. Estructura

```
Hoteles/UI/controllers/
├── controlador_validacion.py     # Orquestador puro (devuelve ValidationResult)
└── validators/
    ├── __init__.py               # Re-exporta tipos y validators
    ├── base.py                   # ValidationError, ValidationResult, Validator
    ├── fechas_validator.py       # Formato + no-pasado + orden
    ├── campos_validator.py       # Campos no vacíos, adultos ≥ 1
    └── excel_validator.py        # Red de seguridad defensiva
```

### 2.2. Tipos base ([validators/base.py](../../Hoteles/UI/controllers/validators/base.py))

```python
@dataclass
class ValidationError:
    campo: str                      # "fecha_entrada", "excel", "adultos"
    mensaje: str                    # human-readable
    severity: str = "error"         # "error" | "warning"

@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    def merge(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)

    def mensajes_concatenados(self) -> str:
        return "\n".join(f"• {e.mensaje}" for e in self.errors)

class Validator(Protocol):
    def validate(self, state) -> ValidationResult: ...
```

### 2.3. Validators concretos

**[fechas_validator.py](../../Hoteles/UI/controllers/validators/fechas_validator.py)**

Si la fecha está vacía, **no agrega error** acá — eso lo reporta `CamposValidator` y evitamos duplicación. Solo agrega errores si la fecha tiene contenido pero el formato es inválido o está en el pasado.

**[campos_validator.py](../../Hoteles/UI/controllers/validators/campos_validator.py)**

Recorre la lista `CAMPOS` y verifica cada campo contra `VACIOS = ("", None, "(ninguna seleccionada)")`. Caso especial para `adultos`: además de no-vacío, debe ser numérico y ≥ 1.

**[excel_validator.py](../../Hoteles/UI/controllers/validators/excel_validator.py)** — red de seguridad:

```python
class ExcelCargadoValidator:
    def validate(self, state) -> ValidationResult:
        result = ValidationResult()
        if not GestorService.esta_cargado():
            result.errors.append(ValidationError(
                campo="excel",
                mensaje=(
                    "No hay archivo Excel cargado. Seleccioná uno desde "
                    "la barra superior."
                ),
            ))
        return result
```

### 2.4. `ControladorValidacion` refactorizado

[controlador_validacion.py](../../Hoteles/UI/controllers/controlador_validacion.py):

```python
class ControladorValidacion:
    def __init__(self, estado_app, validators: Optional[list[Validator]] = None):
        self.estado_app = estado_app
        # Orden importante: Excel primero (si falta, lo demás no tiene sentido),
        # después campos, después fechas (que asume campos completos).
        self._validators: list[Validator] = validators or [
            ExcelCargadoValidator(),
            CamposValidator(),
            FechasValidator(),
        ]

    def validar_todo(self) -> ValidationResult:
        result = ValidationResult()
        for v in self._validators:
            result.merge(v.validate(self.estado_app))
        return result
```

**Cambio de contrato:** ya no devuelve `bool` sino `ValidationResult`. Sin `messagebox` adentro — quien llama decide cómo presentar.

### 2.5. `ControladorComparacion` y el evento `validation_failed`

El comparador corre en un daemon thread (`threading.Thread(target=self._run_async, daemon=True)`). Como `tkinter.messagebox.showerror()` desde un thread no-main puede comportarse de forma inestable en Tk, el orquestador emite un evento que la UI escucha en el main thread:

```python
# controlador_comparacion.py
async def _ejecutar_comparacion(self):
    try:
        # Validar PRIMERO — antes de tocar la UI con comparison_started.
        result = self.controlador_validacion.validar_todo()
        if not result.is_valid:
            self.event_bus.emit('validation_failed', {
                'mensajes': result.mensajes_concatenados(),
                'errors': result.errors,
            })
            return

        self.event_bus.emit('comparison_started')
        # ... resto del flujo
```

```python
# interfaz_ctk.py
def _on_validation_failed(self, data):
    mensajes = data.get('mensajes', '') if isinstance(data, dict) else str(data)
    def _mostrar():
        messagebox.showerror(
            "Datos incompletos o inválidos",
            "Revisá los siguientes campos:\n\n" + mensajes,
        )
    self.root.after(0, _mostrar)
```

**Beneficio inmediato:** el messagebox lista TODOS los errores juntos (7 en el smoke test con AppState vacío), no solo el primero.

**Beneficio futuro:** si mañana se cambia la UX de error (panel inline, badges rojos, toast), se toca SOLO el handler `_on_validation_failed`. Los validators no se enteran.

> **Diferencia con el plan original:** el plan inicial proponía que `ControladorComparacion` llamara `messagebox.showerror()` directamente. Durante la implementación se detectó que ese controlador corre en un daemon thread, y la presentación se delegó al main thread vía evento `validation_failed`. La separación validators-puros → orquestador → UI se mantiene; solo cambia la mecánica de paso.

### 2.6. Validar antes de `comparison_started`

El plan original validaba después de `comparison_started`. Durante la implementación se reordenó para validar PRIMERO. Razón: si `comparison_started` ya se emitió, la UI cambia el layout (panel de progreso, botón disabled) y después hay que revertir todo. Validar antes evita ese roundtrip.

---

## Parte 3 — UI: topbar + modal

### 3.1. Topbar actualizada

[interfaz_ctk.py._crear_header()](../../Hoteles/UI/interfaz_ctk.py):

Layout final:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Crawl-Compare - Comparador…  │  📁 Extracto.xlsx  [Cambiar]   [⚙]   │
└──────────────────────────────────────────────────────────────────────┘
   pack(side="left")             pack(side="right") en orden inverso
```

Atributos guardados en `self`: `label_excel`, `btn_cambiar_excel`, `btn_config`.

El label cambia de color a `Colors.ERROR` (rojo) cuando no hay Excel cargado.
Si el nombre del archivo supera 30 caracteres se trunca con `…` para no
desbordar.

### 3.2. Modal de configuración

[Hoteles/UI/views/config_modal.py](../../Hoteles/UI/views/config_modal.py):

`CTkToplevel` modal (con `grab_set()`) que contiene un `CTkTabview` de 4 pestañas:

- **General** — info del Excel actual + path del config.json (para que el usuario sepa dónde está su configuración persistida)
- **Email** — placeholder ("Próximamente: configuración del email del usuario…")
- **API Keys** — placeholder
- **Scraping** — placeholder

El modal se centra sobre la ventana parent vía `_centrar()` (con `after(50)` para que `winfo_width/height` ya estén calculados).

### 3.3. Handler del botón ⚙ (single-instance)

```python
def _abrir_modal_config(self):
    existente = getattr(self, "_modal_config", None)
    if existente is not None:
        try:
            if existente.winfo_exists():
                existente.lift()
                existente.focus_force()
                return
        except Exception:
            pass
    self._modal_config = ConfigModal(self.root, self.config_service)
```

Doble click en ⚙ no abre dos modales — trae el existente al frente.

---

## Archivos creados / modificados

**Creados:**

- `Hoteles/Core/services/__init__.py`
- [Hoteles/Core/services/config_service.py](../../Hoteles/Core/services/config_service.py)
- [Hoteles/Core/excel_resolver.py](../../Hoteles/Core/excel_resolver.py)
- `Hoteles/UI/controllers/validators/__init__.py`
- [Hoteles/UI/controllers/validators/base.py](../../Hoteles/UI/controllers/validators/base.py)
- [Hoteles/UI/controllers/validators/fechas_validator.py](../../Hoteles/UI/controllers/validators/fechas_validator.py)
- [Hoteles/UI/controllers/validators/campos_validator.py](../../Hoteles/UI/controllers/validators/campos_validator.py)
- [Hoteles/UI/controllers/validators/excel_validator.py](../../Hoteles/UI/controllers/validators/excel_validator.py)
- [Hoteles/UI/views/config_modal.py](../../Hoteles/UI/views/config_modal.py)

**Modificados:**

- [Hoteles/Core/controller.py](../../Hoteles/Core/controller.py) — eliminado `_excel_path()` y global `gestor`; agregado `GestorService`; funciones legacy defensivas.
- [Hoteles/UI/controllers/controlador_validacion.py](../../Hoteles/UI/controllers/controlador_validacion.py) — refactor completo.
- [Hoteles/UI/controllers/controlador_comparacion.py](../../Hoteles/UI/controllers/controlador_comparacion.py) — emite `validation_failed` con `ValidationResult`.
- [Hoteles/UI/controllers/controlador_hotel.py](../../Hoteles/UI/controllers/controlador_hotel.py) — `on_excel_loaded()`.
- [Hoteles/UI/interfaz_ctk.py](../../Hoteles/UI/interfaz_ctk.py) — `__init__` con `ConfigService` + resolver; nuevo `_crear_header()`; métodos `_on_cambiar_excel`, `_actualizar_label_excel`, `_abrir_modal_config`, `_aplicar_modo_sin_excel`; handlers `_on_validation_failed`, `_on_hoteles_recargados`.
- [Hoteles/UI/views/__init__.py](../../Hoteles/UI/views/__init__.py) — exporta `ConfigModal`.
- [.gitignore](../../.gitignore) — agregado `Hoteles/config.json` (cae acá en modo dev).
- [docs/arquitectura/tree-directory.md](../arquitectura/tree-directory.md), [docs/ui/controladores.md](../ui/controladores.md), [docs/README.md](../README.md) — actualizados.

---

## Eventos del EventBus involucrados

| Evento | Emisor | Suscriptores | Payload |
|--------|--------|--------------|---------|
| `excel.loaded` | `interfaz_ctk._on_cambiar_excel` | `ControladorHotel.on_excel_loaded` | `{"path": str, "nombre": str}` |
| `hoteles_recargados` | `ControladorHotel.on_excel_loaded` | `interfaz_ctk._on_hoteles_recargados` | `list[str]` (nombres de hoteles) |
| `validation_failed` | `ControladorComparacion._ejecutar_comparacion` | `interfaz_ctk._on_validation_failed` | `{"mensajes": str, "errors": list[ValidationError]}` |

---

## Smoke tests ejecutados durante la implementación

Todos pasaron OK. Para reproducir:

```bash
cd Hoteles

# 1. Sintaxis y referencias residuales a 'gestor' global
python -c "
import ast
for f in ['Core/controller.py','UI/controllers/controlador_comparacion.py','UI/controllers/controlador_hotel.py','UI/interfaz_ctk.py']:
    tree = ast.parse(open(f, encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == 'gestor' and isinstance(node.ctx, ast.Load):
            raise AssertionError(f'referencia residual en {f}:{node.lineno}')
print('OK: sin referencias residuales a gestor global')
"

# 2. Validación devuelve TODOS los errores juntos (no solo el primero)
python -c "
from UI.controllers.controlador_validacion import ControladorValidacion
class FakeVar:
    def __init__(self, v=''): self.v = v
    def get(self): return self.v
class FakeState:
    def __init__(self):
        for attr in ['fecha_entrada_completa','fecha_salida_completa','adultos','ninos','habitacion','precio']:
            setattr(self, attr, FakeVar(''))
        self.adultos = FakeVar('0')
result = ControladorValidacion(FakeState()).validar_todo()
assert not result.is_valid
assert len(result.errors) >= 4, f'esperaba >=4 errores, hay {len(result.errors)}'
print(f'OK: {len(result.errors)} errores acumulados')
"

# 3. GestorService defensivo (sin Excel → no crashea)
python -c "
from Core.controller import GestorService, dar_hoteles_excel, dar_habitacion_web, dar_mensaje
GestorService.reset()
assert dar_hoteles_excel() == []
assert dar_habitacion_web() is None
assert dar_mensaje() is None
print('OK: funciones defensivas sin Excel devuelven vacío/None sin excepción')
"

# 4. ConfigService persiste y excel_resolver maneja paths fantasma
python -c "
import os, tempfile
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='cc_test_')
from Core.services import ConfigService
cs = ConfigService()
cs.set_last_excel_path('C:/fake/no_existe.xlsx')
cs2 = ConfigService()
assert cs2.get_last_excel_path() == 'C:/fake/no_existe.xlsx'
from Core.excel_resolver import resolver_excel_inicial
result = resolver_excel_inicial(cs2)
print(f'OK: path fantasma se limpia, fallback devuelve: {result}')
"
```

---

## Verificación manual end-to-end (golden path UI)

1. **Arrancar la app con Excel previo en config**: topbar muestra `📁 <nombre>.xlsx` y combo de hoteles poblado.
2. **Click en "Cambiar"** → file picker (abre en el dir del Excel actual) → seleccionar otro `.xlsx` → label se actualiza, combo de hoteles se re-puebla, botón Ejecutar habilitado.
3. **Cerrar y reabrir la app** → recuerda el último Excel.
4. **Borrar `config.json` + `Data/*.xlsx`, abrir** → topbar en rojo "📁 Sin Excel cargado", botón Ejecutar **deshabilitado**.
5. **Con campos vacíos, click en "Ejecutar"** → messagebox lista todos los errores juntos con bullet points.
6. **Click en "⚙"** → modal con 4 pestañas. "General" muestra el path actual del Excel y del config.json. Doble click en ⚙ NO abre dos modales.
7. **Seleccionar un `.xlsx` corrupto** → messagebox de error, Excel anterior queda cargado.
8. **Mover el Excel actual fuera de su carpeta, reiniciar app** → fallback a `Data/` o "Sin Excel cargado".

---

## Edge cases cubiertos

- **Excel corrupto**: `GestorDatos(path)` lanza, `_instance` no se sobrescribe, messagebox al usuario.
- **Excel movido externamente**: `excel_resolver` detecta y limpia el path del config para no reintentar en cada arranque.
- **Path con tildes/ñ**: usamos `Path` + `encoding="utf-8"` en `ConfigService`, debería funcionar en dev y `.exe`.
- **Doble click en ⚙**: chequeo con `winfo_exists()` previene segundo modal.
- **Validación desde daemon thread**: emisión de evento, presentación en main thread vía `root.after`.
- **Cancelar file picker**: `_on_cambiar_excel` retorna temprano sin tocar nada.

---

## Build del `.exe`

Para empaquetar la feature:

1. Correr [Hoteles/Deploy/build.bat](../../Hoteles/Deploy/build.bat).
2. Verificar que [Deploy/build_manifest.py](../../Hoteles/Deploy/build_manifest.py) incluya:
   - `Hoteles/Core/services/` (nuevo paquete)
   - `Hoteles/UI/controllers/validators/` (nuevo subpaquete)
   - `Hoteles/UI/views/config_modal.py`
3. El smoke test post-build ([Deploy/smoke_test.py](../../Hoteles/Deploy/smoke_test.py)) debe seguir pasando.
4. Ejecutar el `.exe` desde una carpeta limpia (sin `Data/`). Debe arrancar mostrando "Sin Excel cargado" sin crashear.
5. Cargar un Excel, cerrar el `.exe`, abrirlo de nuevo → debe recordar el Excel (lee de `%APPDATA%/CrawlCompare/config.json`).

---

## Lo que NO se hizo (intencionalmente, queda para iteraciones futuras)

- ❌ Contenido real de las pestañas "Email", "API Keys" y "Scraping" del modal — solo placeholders.
- ❌ Cambio en la UX de errores de validación — sigue siendo `messagebox`. La refactor preparó el terreno: cuando se quiera cambiar (panel inline, badges en campos, toast), se toca SOLO `_on_validation_failed`.
- ❌ Migración del legacy [UI/interfaz.py](../../Hoteles/UI/interfaz.py) (Tkinter) — solo `interfaz_ctk.py`.
- ❌ Validación profunda del contenido del Excel al cargarlo (estructura de columnas, hojas esperadas). Si está corrupto, `GestorDatos(path)` tira excepción y la atrapamos — eso suficiente. Validación profunda = otra feature.
- ❌ Tests automáticos en `Tests/` para `ConfigService`, `excel_resolver`, validators, `GestorService`. Los smoke tests de la sección anterior cubren los casos críticos manualmente.

---

## Cómo agregar configuraciones nuevas en el futuro

### Caso 1: una opción simple (ej: idioma)

1. Agregar getters al `ConfigService`:
   ```python
   def get_idioma(self) -> str:
       return self.get("idioma", default="es")
   def set_idioma(self, idioma: str) -> None:
       self.set("idioma", idioma)
   ```
2. Agregar contenido a la pestaña "General" o crear pestaña nueva en `ConfigModal`.

### Caso 2: una validación nueva (ej: email del usuario configurado)

1. Crear `Hoteles/UI/controllers/validators/email_validator.py`:
   ```python
   from Core.services import ConfigService
   from .base import ValidationError, ValidationResult

   class EmailConfiguradoValidator:
       def __init__(self, config_service: ConfigService):
           self._config = config_service

       def validate(self, state) -> ValidationResult:
           result = ValidationResult()
           if not self._config.get("user_email"):
               result.errors.append(ValidationError(
                   campo="email",
                   mensaje="Configurá un email en ⚙ → Email antes de comparar.",
                   severity="warning",  # o "error" si es bloqueante
               ))
           return result
   ```
2. Sumarlo a la lista en `ControladorValidacion.__init__` (o inyectarlo).
3. Listo. No se toca ningún otro archivo.

### Caso 3: nueva fuente de datos (ej: cargar también un CSV junto al Excel)

1. Espejar el patrón Excel: `CsvService`, `csv_resolver`, validator nuevo, integración en topbar/modal.
2. La estructura de `Core/services/` y `validators/` ya está preparada para este crecimiento.
