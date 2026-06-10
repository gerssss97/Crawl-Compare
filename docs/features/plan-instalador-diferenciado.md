# Plan: Instalador diferenciado (onedir + ruta a instalador real)

## Estado: PLANIFICADO 📝

Fecha de planificación: 2026-06-09
Branch sugerido: `feature/onedir-distribution`

---

## Contexto

Hoy el `.exe` se buildea con PyInstaller `--onefile`: todo el bundle de 258 MB queda comprimido en un único archivo que descomprime `_MEIPASS` en `%TEMP%\_MEI<random>\` cada vez que se ejecuta. Esto genera tres problemas concretos detectados al validar la feature de splash+logging:

1. **Arranque lento la primera vez** (5-15 seg) — durante ese tiempo el usuario ve solo una consola negra, sin ningún feedback. Aunque agregamos el splash, este no puede aparecer **antes** de que Python termine de descomprimirse.

2. **Bug del Excel embebido persistido** — `excel_resolver` guarda en `config.json` el path del Excel default (`_MEI81562\Data\Extracto_prueba2.xlsx`). Al siguiente arranque, PyInstaller crea otro `_MEI<random>` y el path queda apuntando a una carpeta que ya no existe. Cada arranque loguea:
   ```
   [excel_resolver] Último Excel (..._MEI81562\...) ya no existe. Limpiando config.
   ```

3. **Cualquier path interno del bundle es inestable** — no se puede persistir nada de la carpeta del bundle entre ejecuciones. Si en el futuro se agrega cache de cualquier tipo dentro de `_MEIPASS`, va a fallar igual.

Este plan implementa **Opción 2 (pasar a `--onedir`)** como solución de corto plazo, **dejando preparado el terreno para Opción 3 (instalador real con Inno Setup)** cuando se quiera profesionalizar la distribución.

---

## Decisión actual

**Opción 2 (onedir)** ahora. **Opción 3 (instalador real)** queda preparado como fase 2 dentro del mismo plan.

Razones para no saltar directo a Opción 3:
- Inno Setup requiere instalar herramienta nueva, aprender el lenguaje `.iss`, decidir paths de instalación y testing del wizard. Es 2-3 sesiones.
- Onedir resuelve los 3 problemas detectados HOY con ~15 líneas de cambio.
- Onedir es **prerequisito técnico** de Opción 3: Inno Setup empaqueta una carpeta, no un onefile.
- Pasar de Opción 1 → 2 → 3 incremental es más seguro que saltarse el paso intermedio.

---

## Fase 1 — Pasar a `--onedir`

### Cambios al `crawl_compare.spec`

Hoy el spec termina con un solo bloque `EXE(...)` con `console=True`. Para onedir hay que:

1. Cambiar `EXE(...)`: sacar `a.binaries`, `a.datas` del constructor (no van más adentro del EXE).
2. Agregar bloque `COLLECT(...)` al final que junta el `.exe` + binaries + datas en una carpeta de salida.

Estructura final esperada:

```python
exe = EXE(
    pyz,
    a.scripts,
    [],                  # ← NO a.binaries, NO a.datas (van a COLLECT)
    exclude_binaries=True,  # ← NUEVO: marca el EXE como onedir
    name="CrawlCompare",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,        # mantener True mientras se testea
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CrawlCompare",  # nombre de la CARPETA de salida
)
```

Salida resultante en `dist/`:
```
dist/
└── CrawlCompare/
    ├── CrawlCompare.exe        ← este es el que el usuario abre
    ├── _internal/
    │   ├── base_library.zip
    │   ├── python312.dll
    │   ├── UI/assets/icons/    ← assets visibles, paths estables
    │   ├── Data/Extracto_prueba2.xlsx
    │   ├── .env
    │   ├── playwright/driver/.local-browsers/chromium-1181/
    │   └── ... (cientos de DLLs)
    └── (algunos DLLs pueden quedar en root del onedir según versión de PyInstaller)
```

### Cambios al `build.bat`

El smoke test post-build apunta hoy a `dist\CrawlCompare.exe`. Con onedir, el path cambia:

```bat
:: Antes
"%DIST_DIR%\CrawlCompare.exe" --self-test

