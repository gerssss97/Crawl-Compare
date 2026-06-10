# Build y Deploy — CrawlCompare.exe

Sistema de empaquetado de la app en una carpeta standalone para Windows (PyInstaller `--onedir`). Output final: `Hoteles/Deploy/dist/CrawlCompare/` (~258MB, todo embebido) con `CrawlCompare.exe` + `_internal/` al lado.

---

## 1. Resumen

- El sistema de deploy compila la app + dependencias + Chromium + `.env` + Excel + íconos en una carpeta `--onedir` con PyInstaller, y valida el bundle con un smoke test automático.
- **Output**: carpeta `CrawlCompare/` (~258MB) con `CrawlCompare.exe` + `_internal/`, standalone — no requiere Python, ni `pip install`, ni `playwright install`.
- **Lo que necesita el usuario final**: la **carpeta entera** `CrawlCompare/`. El `.exe` solo no arranca: necesita `_internal/` al lado. Todo está embebido (incluso las API keys del `.env`).
- **Por qué `--onedir` y no `--onefile`**: el `.exe` no se descomprime a `%TEMP%\_MEI<random>\` en cada arranque → más rápido, y los paths internos (`_internal/`) son **estables** entre ejecuciones. Ver [docs/features/plan-instalador-diferenciado.md](../features/plan-instalador-diferenciado.md).
- **Archivos generados en runtime junto al `.exe`**: `crawl_compare_YYYYMMDD.log` (logs persistentes + tracebacks de crashes). Ver sección 7.

---

## 2. Arquitectura del Deploy

```
Hoteles/Deploy/
├── build_manifest.py     ← qué entra al bundle (declarativo)
├── crawl_compare.spec    ← cómo se arma el bundle (lee de build_manifest)
├── smoke_test.py         ← checks post-build de módulos críticos
├── build.bat             ← script de build (compila + corre smoke test)
├── startup_check.py      ← checks de entorno al arrancar (.env, Playwright)
├── error_logger.py       ← logging persistente: excepthook + tee de stdout
├── splash.py             ← ventana de splash durante el arranque del .exe
├── __init__.py           ← vacío, hace Deploy/ paquete importable
└── dist/
    └── CrawlCompare/         ← output final (--onedir)
        ├── CrawlCompare.exe  ← el que el usuario abre
        └── _internal/        ← datas + binarios + DLLs (sys._MEIPASS apunta acá)
