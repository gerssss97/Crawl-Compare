# Plan de Deploy — CrawlCompare.exe

Documentación de todo lo realizado para empaquetar la app en un `.exe` distribuible.

---

## Archivos creados / modificados

| Archivo | Cambio |
|---------|--------|
| `Hoteles/Deploy/startup_check.py` | Nuevo — checks de entorno al arrancar |
| `Hoteles/Deploy/crawl_compare.spec` | Modificado — ahora lee de `build_manifest.py`, sin listas hardcodeadas |
| `Hoteles/Deploy/build.bat` | Modificado — agrega paso [4/4] que corre `--self-test` post-build |
| `Hoteles/Deploy/__init__.py` | Nuevo — hace de `Deploy/` un paquete Python |
| `Hoteles/Deploy/build_manifest.py` | Nuevo — manifest declarativo del bundle (estilo `package.json`) |
| `Hoteles/Deploy/smoke_test.py` | Nuevo — checks declarativos post-build de módulos críticos |
| `Hoteles/main.py` | Modificado — detecta `--self-test` en `sys.argv`, corre smoke test y sale; además `run_checks()` y fix encoding UTF-8 |
| `Hoteles/Core/controller.py` | Modificado — `_excel_path()` con `sys.frozen` + `sys._MEIPASS` |
| `Hoteles/debug_config.py` | Modificado — agregado flag `DEBUG_EXCEL_PARSING` |
| `Hoteles/ExtractorDatos/utils.py` | Modificado — prints de debug bajo `DEBUG_EXCEL_PARSING` |
| `Hoteles/.env` | Movido desde raíz del repo (`Crawl-Compare/.env`) a `Hoteles/.env` |

---

## Arquitectura del Deploy

```
Hoteles/
├── Deploy/
│   ├── startup_check.py   ← checks antes de levantar la UI
│   ├── crawl_compare.spec ← config de PyInstaller
│   ├── build.bat          ← script de build (solo para el dev)
│   ├── __init__.py
│   └── dist/
│       └── CrawlCompare.exe  ← output del build (~241MB)
├── main.py                ← run_checks() como primera línea
└── .env                   ← viaja junto al .exe (embebido en _MEIPASS)
```

### Cómo buildear
Desde Anaconda Prompt, correr `build.bat` o directamente:
```bat
cd Hoteles/
conda run -n crawler pyinstaller "Deploy/crawl_compare.spec" --distpath "Deploy/dist" --workpath "Deploy/build"
```

> **Importante**: `build.bat` ahora corre **automáticamente** el smoke test (`CrawlCompare.exe --self-test`) como paso [4/4] después de compilar. Si algún check falla, el build se considera inválido y aborta. Esto evita que se distribuya un `.exe` con un bundling roto que recién explote en runtime del usuario.

---

## startup_check.py — Lógica de checks

### `_get_base_dir()`
- En `.exe` (`sys.frozen=True`): retorna `sys._MEIPASS` — carpeta temporal donde PyInstaller extrae los archivos declarados en `datas` del `.spec`
- En dev: retorna `Hoteles/` relativo al archivo

### `check_env()`
- Busca `.env` en `base_dir`
- Si no existe → `messagebox.showerror` + `sys.exit(1)`
- Si existe → `load_dotenv(env_path)` carga las keys al entorno

### `check_playwright()`
- En `.exe`: setea `PLAYWRIGHT_BROWSERS_PATH` apuntando a los browsers embebidos en `_MEIPASS` y retorna — no instala nada
- En dev: verifica si `AppData/Local/ms-playwright/chromium-*/chrome.exe` existe, si no lo instala con ventana de progreso

---

## crawl_compare.spec — Decisiones clave

### `collect_all()` en vez de `collect_data_files()` + `collect_submodules()`
Razón: `collect_data_files` solo incluye archivos declarados por el paquete mismo. Dependencias transitivas como `playwright_stealth` y `fake_http_header` tienen archivos `.js` y carpetas `data/` que no se incluían, causando `FileNotFoundError` en runtime.

`collect_all(pkg)` trae `datas + binaries + hiddenimports` en un solo llamado, cubriendo el árbol completo.

Paquetes cubiertos con `collect_all`:
- `customtkinter` — themes JSON y assets
- `crawl4ai` — snippets `.js`
- `playwright` — driver `node.exe` + package JS
- `playwright_stealth` — scripts `.js` de evasión
- `fake_http_header` — carpeta `data/`

### Chromium embebido
```python
(r"C:\Users\...\ms-playwright\chromium-1181", r"playwright/driver/package/.local-browsers/chromium-1181")
```
Chromium (~338MB) se embebe directamente en el `.exe`. Tu amigo no necesita `playwright install` ni nada. Agrega ~150MB al binario final.

**Nota importante**: el path de Chromium apunta a tu `AppData` local. Si Playwright se actualiza y cambia la revisión (ej: `chromium-1182`), hay que actualizar este path en el `.spec` y recompilar.

### `.env` embebido en `_MEIPASS`
```python
(os.path.join(ROOT, ".env"), ".")
```
El `.env` se extrae en la raíz de `_MEIPASS`. `startup_check.py` lo lee desde `sys._MEIPASS` con `_get_base_dir()`.

