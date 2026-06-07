# Feature: Splash screen de arranque + Logging persistente en .exe

## Estado: PLANIFICADO 📝

Fecha de planificación: 2026-06-03
Branch sugerido: `feature/splash-logging`

---

## Contexto

La versión buildeada (`CrawlCompare.exe` generada por PyInstaller) tiene dos problemas operativos en producción:

1. **Pantalla negra muda durante el arranque.** El `.spec` actualmente declara `console=True`, por lo que al lanzar el .exe Windows abre una consola negra mientras `main.py` corre `run_checks()`, importa CTk y crea `CrawlCompareGUI`. El usuario no tiene feedback de que la app está cargando.

2. **Errores fatales se pierden sin rastro.** Si una excepción no manejada explota en producción, el traceback se va a la consola y muere al cerrarse la ventana. Cuando se distribuya con `console=False`, los errores serán completamente invisibles. Lo mismo con los `print()` condicionales de los flags de debug (`DEBUG_SCRAPING_PIPELINE`, `DEBUG_FUZZY_MATCHING`, etc.) en [debug_config.py](../../Hoteles/debug_config.py) — útiles para diagnosticar bugs en una máquina del usuario, pero hoy se pierden.

3. **El usuario final necesita logs operativos siempre activos.** Sin un log persistente de runtime (no solo de crashes), reportar un bug es a ciegas. Queremos que el `.exe` distribuido siempre escriba qué hizo el scraper, qué matcheó el fuzzy, qué Excel se cargó, etc., sin tener que rebuildear con flags distintos.

Esta feature resuelve los tres problemas con dos módulos nuevos en `Deploy/` (`splash.py` y `error_logger.py`) y un override automático de flags en `debug_config.py` cuando corre como `.exe`.

---

## Objetivos

### A — Splash screen con progreso

Mostrar una ventana de bienvenida pequeña, centrada, que informe en tiempo real qué paso del arranque se está ejecutando:

```
+--------------------------------------+
|                                      |
|         Crawl Compare                |
|   Comparador de Precios de Hoteles   |
|                                      |
|   Verificando configuración...       |
|   [████████████░░░░░░░░░░░░░░░]      |
|                                      |
+--------------------------------------+
```

Mensajes esperados durante el arranque:
- `"Verificando configuración..."`
- `"Verificando navegador..."`
- `"Iniciando interfaz..."`

La ventana se cierra automáticamente justo antes de instanciar `ctk.CTk()`.

### B — Logging persistente de errores y debug

1. Cualquier excepción no manejada se persiste automáticamente en un archivo `crawl_compare_YYYYMMDD.log` ubicado **junto al `.exe`** (no en `_MEIPASS`, que es temporal). Un `messagebox` simple informa al usuario que ocurrió un error y dónde encontrar el log.
2. En el `.exe`, un subconjunto de flags de debug se **fuerza a `True`** automáticamente, sin importar lo que diga el código fuente. Los `print()` de esos flags se loguean al mismo archivo, sin tocar ninguno de los 30+ sitios donde se llama a `print()`.
3. En desarrollo (sin `sys.frozen`) el comportamiento actual no cambia — los flags quedan tal como los configuraste en `debug_config.py`.

#### Flags forzados a `True` en `.exe`

| Flag | Por qué se fuerza |
|---|---|
| `DEBUG_SCRAPING_PIPELINE` | Diagnóstico #1 de fallas: success/error/HTML size/respuesta LLM/parseo JSON por intento. |
| `DEBUG_FUZZY_MATCHING` | Explica por qué una habitación matcheó o no con su par en la web. |
| `DEBUG_COMPARISON_PIPELINE` | Contexto completo: habitación, periodo, fechas calculadas, URL del scraper, JSON crudo. |
| `DEBUG_STARTUP_EXCEL_LOAD` | Problema #1 de configuración en el arranque. Costo despreciable (1-2 líneas por arranque). |
| `DEBUG_CRAWL4AI_VERBOSE` | Verbose interno de Crawl4AI (`[INIT]`, `[FETCH]`, `[SCRAPE]`) + cache/pickle. Ayuda a entender por qué un scrape se cayó dentro de la lib. |

#### Flags que quedan en `False` incluso en `.exe`