:: Después
"%DIST_DIR%\CrawlCompare\CrawlCompare.exe" --self-test
```

Conviene declarar el path como variable al inicio del script para no hardcodearlo dos veces.

### Validación del comportamiento de `sys._MEIPASS` en onedir

**CRÍTICO**: confirmar antes de validar el resto.

En onefile, `sys._MEIPASS` apunta a `%TEMP%\_MEI<random>\` (carpeta temporal de extracción).

En onedir, **PyInstaller setea `sys._MEIPASS` apuntando a la carpeta `_internal/` adyacente al `.exe`**. Es decir, `<dist>/CrawlCompare/_internal/`.

Esto significa que **el código actual no debería requerir cambios**: todos los lugares que hoy hacen `os.path.join(sys._MEIPASS, "Data", "...")` van a seguir funcionando porque `_MEIPASS` sigue siendo "la raíz donde están los datas". Solo cambia el path físico (estable ahora, antes random).

**Cómo validar**: build de prueba + corre el `.exe` con `--self-test` + verificá que los 9 checks pasan. Si pasan, el código está bien.

### Revisión de archivos que asumen el modelo

Estos 10 archivos tienen referencias a `sys.frozen` o `sys._MEIPASS`. **No deberían requerir cambios pero hay que confirmarlo uno por uno**:

| Archivo | Uso de `_MEIPASS` o `frozen` | Riesgo en onedir |
|---|---|---|
| `Hoteles/Deploy/smoke_test.py` | `_MEIPASS` para Excel y íconos | Bajo — sigue siendo válido |
| `Hoteles/Deploy/startup_check.py` | `_MEIPASS` para PLAYWRIGHT_BROWSERS_PATH | Bajo — sigue siendo válido |
| `Hoteles/Core/excel_resolver.py` | `_MEIPASS` para Data dir | **Medio** — el bug del Excel se resuelve solo al tener path estable |
| `Hoteles/Core/services/config_service.py` | `sys.frozen` para decidir dónde escribir config | Bajo — sigue siendo válido |
| `Hoteles/debug_config.py` | `sys.frozen` para forzar flags | Bajo |
| `Hoteles/main.py` | `sys.frozen` para crear splash | Bajo |
| `Hoteles/Deploy/error_logger.py` | `sys.executable.parent` para log dir | Bajo |
| `Hoteles/Deploy/splash.py` | Ninguno directo | N/A |
| `Hoteles/Deploy/build_manifest.py` | Ninguno (es el manifest) | N/A |
| Docs varios | Referencias documentales | N/A |

### Verificación de Fase 1

1. **Build limpio**: borrar `dist/` y `build/`, correr `build.bat`.
2. **Smoke test pasa 9/9** desde el path nuevo del .exe.
3. **Doble click al .exe** desde el explorador de Windows:
   - Arranque debería ser visiblemente más rápido que onefile.
   - Splash aparece **inmediatamente** (no hay descompresión previa).
   - Log `crawl_compare_YYYYMMDD.log` se crea junto al `.exe`, en la misma carpeta que `_internal/`.
4. **Confirmar fix del bug del Excel**: abrir la app, cerrar, abrir de nuevo. Esta vez NO debería aparecer en el log `[excel_resolver] Último Excel (..._MEI...) ya no existe`.
5. **Confirmar persistencia normal de config**: cambiar Excel desde la UI, cerrar, reabrir. Debería recordar la última selección.
6. **Test de portabilidad**: mover la carpeta `CrawlCompare/` completa a otro lugar (ej. Desktop). Debería seguir funcionando.
7. **Test de fragilidad esperada**: copiar SOLO el `.exe` sin `_internal/` a otro lugar. Debería fallar (esperado, documentar para el usuario).

### Distribución de la Fase 1

- **Formato**: `.zip` con la carpeta `CrawlCompare/` completa.
- **README.txt** dentro del zip: "Descomprimí donde quieras y hacé doble click en `CrawlCompare/CrawlCompare.exe`."
- **NO incluir `.env`** en el zip — debe ir aparte por seguridad (contiene `GROQ_API_KEY`).
- Tamaño esperado del `.zip` comprimido: ~280 MB (similar al onefile pero con archivos individuales).

### Cambios mínimos a documentar

- `docs/deploy/build-deploy.md`: actualizar el output esperado del build (carpeta en vez de archivo único).
- `docs/features/TODO.md`: marcar el bug del Excel persistido como **resuelto por path estable**.

---

## Fase 2 — Instalador real con Inno Setup

**Cuándo abordar**: cuando la distribución vía `.zip` empiece a generar fricción con usuarios no técnicos, o cuando quieras updates automáticos.

### Por qué Inno Setup y no NSIS

| Aspecto | Inno Setup | NSIS |
|---|---|---|
| Curva de aprendizaje | Lenguaje `.iss` declarativo, sencillo | Lenguaje propio más imperativo, más verboso |
| GUI editor | Sí (Inno Script Studio) | No oficial |
| Documentación | Excelente, ejemplos abundantes | Buena pero más técnica |
| Tamaño output | Comparable | Comparable |
| Plugins/extensiones | Suficientes para casos comunes | Más amplios (overkill para esto) |
| Comunidad Python+PyInstaller | Inno es el default de facto | Menos referencias |

**Recomendación**: Inno Setup.

### Lo que el instalador debe hacer

1. **Wizard de bienvenida** con licencia (opcional) y selección de directorio de instalación.
2. **Instalación por defecto en `%LOCALAPPDATA%\CrawlCompare\`** — no requiere permisos de admin.
3. **Copiar la carpeta onedir completa** a la ubicación elegida.
4. **Crear shortcuts**:
   - Menú inicio (siempre).
   - Escritorio (checkbox opcional, marcado por default).
5. **Registrar en "Agregar/quitar programas"** con uninstaller automático.
6. **Opción "Iniciar ahora"** al final del wizard.

### Salida del build

```
Deploy/
└── dist/
    ├── CrawlCompare/             ← onedir (input del instalador)
    └── CrawlCompareSetup.exe     ← output del instalador (~280 MB)