```

| Archivo | Rol |
|---------|-----|
| `build_manifest.py` | Manifest declarativo de paquetes, datas, binarios externos. **Tocar este, no el .spec.** |
| `crawl_compare.spec` | Config PyInstaller. Lee de `build_manifest.py`, no tiene listas hardcodeadas. |
| `smoke_test.py` | Lista declarativa de checks que validan el bundle. Corre via `--self-test`. |
| `build.bat` | Script 4 pasos: verifica PyInstaller → limpia → compila → corre smoke test. |
| `startup_check.py` | Lógica de arranque del `.exe`: carga `.env`, setea Playwright. Acepta callback `on_progress` para notificar al splash. |
| `error_logger.py` | Instala `sys.excepthook` (traceback al log + messagebox) y `_TeeStream` que duplica `stdout`/`stderr` al archivo `crawl_compare_YYYYMMDD.log`. Solo activo en `.exe`. |
| `splash.py` | `SplashScreen` en `tkinter` puro (no CTk) — ventana sin barra de título con label de estado y barra de progreso indeterminada. Se muestra durante todo el arranque. |
| `__init__.py` | Hace `Deploy/` importable desde `main.py`. |

---

## 3. Cómo buildear

### Opción A — `build.bat` (recomendado)

Compila **y** corre el smoke test automáticamente. Si el smoke test falla, aborta.

```bat
cd Hoteles
Deploy\build.bat
```

Output esperado: `[1/4] PyInstaller OK → [2/4] limpio → [3/4] compila → [4/4] smoke test 9/9 ✅`.

### Opción B — Manual (dos pasos)

```bat
cd Hoteles
conda run -n crawler pyinstaller "Deploy/crawl_compare.spec" --distpath "Deploy/dist" --workpath "Deploy/build"
Deploy\dist\CrawlCompare\CrawlCompare.exe --self-test
```

Ver comandos completos y troubleshooting de output en [comandos.md](comandos.md).

---

## 4. Cómo distribuir

- Comprimir la **carpeta entera** `dist/CrawlCompare/` en un `.zip` (~258MB) y pasar ese `.zip`. **No** mandar el `.exe` suelto: sin `_internal/` al lado no arranca.
- Incluir un `README.txt` dentro del `.zip`: *"Descomprimí donde quieras y hacé doble click en `CrawlCompare/CrawlCompare.exe`. No muevas el `.exe` solo: necesita la carpeta `_internal/` al lado."*
- **Sugerencias**: Google Drive, WeTransfer, OneDrive. No mandar por WhatsApp ni email (límites de tamaño + compresión que rompe el binario).
- **Avisar al destinatario**: Windows Defender / SmartScreen va a marcar el `.exe` como sospechoso (falso positivo típico de PyInstaller con binarios grandes sin firmar). Hay que hacer click en "Más información → Ejecutar de todas formas".
- **Asumir círculo de confianza**: el `.env` con `GROQ_API_KEY` viaja embebido en `_internal/`. Cualquiera con la carpeta puede extraerlo. No distribuir fuera del entorno controlado.
- **`console=True` actualmente** en el `.spec`: al ejecutar aparece una ventana negra de terminal junto a la UI (útil para ver logs y errores). Antes de distribución masiva conviene cambiar a `console=False` y recompilar. El logging persistente (sección 7) cubre el caso `console=False` automáticamente.
- **Logs en runtime**: el `.exe` crea/anexa `crawl_compare_YYYYMMDD.log` en su misma carpeta. Si el usuario reporta un bug, pedirle ese archivo.

> 📋 **Próximo paso de distribución**: la Fase 1 (`--onedir`) ya está implementada. La Fase 2 (instalador real con Inno Setup) queda pendiente. Ver [docs/features/plan-instalador-diferenciado.md](../features/plan-instalador-diferenciado.md).

---

## 5. Manifest declarativo (`build_manifest.py`)

Es el "package.json" del deploy. Separa **qué entra al bundle** (declarativo) de **cómo se arma** (imperativo, en el `.spec`). El `.spec` lee de acá — **nunca tocar el `.spec` directo**.

### Las 6 listas

| Lista | Contiene actualmente | Cuándo tocarla |
|-------|----------------------|----------------|
| `PACKAGES_COLLECT_ALL` | `customtkinter`, `crawl4ai`, `playwright`, `playwright_stealth`, `fake_http_header`, `tiktoken`, `tiktoken_ext`, `litellm` | Paquete pesado con `datas + binaries + hiddenimports` propios. Si una lib explota con `FileNotFoundError`, `ModuleNotFoundError` o `Plugins found: []`, agregala acá. |
| `PACKAGES_SUBMODULES` | `openpyxl`, `rapidfuzz`, `pydantic` | Lib Python pura con discovery dinámico de submódulos (sin datas/binarios). |
| `EXTRA_HIDDEN_IMPORTS` | `dotenv`, `tkinter`, `tkinter.ttk` | Módulos cargados por nombre con `importlib` o que PyInstaller no detecta por análisis estático. |
| `EXTRA_DATAS` | `(Data/Extracto_prueba2.xlsx, Data)`, `(.env, .)`, `(UI/assets/icons/light, UI/assets/icons/light)`, `(UI/assets/icons/dark, UI/assets/icons/dark)` | Archivos y/o carpetas sueltas del proyecto. Tuplas `(src_relativo_a_Hoteles, dest_en_MEIPASS)`. PyInstaller acepta directorios — los expande recursivamente. |
| `EXTERNAL_BINARIES` | Chromium 1181 (`ms-playwright/chromium-1181`) + Playwright driver (`node.exe` + package JS) | Binarios fuera del venv. Si Playwright actualiza la revisión de Chromium (ej: a 1182), hay que actualizar el path acá. |
| `EXCLUDES` | `Tests` | Carpetas/módulos a excluir del análisis para bajar tamaño. |

### Ejemplo: agregar una dependencia nueva

Supongamos que sumás `langchain` y al correr el `.exe` falla con `ModuleNotFoundError: langchain.embeddings`. Pasos:

1. Abrir `Hoteles/Deploy/build_manifest.py`.
2. Agregar `"langchain"` a `PACKAGES_COLLECT_ALL` (si tiene datas/configs internos) o `PACKAGES_SUBMODULES` (si es Python puro).
3. Rebuildear con `build.bat`.
4. Si el bug es plugin-style (descubrimiento dinámico), **además** agregá un check a `smoke_test.py` para que no se repita.

**Regla**: tocar `build_manifest.py`, NO `crawl_compare.spec` directamente.

---

## 6. Smoke test post-build (`--self-test`)

### Qué valida (9 checks actuales)

1. `customtkinter` — version
2. `tiktoken` encoding — `cl100k_base loaded`
3. `playwright` — import
4. `playwright_stealth` — import
5. `crawl4ai` — version
6. `fake_http_header` — `FakeHttpHeader()` instanciado
7. `.env loaded` — `GROQ_API_KEY` presente en entorno
8. Excel embebido — `Extracto_prueba2.xlsx` en `_MEIPASS/Data/`
9. **Íconos bundled** — verifica ≥ `_MIN_ICONS_POR_VARIANTE` PNGs en `_MEIPASS/UI/assets/icons/light/` y `dark/`, y que cada nombre en `light/` tenga su par en `dark/`. Detecta tanto "olvidé `EXTRA_DATAS`" como "agregué un PNG solo en una variante".

### Cómo se ejecuta

- **Automático**: `build.bat` lo corre como paso [4/4] después de compilar. Si exit code != 0, marca el build como inválido.
- **Manual**: `Hoteles\Deploy\dist\CrawlCompare.exe --self-test`. `main.py` detecta el flag en `sys.argv`, llama `smoke_test.run_smoke_test()` y sale antes de levantar la UI.

### Regla de oro

> **Cada bug de bundling descubierto = un check nuevo en `smoke_test.py`.**

Si no, el bug puede volver silenciosamente al actualizar una dep o agregar una feature, y recién explota en la máquina del usuario. El smoke test es la red de seguridad.

### Ejemplo: agregar un check

En `smoke_test.py`:

```python
def _check_mi_lib():
    import mi_lib
    mi_lib.do_something_que_explotaba()
    return "OK"