| Flag | Por qué NO se fuerza |
|---|---|
| `DEBUG_LLM_MARKDOWN` | Genera un `debug_llm_input_*.txt` **por cada intento de scrape**. En una sesión con 10 habitaciones × 3 periodos = 30 archivos sueltos en la carpeta del usuario. |
| `DEBUG_EXCEL_PARSING` | Muy verboso por cada fila parseada. El error final del parseo ya es visible sin este flag. |

---

## Orden de inicialización

El orden no es negociable — el logger debe estar activo antes de que cualquier otro código pueda fallar, incluido el splash:

```
[EXE arranca]
    │
    ▼
[1] error_logger.setup_error_logging()
       ├── sys.excepthook  → escribe traceback a archivo
       └── _TeeStream      → duplica stdout/stderr a archivo (si hay debug flags)
    │
    ▼
[2] splash = SplashScreen()        (solo en .exe)
    │
    ▼
[3] run_checks(on_progress=splash.update_status)
       ├── check_env()
       └── check_playwright()
    │
    ▼
[4] splash.close()                 → destruye Tk root para liberar el slot
    │
    ▼
[5] ctk.CTk() + CrawlCompareGUI    → app principal arranca normalmente
```

Justificación del orden:
- **Logger primero** porque si el splash falla (CTk mal bundleado, Tk no disponible), el crash debe quedar registrado.
- **Splash en el main thread** porque Tkinter/CTk no son thread-safe — todos los widgets deben crearse y operarse desde el mismo thread.
- **Checks notifican por callback** en vez de correr en thread separado, porque son rápidos (<1 seg en el caso normal) y el patrón `update()` manual de Tkinter ya cubre este caso sin bloquear.

---

## Archivos

### Nuevos

#### `Hoteles/Deploy/error_logger.py`

Responsabilidades:
- `_get_log_dir()` — devuelve `Path(sys.executable).parent` en .exe, `Hoteles/` en dev.
- `_TeeStream` — wrapper sobre un stream que escribe simultáneamente a destino original y archivo de log. Implementa `write`, `flush`, `encoding`, `errors` para ser compatible con `io.TextIOWrapper`.
- `_DummyStream` — stand-in cuando `sys.stdout is None` (caso `console=False`). Permite que el Tee siga capturando al archivo aunque la consola no exista.
- `setup_error_logging()` — instala `sys.excepthook` que vuelca traceback + timestamp al archivo, y opcionalmente envuelve stdout/stderr con `_TeeStream` si algún flag de `debug_config` está activo.

Esqueleto:

```python
import sys, traceback, datetime
from pathlib import Path

class _TeeStream:
    def __init__(self, original, log_path):
        self._orig = original
        self._log = open(log_path, "a", encoding="utf-8", buffering=1)
    def write(self, text):
        self._orig.write(text)
        self._log.write(text)
    def flush(self):
        self._orig.flush()
        self._log.flush()
    @property
    def encoding(self): return self._orig.encoding
    @property
    def errors(self): return self._orig.errors

class _DummyStream:
    def write(self, text): pass
    def flush(self): pass
    encoding = "utf-8"
    errors = "replace"

def _get_log_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent

def setup_error_logging():
    if not getattr(sys, "frozen", False):
        return  # En dev: no se toca nada

    log_path = _get_log_dir() / f"crawl_compare_{datetime.date.today():%Y%m%d}.log"

    # Los flags ya vienen forzados por el override de debug_config.py.
    # Acá solo envolvemos stdout/stderr para que los print() vayan al log también.
    sys.stdout = _TeeStream(sys.stdout or _DummyStream(), log_path)
    sys.stderr = _TeeStream(sys.stderr or _DummyStream(), log_path)

    def _excepthook(exc_type, exc_value, exc_tb):
        # 1. Persistir el traceback completo al log
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"{'='*60}\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)

        # 2. Avisar al usuario con un messagebox simple (tk puro, sin CTk)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Crawl Compare — Error inesperado",
                f"Ocurrió un error y la aplicación debe cerrarse.\n\n"
                f"Se guardó un log con los detalles en:\n{log_path}\n\n"
                f"Por favor envía ese archivo para diagnóstico."
            )
            root.destroy()
        except Exception:
            pass  # Si el messagebox falla, al menos el log ya está escrito

        # 3. Delegar al excepthook original (consola si existe)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
```

#### Modificación a `Hoteles/debug_config.py` (no es archivo nuevo, pero el cambio es central)