```

El usuario solo recibe `CrawlCompareSetup.exe`. El wizard se encarga del resto.

### Cambios al `build.bat`

Agregar paso 5 después del smoke test:

```bat
:: Paso 5: Empaquetar con Inno Setup
echo [5/5] Empaquetando con Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Deploy\crawl_compare.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup falló.
    pause
    exit /b 1
)
echo      OK
```

### Estructura del `.iss`

Archivo nuevo: `Hoteles/Deploy/crawl_compare.iss`. Esqueleto:

```iss
[Setup]
AppName=Crawl Compare
AppVersion=1.0.0
AppPublisher=German Lucero
DefaultDirName={localappdata}\CrawlCompare
DefaultGroupName=Crawl Compare
OutputDir=dist
OutputBaseFilename=CrawlCompareSetup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Files]
Source: "dist\CrawlCompare\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Crawl Compare"; Filename: "{app}\CrawlCompare.exe"
Name: "{commondesktop}\Crawl Compare"; Filename: "{app}\CrawlCompare.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el Escritorio"; GroupDescription: "Opciones adicionales:"

[Run]
Filename: "{app}\CrawlCompare.exe"; Description: "Ejecutar Crawl Compare ahora"; Flags: postinstall nowait skipifsilent
```

### Cuestiones a resolver al abordar Fase 2

1. **`.env` con `GROQ_API_KEY`**: ¿se distribuye dentro del instalador, o el usuario lo configura post-instalación desde la UI? Recomendación: prompt en el wizard que pida la API key y la escriba al `.env` después.
2. **Firma de código**: para evitar warnings de SmartScreen ("Windows protegió tu PC"). Requiere certificado EV (~USD 200-400/año).
3. **Updates automáticos**: ¿se implementa "check for updates" en la app, o el usuario descarga manualmente el nuevo `Setup.exe`? Recomendación: empezar con manual, evaluar Squirrel.Windows si crece la base de usuarios.
4. **Migración de config**: el instalador NO debe pisar `%APPDATA%/CrawlCompare/config.json`. Verificar que upgrades preserven el config.

### Verificación de Fase 2

1. Build completo: `build.bat` genera `dist/CrawlCompareSetup.exe`.
2. Ejecutar `CrawlCompareSetup.exe` en una VM limpia (sin la app instalada).
3. Wizard completa sin errores.
4. App quedó instalada en `%LOCALAPPDATA%\CrawlCompare\`.
5. Shortcuts en menú inicio y escritorio funcionan.
6. "Agregar/quitar programas" muestra la entrada con uninstaller.
7. Uninstall limpia todo excepto `%APPDATA%/CrawlCompare/config.json` (decisión: ¿preservar o pedir confirmación?).
8. Re-instalar versión nueva preserva config.

---

## Archivos a modificar/crear

### Fase 1 (onedir)
- `Hoteles/Deploy/crawl_compare.spec` — agregar `COLLECT(...)` + `exclude_binaries=True` en `EXE(...)`.
- `Hoteles/Deploy/build.bat` — ajustar path del smoke test.
- `docs/deploy/build-deploy.md` — actualizar output esperado.
- `docs/features/TODO.md` — marcar bug del Excel como resuelto.

### Fase 2 (instalador)
- `Hoteles/Deploy/crawl_compare.iss` — **nuevo**, script Inno Setup.
- `Hoteles/Deploy/build.bat` — agregar paso 5 (Inno Setup).
- `docs/deploy/build-deploy.md` — documentar flujo del instalador.
- (Opcional) `Hoteles/Deploy/installer_assets/` — íconos del instalador, banner del wizard, licencia.

---

## Riesgos y mitigaciones

### Fase 1

| Riesgo | Mitigación |
|---|---|
| `_MEIPASS` no apunta donde esperamos en onedir | Smoke test ya valida assets — captura el problema antes de distribuir. |
| Algún DLL queda fuera del `_internal/` y falla en runtime | Smoke test exhaustivo. Si falla, agregar entrada a `EXTRA_DATAS` o `EXTERNAL_BINARIES`. |
| Usuario mueve solo el `.exe` sin `_internal/` y no arranca | README en el `.zip` explicando que se mueve la **carpeta entera**. |
| Antivirus marca alguna DLL como sospechosa | Listar en `EXCLUDES` las DLLs sospechosas. Si persiste, considerar firma de código (Fase 2). |

### Fase 2

| Riesgo | Mitigación |
|---|---|
| SmartScreen bloquea el instalador sin firma | Documentar "Más info → Ejecutar de todas formas" para usuarios. Largo plazo: firmar. |
| Wizard rompe en versiones viejas de Windows | Inno Setup soporta Win7+; declarar `MinVersion=6.1` para evitar instalación en versiones no soportadas. |
| Uninstall borra config del usuario | Excluir explícitamente `%APPDATA%/CrawlCompare/` del uninstall. |
| Update sobre versión anterior pisa config | Inno Setup detecta upgrades por `AppId`. Configurar GUID estable. |

---

## Checklist accionable

### Fase 1 (cuando se aborde)
- [ ] Modificar `crawl_compare.spec`: `EXE(exclude_binaries=True)` + `COLLECT(...)`.
- [ ] Build de prueba: validar que `dist/CrawlCompare/` se genera y contiene `.exe` + `_internal/`.
- [ ] Confirmar con `--self-test` que `_MEIPASS` apunta a `_internal/` y los 9 checks pasan.
- [ ] Ajustar `build.bat` con el nuevo path del smoke test.
- [ ] Doble click al `.exe`, validar arranque rápido y sin descompresión.
- [ ] Cerrar y reabrir, verificar que el bug del Excel embebido desapareció.
- [ ] Actualizar docs.
- [ ] Decidir formato de distribución (`.zip` directo o esperar Fase 2).

### Fase 2 (cuando se aborde)
- [ ] Instalar Inno Setup 6.
- [ ] Crear `Hoteles/Deploy/crawl_compare.iss` con esqueleto del plan.
- [ ] Decidir manejo del `.env` (en wizard o post-instalación).
- [ ] Agregar paso 5 a `build.bat`.
- [ ] Build completo, verificar que `CrawlCompareSetup.exe` se genera.
- [ ] Test en VM limpia: instalación, shortcut, uninstall, upgrade.
- [ ] Decidir si vale la pena firma de código.

---

## Ver también

- [docs/features/splash-screen-y-logging.md](splash-screen-y-logging.md) — feature que destapó los problemas que motivan este plan.
- [docs/features/TODO.md](TODO.md) — bug del Excel persistido (se resuelve en Fase 1).
- [docs/deploy/build-deploy.md](../deploy/build-deploy.md) — proceso de build actual.
