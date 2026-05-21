# Build y Deploy — CrawlCompare.exe

Sistema de empaquetado de la app en un binario standalone para Windows. Output final: `Hoteles/Deploy/dist/CrawlCompare.exe` (~241MB, todo embebido).

---

## 1. Resumen

- El sistema de deploy compila la app + dependencias + Chromium + `.env` + Excel en un solo `.exe` con PyInstaller, y valida el bundle con un smoke test automático.
- **Output**: `CrawlCompare.exe` (~241MB), standalone — no requiere Python, ni `pip install`, ni `playwright install`.
- **Lo que necesita el usuario final**: solo el `.exe`. Todo está embebido (incluso las API keys del `.env`).

---

## 2. Arquitectura del Deploy

```
Hoteles/Deploy/
├── build_manifest.py     ← qué entra al bundle (declarativo)
├── crawl_compare.spec    ← cómo se arma el bundle (lee de build_manifest)
├── smoke_test.py         ← checks post-build de módulos críticos
├── build.bat             ← script de build (compila + corre smoke test)
├── startup_check.py      ← checks de entorno al arrancar (.env, Playwright)
├── __init__.py           ← vacío, hace Deploy/ paquete importable
└── dist/
    └── CrawlCompare.exe  ← output final
```

| Archivo | Rol |
|---------|-----|
| `build_manifest.py` | Manifest declarativo de paquetes, datas, binarios externos. **Tocar este, no el .spec.** |
| `crawl_compare.spec` | Config PyInstaller. Lee de `build_manifest.py`, no tiene listas hardcodeadas. |
| `smoke_test.py` | Lista declarativa de checks que validan el bundle. Corre via `--self-test`. |
| `build.bat` | Script 4 pasos: verifica PyInstaller → limpia → compila → corre smoke test. |
| `startup_check.py` | Lógica de arranque del `.exe`: carga `.env`, setea Playwright. |
| `__init__.py` | Hace `Deploy/` importable desde `main.py`. |

---

## 3. Cómo buildear

### Opción A — `build.bat` (recomendado)

Compila **y** corre el smoke test automáticamente. Si el smoke test falla, aborta.

```bat
cd Hoteles
Deploy\build.bat
```

Output esperado: `[1/4] PyInstaller OK → [2/4] limpio → [3/4] compila → [4/4] smoke test 8/8 ✅`.

### Opción B — Manual (dos pasos)

```bat
cd Hoteles
conda run -n crawler pyinstaller "Deploy/crawl_compare.spec" --distpath "Deploy/dist" --workpath "Deploy/build"
Deploy\dist\CrawlCompare.exe --self-test
```

Ver comandos completos y troubleshooting de output en [comandos.md](comandos.md).

---

## 4. Cómo distribuir

- Pasar **solo el `.exe`** (~241MB). Todo lo demás está embebido.
- **Sugerencias**: Google Drive, WeTransfer, OneDrive. No mandar por WhatsApp ni email (límites de tamaño + compresión que rompe el binario).
- **Avisar al destinatario**: Windows Defender / SmartScreen va a marcarlo como sospechoso (falso positivo típico de PyInstaller con binarios grandes sin firmar). Hay que hacer click en "Más información → Ejecutar de todas formas".
- **Asumir círculo de confianza**: el `.env` con `GROQ_API_KEY` viaja embebido en `_MEIPASS`. Cualquiera con el `.exe` puede extraerlo. No distribuir fuera del entorno controlado.
- **`console=True` actualmente** en el `.spec`: al ejecutar aparece una ventana negra de terminal junto a la UI (útil para ver logs y errores). Antes de distribución masiva conviene cambiar a `console=False` y recompilar.

---

## 5. Manifest declarativo (`build_manifest.py`)

Es el "package.json" del deploy. Separa **qué entra al bundle** (declarativo) de **cómo se arma** (imperativo, en el `.spec`). El `.spec` lee de acá — **nunca tocar el `.spec` directo**.

### Las 6 listas

| Lista | Contiene actualmente | Cuándo tocarla |
|-------|----------------------|----------------|
| `PACKAGES_COLLECT_ALL` | `customtkinter`, `crawl4ai`, `playwright`, `playwright_stealth`, `fake_http_header`, `tiktoken`, `tiktoken_ext`, `litellm` | Paquete pesado con `datas + binaries + hiddenimports` propios. Si una lib explota con `FileNotFoundError`, `ModuleNotFoundError` o `Plugins found: []`, agregala acá. |
| `PACKAGES_SUBMODULES` | `openpyxl`, `rapidfuzz`, `pydantic` | Lib Python pura con discovery dinámico de submódulos (sin datas/binarios). |
| `EXTRA_HIDDEN_IMPORTS` | `dotenv`, `tkinter`, `tkinter.ttk` | Módulos cargados por nombre con `importlib` o que PyInstaller no detecta por análisis estático. |
| `EXTRA_DATAS` | `(Data/Extracto_prueba2.xlsx, Data)`, `(.env, .)` | Archivos sueltos del proyecto. Tuplas `(src_relativo_a_Hoteles, dest_en_MEIPASS)`. |
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

### Qué valida (8 checks actuales)

1. `customtkinter` — version
2. `tiktoken` encoding — `cl100k_base loaded`
3. `playwright` — import
4. `playwright_stealth` — import
5. `crawl4ai` — version
6. `fake_http_header` — `FakeHttpHeader()` instanciado
7. `.env loaded` — `GROQ_API_KEY` presente en entorno
8. Excel embebido — `Extracto_prueba2.xlsx` en `_MEIPASS/Data/`

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

## 7. `startup_check.py`

Corre **antes** de levantar la UI desde `main.py` (`run_checks()`).

### `_get_base_dir()`

Lógica frozen vs dev:
- En `.exe` (`sys.frozen=True`): retorna `sys._MEIPASS` — carpeta temporal donde PyInstaller extrae los archivos declarados en `datas`.
- En dev: retorna `Hoteles/` relativo al `__file__`.

### `check_env()`

- Busca `.env` en `base_dir`.
- Si no existe → `messagebox.showerror` + `sys.exit(1)`.
- Si existe → `load_dotenv(env_path)` carga las keys al entorno (`GROQ_API_KEY`, etc.).

### `check_playwright()`

- En `.exe`: setea `PLAYWRIGHT_BROWSERS_PATH` apuntando a `_MEIPASS/playwright/driver/package/.local-browsers/` y retorna — **no instala nada**.
- En dev: verifica si `AppData/Local/ms-playwright/chromium-*/chrome.exe` existe; si no, lo instala con una ventanita de progreso.

---

## 8. Decisiones clave del `.spec`

### `collect_all()` en vez de `collect_data_files()` + `collect_submodules()`

`collect_data_files` solo incluye archivos declarados por el paquete mismo. Dependencias transitivas como `playwright_stealth` o `fake_http_header` tienen `.js` y carpetas `data/` que no se incluían, causando `FileNotFoundError` en runtime.

`collect_all(pkg)` trae `datas + binaries + hiddenimports` en un solo llamado, cubriendo el árbol completo.

### Chromium embebido

Chromium completo (~338MB sin comprimir, ~150MB extra en el binario final) se embebe en el `.exe` desde `AppData/Local/ms-playwright/chromium-1181/`. El usuario no necesita `playwright install`.

### `.env` y Excel embebidos en `_MEIPASS`

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

---

> **Nota**: estos fixes ya están aplicados en el sistema actual — quedan acá como referencia de los gotchas encontrados en el proceso.