Al final del archivo se agrega un override automático que se ejecuta una sola vez, en el import inicial del módulo:

```python
# ============================================================
# Override automático en producción (.exe)
# ============================================================
# En el .exe queremos ciertos logs SIEMPRE activos, sin importar
# lo que diga el código fuente más arriba. Así, si el usuario reporta
# un bug, ya tenemos información del runtime en crawl_compare_YYYYMMDD.log
# sin necesidad de rebuildear con flags distintos.
#
# En dev (sin sys.frozen) los flags quedan como los configuraste arriba.
# ============================================================
import sys as _sys
if getattr(_sys, "frozen", False):
    DEBUG_SCRAPING_PIPELINE = True       # pipeline de cada intento de scrape
    DEBUG_FUZZY_MATCHING = True          # scores del matching Excel↔Web
    DEBUG_COMPARISON_PIPELINE = True     # contexto multi-periodo + URLs + JSON
    DEBUG_STARTUP_EXCEL_LOAD = True      # carga de Excel al arrancar
    DEBUG_CRAWL4AI_VERBOSE = True        # verbose interno de Crawl4AI + cache

    # Los siguientes quedan en False INCLUSO en .exe:
    # DEBUG_LLM_MARKDOWN     — genera un archivo por intento (llena disco)
    # DEBUG_EXCEL_PARSING    — muy verboso, solo útil para diagnosticar parseo
```

**Por qué este patrón y no env vars o config file:** mantiene una única fuente de verdad para qué se loguea. El dev sigue editando `debug_config.py` con sus flags locales (en dev), y el `if sys.frozen` garantiza el comportamiento de producción. Activar/desactivar dinámicamente queda como **mejora futura** (ver sección al final).

**Orden de import crítico:** este bloque ejecuta al primer `import debug_config`. `error_logger.setup_error_logging()` se llama después en `main.py`, por lo que cuando el logger envuelve `stdout`, los flags ya están en su estado final (forzados o no).

#### `Hoteles/Deploy/splash.py`

Responsabilidades:
- `SplashScreen` — clase que crea una ventana `tk.Tk()` sin barra de título (`overrideredirect(True)`), centrada en pantalla, con label de estado + barra de progreso indeterminada.
- `update_status(mensaje)` — actualiza el label y llama `update()` para forzar redibujado.
- `close()` — para la barra y destruye el root.

Decisión clave: usa `tkinter` puro, NO CustomTkinter. Razones:
- CTk no está inicializado en este punto del arranque.
- `ctk.CTk()` debe instanciarse una sola vez como root de la app — el splash no puede competir con la app principal por ese slot.
- Tkinter siempre está disponible (ships con Python).
- Los colores se hardcodean (no se importa `UI/styles/colors.py` porque ese módulo depende de CTk).

#### Tests opcionales

- `Hoteles/Tests/test_splash_visual.py` — smoke test visual del splash (instanciar, mostrar 3 mensajes con sleep, cerrar).

### Modificados

#### `Hoteles/main.py`

Cambios (+15 líneas aprox):

```python
import sys, io

# Forzar UTF-8 (sin cambios)
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# [NUEVO] 1. Logger ANTES de todo
from Deploy.error_logger import setup_error_logging
setup_error_logging()

# [NUEVO] 2. Splash solo en .exe
_splash = None
if getattr(sys, "frozen", False):
    from Deploy.splash import SplashScreen
    _splash = SplashScreen()

if "--self-test" in sys.argv:
    from Deploy.smoke_test import run_smoke_test
    run_smoke_test()

# 3. Checks con callback
from Deploy.startup_check import run_checks
run_checks(on_progress=_splash.update_status if _splash else None)

# [NUEVO] 4. Cerrar splash antes de CTk
if _splash:
    _splash.update_status("Iniciando interfaz...")
    _splash.close()
    _splash = None

import customtkinter as ctk
from Core.gestor_datos import *
from UI.interfaz_ctk import CrawlCompareGUI

def run_app():
    root = ctk.CTk()
    app = CrawlCompareGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
```

Encadenado importante de wrappers sobre stdout:

```
sys.stdout original (PyInstaller)
    └── io.TextIOWrapper (UTF-8, main.py)
            └── _TeeStream (Tee a log, error_logger.py)
```