# Sumarlo a la lista:
CHECKS = [
    ...,
    ("mi_lib funcional", _check_mi_lib),
]
```

---

## 7. Arranque del `.exe`

Esta sección describe el orden completo de inicialización desde que el usuario hace doble click hasta que aparece la UI. El orden es **deliberado** — invertir pasos rompe garantías.

### 7.1 Orden de inicialización

```
[Doble click → PyInstaller carga desde _internal/ (onedir, sin descompresión a %TEMP%)]
    │  (arranque rápido y estable; sys._MEIPASS apunta a _internal/ junto al .exe)
    ▼
[Python arranca, ejecuta Hoteles/main.py]
    │
    ▼
[1] UTF-8 wrappers sobre sys.stdout / sys.stderr
    │  (necesario: PyInstaller no hereda UTF-8 en Windows → tildes/ñ explotan)
    │
    ▼
[2] error_logger.setup_error_logging()
    ├── Instala sys.excepthook que vuelca traceback al log + messagebox al usuario
    └── Envuelve sys.stdout/sys.stderr con _TeeStream → todo print() también
        va a crawl_compare_YYYYMMDD.log
    │
    ▼
[3] SplashScreen() (solo si sys.frozen)
    │  Ventana tk pura, sin barra de título, centrada. Topmost.
    │
    ▼