### Excel embebido en `_MEIPASS/Data/`
```python
(os.path.join(ROOT, "Data", "Extracto_prueba2.xlsx"), "Data")
```
`controller.py` usa `sys._MEIPASS / "Data" / "Extracto_prueba2.xlsx"` cuando `sys.frozen=True`.

---

## Fixes aplicados durante el proceso

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
**Fix**: agregar `tiktoken` y `tiktoken_ext` a `PACKAGES_COLLECT_ALL` en `build_manifest.py`. También se sumó `litellm` por las dudas (mismo patrón plugin-style, podría reventar en cualquier momento).
**Prevención**: el smoke test ahora ejecuta `tiktoken.get_encoding("cl100k_base")` como check obligatorio post-build. Si alguna vez se rompe de nuevo, el `build.bat` aborta antes de que el `.exe` llegue al usuario.

---

## Manifest declarativo (`build_manifest.py`)

Antes el `.spec` tenía listas hardcodeadas mezcladas con lógica de PyInstaller. Cada vez que había que agregar un paquete o un hidden import, había que tocar el `.spec` directo. Eso es frágil — el `.spec` es un script Python que se evalúa, no un manifiesto.

La idea es separar **qué entra al bundle** (declarativo) de **cómo se arma el bundle** (imperativo, PyInstaller). Misma filosofía que `package.json` vs `node_modules`: el manifest dice qué querés, el tooling lo resuelve.

### Las 6 listas del manifest

| Lista | Cuándo tocarla |
|-------|----------------|
| `PACKAGES_COLLECT_ALL` | Paquetes pesados que necesitan `datas + binaries + hiddenimports` enteros (customtkinter, crawl4ai, playwright, tiktoken). Cuando agregás una lib que falla con `FileNotFoundError` o `ModuleNotFoundError` de submódulos. |
| `PACKAGES_SUBMODULES` | Cuando solo necesitás `collect_submodules()` (sin datas/binarios). Útil para libs puramente Python con discovery dinámico. |
| `EXTRA_HIDDEN_IMPORTS` | Imports puntuales que PyInstaller no detecta (ej: módulos cargados por nombre con `importlib`). |
| `EXTRA_DATAS` | Archivos sueltos: `.env`, `Extracto_prueba2.xlsx`, etc. Tuplas `(src, dest_en_MEIPASS)`. |
| `EXTERNAL_BINARIES` | Binarios externos al venv que se embeben en el `.exe` (Chromium, drivers). |
| `EXCLUDES` | Paquetes a **excluir** del análisis para bajar tamaño (ej: `tkinter`, módulos de testing). |

Para agregar una dependencia nueva: editás `build_manifest.py`, no tocás el `.spec`.

---

## Smoke test post-build (`smoke_test.py` + `--self-test`)

### Cómo funciona
1. `main.py` chequea `sys.argv` al arrancar. Si encuentra `--self-test`, importa `smoke_test.run_smoke_test()` y sale **antes** de levantar la UI.
2. El smoke test corre una lista declarativa de checks — cada uno intenta importar/usar un módulo crítico que ya nos rompió antes (tiktoken cl100k_base, playwright sync, crawl4ai, etc.).
3. Si **todos** pasan: exit code 0. Si **alguno** falla: exit code != 0 con el motivo.
4. `build.bat` corre `CrawlCompare.exe --self-test` como paso [4/4] del build. Si el exit code no es 0, marca el build como **inválido** y aborta.

### Regla de oro
> **Cada vez que se descubra un bug de bundling (módulo que falta, plugin que no registra, encoding que no carga), agregar un check al `smoke_test.py`.**

Si no, el bug puede volver en silencio cuando se actualice una dependencia o se agregue una feature, y recién explota en la máquina del usuario. El smoke test es la red de seguridad — sin él, cada build es ruleta rusa.

---

## Estado actual del .exe (sesión actual)

| Item | Estado |
|------|--------|
| App arranca | ✅ |
| `.env` se carga | ✅ |
| Chromium se encuentra | ✅ |
| Excel se carga | ✅ |
| UI se muestra correctamente | ✅ |
| Encoding UTF-8 | ✅ |
| Scraping web (comparación) | ✅ — resuelto en Fix 8 (tiktoken `cl100k_base`) |

---

## Problema pendiente — Scraping no obtiene datos ✅ RESUELTO

**Resolución**: era el bug de `tiktoken_ext` documentado en **Fix 8**. El `LLMExtractionStrategy` de Crawl4AI tokeniza el markdown con `tiktoken.get_encoding("cl100k_base")` antes de mandarlo al LLM; como el submódulo `tiktoken_ext` no estaba en el bundle, la lista de plugins venía vacía y el encoding nunca se resolvía. El scraping fallaba silenciosamente porque el error se enmascaraba como "no se pudieron obtener datos" en la capa de reintentos.

Fix aplicado: `tiktoken` + `tiktoken_ext` en `PACKAGES_COLLECT_ALL` del `build_manifest.py`, más un check en `smoke_test.py` que verifica `get_encoding("cl100k_base")` post-build para que no se repita.