Este orden funciona porque `_TeeStream.write()` delega al `TextIOWrapper` que maneja la codificación UTF-8 correctamente.

#### `Hoteles/Deploy/startup_check.py`

Agregar parámetro opcional `on_progress` retrocompatible:

```python
from typing import Optional, Callable

def run_checks(on_progress: Optional[Callable[[str], None]] = None) -> None:
    _notify = on_progress or (lambda msg: None)

    _notify("Verificando configuración...")
    check_env()

    _notify("Verificando navegador...")
    check_playwright()
```

Llamadas existentes a `run_checks()` sin argumento siguen funcionando (dev, tests).

#### `Hoteles/Deploy/crawl_compare.spec`

Cuando se quiera distribuir al usuario final:

```python
console=False,  # antes: True
```

Mientras se testea, mantener `True` para ver output en consola en paralelo al log. Este cambio es independiente del resto de la feature y se hace cuando el logging esté validado.

---

## Trade-offs y alternativas descartadas

### Por qué `_TeeStream` y no `logging` stdlib

| Opción | Pros | Contras |
|---|---|---|
| **`_TeeStream` (elegido)** | 0 cambios en módulos existentes. Los `print()` siguen funcionando. | No estructura logs por niveles. |
| `logging` stdlib | Niveles, handlers, formatters estándar. | Hay que migrar 30+ sitios de `print()` a `logging.debug()`. Cambio de superficie grande. |

El patrón de "flag booleano + `print()`" ya está consolidado en el proyecto. Solo falta el destino, y `_TeeStream` lo agrega sin tocar el resto.

### Por qué `tkinter` puro para el splash y no CTk

`customtkinter` mantiene estado global (tema, fuentes, scaling) inicializado al instanciar el primer widget. Crear dos `ctk.CTk()` distintos en el ciclo de vida del proceso es undefined behavior según la convención de CTk (no documentado como soportado).

Con `tk.Tk()` para splash y `ctk.CTk()` para la app: al hacer `splash.close()` → `root.destroy()`, el slot de root de Tk queda libre y CTk lo toma limpio. Esto funciona porque `ctk.CTk` hereda de `tk.Tk`.

### Por qué `update()` manual y no thread separado

Tkinter detecta cuando un widget se opera desde un thread distinto al que lo creó y puede lanzar `RuntimeError: main thread is not in main loop`. Tcl (la lib que respalda Tk) no es thread-safe para widgets.

El patrón documentado es: crear la ventana en el main thread, llamar `update()` manualmente entre tareas largas. Esto funciona acá porque `run_checks()` ya es secuencial y rápido — los checks que tardan (instalación de Playwright) ya tienen su propia ventana de progreso y solo ocurren en dev.

### Por qué el log junto al `.exe` y no en `%APPDATA%`

| Opción | Pros | Contras |
|---|---|---|
| **Junto al `.exe` (elegido)** | El usuario lo encuentra fácil para mandárnoslo cuando algo falla. | Requiere permisos de escritura en esa carpeta. |
| `%APPDATA%/CrawlCompare/` | Convención Windows, no requiere permisos especiales. | El usuario no sabe dónde está. |

Como la app se distribuye en una carpeta donde el usuario tiene permisos (típicamente `Documents/` o `Desktop/`), no hay problema de permisos. Y la usabilidad de "mandanos el `log.txt` que está al lado del .exe" supera la pureza de la convención.

### Por qué el splash solo en `.exe` y no en dev

En dev ya se ve la consola con el output de `print()` y el arranque toma <1 segundo. El splash agregaría fricción al ciclo de desarrollo (más ventana que cerrar mentalmente al testear). En producción, en cambio, es la única forma de informarle al usuario que la app está cargando.

---

## Decisiones confirmadas

1. **Nombre del log**: `crawl_compare_YYYYMMDD.log` (uno por día, sin auto-cleanup en esta primera versión). ✅
2. **Cambio `console=True` → `False`**: queda **fuera de esta feature**, se hace en un PR aparte después de validar que el logging funciona bien en producción. ✅
3. **Messagebox al crash**: SÍ. `tk.messagebox.showerror` simple informando al usuario que algo falló y dónde está el log. Implementado dentro de `_excepthook`. ✅
4. **Flags forzados en `.exe`**: 5 flags (`DEBUG_SCRAPING_PIPELINE`, `DEBUG_FUZZY_MATCHING`, `DEBUG_COMPARISON_PIPELINE`, `DEBUG_STARTUP_EXCEL_LOAD`, `DEBUG_CRAWL4AI_VERBOSE`). Los otros dos quedan en `False` por motivos de ruido/disco. ✅