[4] startup_check.run_checks(on_progress=splash.update_status)
    ├── _notify("Verificando configuración...")
    │   └── check_env() → carga .env desde _MEIPASS
    └── _notify("Verificando navegador...")
        └── check_playwright() → setea PLAYWRIGHT_BROWSERS_PATH
    │
    ▼
[5] splash.update_status("Iniciando ventana...") + splash.close()
    │  CRÍTICO: cerrar splash ANTES de instanciar ctk.CTk(). Tener dos
    │  roots Tk vivos rompe el registro de imágenes de PIL/CTk
    │  ("image pyimage1 doesn't exist" en el header). Ver Fix 10.
    │
    ▼
[6] import customtkinter as ctk + import Core.gestor_datos + import CrawlCompareGUI
    │  (~600ms en frío — son los imports pesados)
    │
    ▼
[7] root = ctk.CTk() + CrawlCompareGUI(root) + root.mainloop()
```

### 7.2 `error_logger.py` — logging persistente

Sus tres responsabilidades:

1. **`sys.excepthook` instalado**: cualquier excepción no manejada se persiste con timestamp y separador en `crawl_compare_YYYYMMDD.log` ubicado junto al `.exe` (`Path(sys.executable).parent`, **no** en `_MEIPASS` que es temporal). Después muestra un `tk.messagebox.showerror` informando la ruta del log para que el usuario nos lo mande.

2. **`_TeeStream` sobre `stdout` y `stderr`**: wrapper que escribe simultáneamente al destino original (consola si `console=True`) y al archivo de log. Los 30+ sitios del código que usan `print()` condicional con flags de debug van automáticamente al log sin necesidad de migrar a `logging` stdlib.

3. **`_DummyStream`**: stand-in cuando `sys.stdout is None` (caso `console=False`). Permite que el Tee siga capturando al archivo aunque no haya consola visible.

`setup_error_logging()` **hace early return en dev** (`not sys.frozen`). Comportamiento en desarrollo no cambia.

### 7.3 Override de flags de debug en `.exe` (`debug_config.py`)

En el `.exe`, **5 flags de debug se fuerzan a `True`** automáticamente al importar `debug_config`:

| Flag | Por qué se fuerza en `.exe` |
|---|---|
| `DEBUG_SCRAPING_PIPELINE` | Diagnóstico #1: pipeline completo de cada intento de scrape. |
| `DEBUG_FUZZY_MATCHING` | Scores del matching Excel ↔ Web. |
| `DEBUG_COMPARISON_PIPELINE` | URLs, JSON crudo del LLM, contexto multi-periodo. |
| `DEBUG_STARTUP_EXCEL_LOAD` | Confirma qué Excel se cargó al arrancar. |
| `DEBUG_CRAWL4AI_VERBOSE` | Verbose interno de Crawl4AI (`[INIT]`, `[FETCH]`, etc.) + cache. |

Los siguientes **NO se fuerzan** (quedan en `False` incluso en `.exe`):
- `DEBUG_LLM_MARKDOWN` — genera un archivo por intento (llena disco rápido).
- `DEBUG_EXCEL_PARSING` — muy verboso, solo útil para diagnosticar el parser de fechas.

**En dev** los flags quedan como los configuraste localmente (todos en `False` por defecto).

El override y el `_TeeStream` se complementan: gracias a los flags forzados hay output operativo, y gracias al Tee ese output queda persistido en el log del usuario.

### 7.4 `splash.py` — ventana de bienvenida

Usa **`tkinter` puro** (no CTk). Razones:
- CTk no está inicializado en este punto del arranque.
- Solo se puede crear una instancia de `ctk.CTk()` como root durante el ciclo de vida del proceso. El splash debe ser un Tk separado que se destruye antes de instanciar `ctk.CTk()`.
- Colores hardcodeados (no se importa `UI/styles/colors.py` porque ese módulo depende de CTk).

Patrón de actualización: `update_status(mensaje)` setea el label y llama `self._root.update()` (no `mainloop()` que bloquearía). Como el `_TeeStream` está activo, cada `update_status` también hace `print("[startup] ...")` que queda en el log y en consola.

**Por qué se cierra antes de `ctk.CTk()`**: ver Fix 10 en sección 10 (historial de bugs).

### 7.5 `startup_check.py` — checks de entorno

#### `_get_base_dir()`

Lógica frozen vs dev:
- En `.exe` (`sys.frozen=True`): retorna `sys._MEIPASS` — en onedir es la carpeta `_internal/` adyacente al `.exe` (path estable) donde están los archivos declarados en `datas`.
- En dev: retorna `Hoteles/` relativo al `__file__`.

#### `check_env()`

- Busca `.env` en `base_dir`.
- Si no existe → `messagebox.showerror` + `sys.exit(1)`.
- Si existe → `load_dotenv(env_path)` carga las keys al entorno (`GROQ_API_KEY`, etc.).

#### `check_playwright()`

- En `.exe`: setea `PLAYWRIGHT_BROWSERS_PATH` apuntando a `_MEIPASS/playwright/driver/package/.local-browsers/` y retorna — **no instala nada**.
- En dev: verifica si `AppData/Local/ms-playwright/chromium-*/chrome.exe` existe; si no, lo instala con una ventanita de progreso.

#### `run_checks(on_progress=None)`

Wrapper que invoca los dos checks anteriores notificando progreso vía callback opcional. Si no se pasa callback (uso desde dev/tests), el `_notify` es un no-op lambda. La feature del splash usa este callback para mostrar progreso visual.

---

## 8. Decisiones clave del `.spec`

### `collect_all()` en vez de `collect_data_files()` + `collect_submodules()`

`collect_data_files` solo incluye archivos declarados por el paquete mismo. Dependencias transitivas como `playwright_stealth` o `fake_http_header` tienen `.js` y carpetas `data/` que no se incluían, causando `FileNotFoundError` en runtime.

`collect_all(pkg)` trae `datas + binaries + hiddenimports` en un solo llamado, cubriendo el árbol completo.

### Chromium embebido

Chromium completo (~338MB sin comprimir, ~150MB extra en el binario final) se embebe en el `.exe` desde `AppData/Local/ms-playwright/chromium-1181/`. El usuario no necesita `playwright install`.

### `.env` y Excel embebidos en `_MEIPASS` (= `_internal/` en onedir)

- `.env` → raíz de `_MEIPASS` (leído por `startup_check.check_env()`).
- `Extracto_prueba2.xlsx` → `_MEIPASS/Data/` (leído por `controller._excel_path()` cuando `sys.frozen=True`).

---

## 9. Troubleshooting común

| Síntoma | Causa | Fix |
|---------|-------|-----|
| Build se corta en `[1/3]` o `[3/4]` sin error visible | Falta `call conda run` en `build.bat`, o `conda` no está en el PATH del cmd | Correr desde Anaconda Prompt, no PowerShell genérico. Verificar `conda --version` antes. |
| Smoke test falla en módulo X (`FileNotFoundError` o `ModuleNotFoundError`) | El paquete X no está en `PACKAGES_COLLECT_ALL` o le faltan submódulos | Agregar X a `PACKAGES_COLLECT_ALL` en `build_manifest.py`, rebuildear. |
| `.exe` arranca pero crashea al scrapear sin error claro | Falta debug visible — algún plugin-style no se cargó | Activar `DEBUG_SCRAPING_PIPELINE=True` en `debug_config.py`, rebuildear, ver logs en la ventana de consola. |
| `FileNotFoundError` en runtime con archivo `.js`/`.json` de un paquete | El paquete usa `collect_data_files` insuficiente | Migrarlo a `PACKAGES_COLLECT_ALL` (trae `datas + binaries + hiddenimports`). |
| `Unknown encoding cl100k_base. Plugins found: []` | `tiktoken_ext` no en el bundle (plugin-style, análisis estático no lo ve) | Ya cubierto: `tiktoken_ext` está en `PACKAGES_COLLECT_ALL` + check en smoke test. |
| Windows Defender bloquea el `.exe` | Falso positivo típico de PyInstaller sin firmar | Click en "Más información → Ejecutar de todas formas". A largo plazo: firmar el binario. |

---

## 10. Historial de bugs resueltos (apéndice)

### Fix 1 — `.env` no encontrado
**Síntoma**: al correr el `.exe`, messagebox "Archivo .env no encontrado".
**Causa**: `_get_base_dir()` usaba `os.path.dirname(sys.executable)` (carpeta del `.exe`) pero el `.env` está embebido en `sys._MEIPASS`.
**Fix**: cambiar a `sys._MEIPASS` en modo frozen.

### Fix 2 — Loop de ventanas de instalación de Playwright
**Síntoma**: se abría una ventana tras otra indefinidamente.
**Causa**: el check original usaba `sync_playwright()` para verificar si Chromium estaba instalado. Dentro del `.exe` siempre fallaba (paths distintos), causando que siempre intentara instalar.
**Fix**: reemplazar por `_chromium_installed()` que verifica directamente si `chrome.exe` existe en `AppData/Local/ms-playwright/`.

### Fix 3 — `fake_http_header.data` no encontrado
**Síntoma**: `ModuleNotFoundError: No module named 'fake_http_header.data'` al arrancar el `.exe`.
**Causa**: `collect_data_files` no incluía las dependencias transitivas de `crawl4ai`.
**Fix**: migrar a `collect_all()` para todos los paquetes grandes.

### Fix 4 — `playwright_stealth` JS no encontrado
**Síntoma**: `FileNotFoundError: chrome.csi.js` al arrancar el `.exe`.
**Causa**: misma causa que Fix 3.
**Fix**: incluido en la migración a `collect_all()`.

### Fix 5 — Excel no encontrado
**Síntoma**: `FileNotFoundError: Extracto_prueba2.xlsx` al arrancar el `.exe`.
**Causa**: `_excel_path()` en `controller.py` usaba `Path(sys.executable).parent` en lugar de `sys._MEIPASS`.
**Fix**: corregir a `Path(sys._MEIPASS) / "Data" / "Extracto_prueba2.xlsx"`.

### Fix 6 — Encoding `charmap` en comparación
**Síntoma**: "Error de validación: 'charmap' codec can't encode characters in position 194-255".
**Causa**: PyInstaller en Windows no hereda UTF-8 para `sys.stdout`. Algún `print()` con tildes/ñ explotaba.
**Fix**: forzar UTF-8 en `sys.stdout` y `sys.stderr` al inicio de `main.py`.

### Fix 7 — Chromium no encontrado al scrapear
**Síntoma**: "BrowserType.launch: Executable doesn't exist at `_MEI.../chromium-1181/chrome-win/chrome.exe`".
**Causa**: Playwright dentro del `.exe` buscaba Chromium en `_MEIPASS` pero no estaba embebido.
**Fix**: embeber `chromium-1181` completo en el `.spec` + setear `PLAYWRIGHT_BROWSERS_PATH` en `check_playwright()`.

### Fix 8 — tiktoken `cl100k_base` no encontrado
**Síntoma**: al disparar el scraping desde el `.exe`, error `Unknown encoding cl100k_base. Plugins found: []`. En dev (`python main.py`) funcionaba sin problemas.
**Causa**: `tiktoken_ext` es el paquete que registra los encodings (`cl100k_base`, `p50k_base`, etc.) como **plugins de descubrimiento dinámico** vía entry points. PyInstaller hace análisis estático del árbol de imports, así que nunca "ve" a `tiktoken_ext` porque nadie lo importa directamente — `tiktoken` lo carga en runtime escaneando plugins. Resultado: el submódulo no entra al bundle y `tiktoken.get_encoding("cl100k_base")` falla con la lista de plugins vacía.
**Fix**: agregar `tiktoken` y `tiktoken_ext` a `PACKAGES_COLLECT_ALL` en `build_manifest.py`. También se sumó `litellm` por las dudas (mismo patrón plugin-style).
**Prevención**: el smoke test ahora ejecuta `tiktoken.get_encoding("cl100k_base")` como check obligatorio post-build.

### Fix 9 — Íconos PNG no embebidos
**Síntoma**: el `.exe` arranca, splash + checks pasan OK, pero al construir el header de `CrawlCompareGUI` crashea con `FileNotFoundError: [Errno 2] No such file or directory: '..._MEI<random>\\UI\\assets\\icons\\light\\clock.png'`.
**Causa**: `UI/styles/icons.py` carga PNGs de `UI/assets/icons/light/` y `dark/` con `PIL.Image.open()` para crear `CTkImage`. Esas carpetas **no estaban declaradas** en `EXTRA_DATAS` del `build_manifest.py`, así que los PNGs nunca llegaban al bundle. El bug pasó silencioso en builds anteriores porque la feature de logging recién agregada destapó el traceback (antes, sin excepthook personalizado, el crash se perdía con la consola).
**Fix**: agregar las dos carpetas como entradas al manifest:
```python
EXTRA_DATAS = [
    ...,
    ("UI/assets/icons/light", "UI/assets/icons/light"),
    ("UI/assets/icons/dark",  "UI/assets/icons/dark"),
]
```
PyInstaller acepta directorios como fuente — los expande recursivamente.
**Prevención**: nuevo check `Íconos bundled` en `smoke_test.py` que verifica ≥ N PNGs por variante + paridad `light↔dark`. Si una variante queda incompleta o vacía, falla el build. Además se agregó el hook `check_build_deps.py` en `.claude/` que avisa proactivamente cuando se modifican archivos del build o assets bajo `UI/assets/`.

### Fix 10 — `image "pyimage1" doesn't exist` al construir el header
**Síntoma**: con la feature de splash recién agregada, el `.exe` mostraba el splash unos ms, lo cerraba, y crashea al construir `CrawlCompareGUI` con `_tkinter.TclError: image "pyimage1" doesn't exist`. El traceback apunta a `_crear_header` → `ctk.CTkButton.__init__` → `_update_image`.
**Causa**: al crear el `SplashScreen` se instancia `tk.Tk()` que arranca un intérprete Tcl propio. Luego `ctk.CTk()` se instancia (hereda de `tk.Tk`), pero el primer Tk sigue vivo en paralelo. Cuando `Icons.load()` crea las `CTkImage`, PIL las registra como `pyimage1`, `pyimage2`, etc. en el intérprete activo, que en algunos casos era el del splash. Al cerrar el splash después de instanciar CTk, ese intérprete muere y las imágenes registradas allí también — pero los `CTkButton` del header ya guardaron referencia a `pyimage1`. Al primer redibujo en el `mainloop`, explotan.
**Fix**: **cerrar el splash ANTES de instanciar `ctk.CTk()`**. Así nunca hay dos roots Tk vivos en simultáneo y todas las `CTkImage` se registran en un único intérprete (el de CTk) que vive durante todo el `mainloop`. Trade-off de UX: el splash pierde la cobertura visual de los ~80ms que tarda `CrawlCompareGUI.__init__`. Aceptable comparado con los ~600ms de imports que sí cubre.
**Prevención**: comentario extenso en `main.py:run_app()` explicando POR QUÉ se cierra el splash antes — es contraintuitivo y un futuro refactor podría romper la garantía sin saber.

---

> **Nota**: estos fixes ya están aplicados en el sistema actual — quedan acá como referencia de los gotchas encontrados en el proceso.
