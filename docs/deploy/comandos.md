# Comandos y Scripts — Deploy CrawlCompare

---

## Buildear el .exe

### Opción A — `build.bat` (RECOMENDADO)

Compila **y** corre el smoke test automáticamente. Si el smoke test falla, aborta el build.

```bat
cd Hoteles
Deploy\build.bat
```

O doble click en `Hoteles/Deploy/build.bat` desde Anaconda Prompt.

Output esperado:
```
[1/4] Verificando PyInstaller... OK
[2/4] Limpiando builds anteriores... OK
[3/4] Compilando .exe...
[4/4] Corriendo smoke test del .exe...
[SMOKE] OK   tiktoken encoding — cl100k_base loaded (100277 tokens)
[SMOKE] OK   playwright — import OK
...
[SMOKE] ✅ TODOS LOS CHECKS PASARON (8/8)
Build exitoso!
```

### Opción B — Manual (dos pasos)

Útil si querés separar la salida de PyInstaller del smoke test, o re-correr solo uno de los dos.

```bat
cd Hoteles
:: Paso 1 — compilar
conda run -n crawler pyinstaller "Deploy/crawl_compare.spec" --distpath "Deploy/dist" --workpath "Deploy/build"

:: Paso 2 — validar el bundle
Deploy\dist\CrawlCompare.exe --self-test
```

> El comando de PyInstaller **solo compila**. No corre validación. El `--self-test` es un flag del propio `.exe` que dispara los checks de [smoke_test.py](../../Hoteles/Deploy/smoke_test.py) en vez de levantar la UI.

---

## Testear el .exe capturando errores

### Desde Anaconda Prompt (cmd) — RECOMENDADO

```bat
cd Hoteles\Deploy\dist
CrawlCompare.exe > output.log 2>&1
type output.log
```

Redirige stdout y stderr a `output.log` — útil porque con `console=True` la ventana negra se cierra antes de que puedas leer el error.

### Desde PowerShell

```powershell
cd Hoteles\Deploy\dist
.\CrawlCompare.exe *> output.log
Get-Content output.log
```

El `*>` en PowerShell captura **todos** los streams (stdout, stderr, warnings) a la vez. Evitar `2>&1` con ejecutables nativos en PS 5.1 — wrappea stderr en `NativeCommandError` y puede perder output.

### Notas

- **No usar terminal integrada de VSCode** para correr el `.exe` — tiene problemas con apps GUI de Windows (proceso queda colgado, ventana se abre en background). Usar Anaconda Prompt o PowerShell standalone.
- Si querés ver el output en tiempo real **y** guardarlo (PowerShell): `.\CrawlCompare.exe 2>&1 | Tee-Object -FilePath output.log`

---

## Correr el smoke test manualmente

```bat
Hoteles\Deploy\dist\CrawlCompare.exe --self-test
```

Corre la lista de checks declarativos definida en `Hoteles/Deploy/smoke_test.py` (tiktoken `cl100k_base`, playwright, crawl4ai, etc.) y sale con exit code 0 si todo OK, o != 0 si falla algún módulo.

**Cuándo usarlo**:
- Después de un build manual (sin `build.bat`), para validar que el bundle quedó sano.
- Cuando sospechás que falta algo en el bundle (un import roto, un plugin que no carga) pero no querés recompilar para investigar — el `--self-test` te da el diagnóstico en segundos.
- En CI o pre-distribución, como gate antes de mandarle el `.exe` al usuario.

> El `build.bat` ya lo corre automáticamente como paso [4/4]. Este comando es para correrlo a mano.

---

## Instalar PyInstaller en el env (solo primera vez)

```bash
conda run -n crawler pip install pyinstaller
```

---

## Limpiar build anterior y recompilar desde cero

```bash
rm -rf Hoteles/Deploy/build Hoteles/Deploy/dist
conda run -n crawler pyinstaller "Deploy/crawl_compare.spec" --distpath "Deploy/dist" --workpath "Deploy/build"
```

---

## Archivos del deploy — Resumen

### `Hoteles/Deploy/startup_check.py`
Corre antes de que levante la UI. Hace dos checks:
- **`check_env()`** — busca el `.env` en `sys._MEIPASS` (`.exe`) o `Hoteles/` (dev). Si no existe, muestra error y cierra.
- **`check_playwright()`** — en `.exe` setea `PLAYWRIGHT_BROWSERS_PATH` apuntando a Chromium embebido. En dev verifica si Chromium está instalado en `AppData/ms-playwright/`, si no lo instala con una ventanita de progreso.

### `Hoteles/Deploy/crawl_compare.spec`
Configuración de PyInstaller. Define qué entra en el `.exe`:
- `collect_all()` para `customtkinter`, `crawl4ai`, `playwright`, `playwright_stealth`, `fake_http_header`
- Chromium binario completo desde `AppData/Local/ms-playwright/chromium-1181/`
- Driver de Playwright (`node.exe` + package JS)
- `Extracto_prueba2.xlsx` embebido en `_MEIPASS/Data/`
- `.env` embebido en raíz de `_MEIPASS`
- `console=True` mientras se testea — cambiar a `False` antes de distribuir

### `Hoteles/Deploy/build.bat`
Script Windows para buildear. Verifica que conda esté en el PATH, instala PyInstaller si falta, limpia builds anteriores y corre PyInstaller con el `.spec`.

### `Hoteles/Deploy/__init__.py`
Vacío. Hace que `Deploy/` sea un paquete Python importable desde `main.py`.

### `Hoteles/Deploy/dist/CrawlCompare.exe`
El ejecutable final (~241MB). Contiene Python, todas las dependencias, Chromium y el Excel embebidos. Tu amigo solo necesita este archivo + el `.env` con las API keys.