---

## Mejoras futuras (NO entran en esta feature)

### Toggle de flags desde la UI

Hoy el único modo de cambiar qué se loguea es rebuildear el `.exe`. Sería útil que el usuario (o nosotros, vía instrucciones remotas) pudiera activar/desactivar flags sin recompilar.

**Diseño propuesto cuando se aborde:**
- Agregar una **5ª pestaña "Debug"** al [config_modal.py](../../Hoteles/UI/views/config_modal.py) con checkboxes por flag.
- Persistir el override de cada flag en `config.json` (vía `ConfigService` que ya existe).
- Refactorizar `debug_config.py` para leer el override desde `ConfigService` además del `sys.frozen` actual.

**Por qué NO entra ahora:**
- Cambia el orden de import (`debug_config.py` pasaría a depender de `ConfigService`, que hoy es al revés).
- Requiere repensar UX de "reiniciar la app para aplicar cambios" o hot-reload de flags.
- Mezcla scope con la presente feature (que es solo arranque + persistencia base).

### Auto-rotación / cleanup del log

Eliminar logs viejos automáticamente (mantener solo los últimos N días) para no llenar la carpeta del usuario indefinidamente.

### Niveles de log estructurados

Migrar de `print()` condicional a `logging` stdlib con niveles (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Permite filtrar el archivo por severidad. Es un cambio grande (30+ sitios) y solo conviene si el toggle desde UI también se implementa.

---

## Plan de implementación incremental

Recomendación de orden por commits, cada uno auto-contenido y testeable:

1. **`feat(debug): override de flags en .exe`**
   - Agrega bloque `if sys.frozen` al final de `debug_config.py` que fuerza los 5 flags elegidos.
   - Sin logger todavía. Test: build .exe, agregar `print(DEBUG_SCRAPING_PIPELINE)` temporal y verificar que sale `True`.

2. **`feat(deploy): error_logger con excepthook + tee de stdout + messagebox`**
   - Crea `Deploy/error_logger.py` completo (TeeStream, DummyStream, excepthook con messagebox).
   - Modifica `main.py` para llamar `setup_error_logging()` antes de cualquier otra cosa.
   - Sin splash todavía. Test: forzar un `raise` en `main.py` después del setup y verificar que aparece el log + messagebox.

3. **`feat(deploy): startup_check acepta callback de progreso`**
   - Modifica `startup_check.py` agregando `on_progress`.
   - Sin splash todavía — solo la firma cambia, retrocompatible. Test: corre todo igual que antes.

4. **`feat(deploy): splash screen con progreso en arranque del .exe`**
   - Crea `Deploy/splash.py`.
   - Modifica `main.py` para instanciar splash, pasar callback a `run_checks`, cerrar splash antes de CTk.
   - Test: build .exe y verificar splash visible + mensajes correctos + cierre limpio + log generado con runtime.

5. **(Fuera de esta feature) `chore(deploy): console=False en spec para distribución`**
   - PR aparte después de validar el logging en producción.

---

## Archivos críticos a tocar

- [Hoteles/main.py](../../Hoteles/main.py) — orquestación del arranque (logger + splash + checks + CTk)
- [Hoteles/debug_config.py](../../Hoteles/debug_config.py) — override de 5 flags cuando `sys.frozen`
- [Hoteles/Deploy/startup_check.py](../../Hoteles/Deploy/startup_check.py) — agregar `on_progress`
- [Hoteles/Deploy/error_logger.py](../../Hoteles/Deploy/error_logger.py) — **nuevo**
- [Hoteles/Deploy/splash.py](../../Hoteles/Deploy/splash.py) — **nuevo**
- [Hoteles/Deploy/crawl_compare.spec](../../Hoteles/Deploy/crawl_compare.spec) — **fuera de esta feature** (PR aparte para `console=False`)

---

## Ver también

- [docs/deploy/build-deploy.md](../deploy/build-deploy.md) — proceso de build actual
- [docs/desarrollo/debugging.md](../desarrollo/debugging.md) — flags de debug existentes
