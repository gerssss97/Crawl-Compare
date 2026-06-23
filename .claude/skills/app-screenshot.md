# app-screenshot

Lanza la app PySide6 completa, espera a que renderice, toma un screenshot automático y lo lee para análisis visual. Permite a Claude ver exactamente cómo luce la UI sin intervención manual del usuario.

## Cuándo usar

- Antes de proponer cambios visuales (spacing, layout, colores)
- Para verificar que un cambio de UI quedó bien
- Para detectar problemas visuales (overflow, clipping, elementos cortados)
- Cuando el usuario pregunta "¿cómo se ve?" o "¿podés ver la app?"

## Entorno

- **Python**: `conda run -n crawler python` (miniconda en `C:\Users\German\miniconda3`)
- **Captura**: `PIL.ImageGrab` (disponible en el env `crawler`)
- **Output**: `app_qt_screenshot.png` en `.claude/skills/scripts/`

## Procedimiento

### 1. Ejecutar con PowerShell (desde la raíz del proyecto)

El script ya existe en `.claude/skills/scripts/screenshot.py`, ejecutarlo directamente:

```powershell
conda run -n crawler python .claude/skills/scripts/screenshot.py
```

> **Nota**: `conda run` devuelve exit code 255 cuando la app Qt cierra. Eso es **esperado y normal** — no indica error. El screenshot ya fue guardado antes de que el proceso termine.

### 2. Leer el screenshot

Una vez generado `app_qt_screenshot.png`, leerlo con el tool `Read` para análisis visual:

```
Read: C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts\app_qt_screenshot.png
```

## Detalles técnicos clave

- **`sys.path` doble**: tanto `C:\...\Hoteles` (raíz del proyecto) como `C:\...\Hoteles\Hoteles` deben estar en el path para resolver módulos internos (`UI_qt`, `core`, etc.)
- **`os.chdir(hoteles_dir)`**: obligatorio, la app resuelve paths relativos desde `Hoteles/`
- **`QApplication.instance() or QApplication(sys.argv)`**: evita crear una segunda instancia si ya existe una
- **`MainWindow` standalone**: la clase `MainWindow` en `UI_qt/interfaz_qt.py` no requiere argumentos externos
- **`threading.Thread` + `time.sleep(4)`**: 4 segundos es suficiente para que PySide6 renderice completamente antes de capturar
- **`PIL.ImageGrab.grab(bbox=...)`**: captura la ventana usando coordenadas reales de pantalla (`win.pos().x/y` + `win.width/height`)
- **Exit code 255**: comportamiento normal de `conda run` al terminar una app Qt con `app.quit()`; buscar la línea `SCREENSHOT_OK` en stdout para confirmar éxito

## Errores conocidos

### Screenshot en negro o vacío
**Causa**: La ventana no tuvo tiempo de renderizar antes de la captura.  
**Fix**: Aumentar el `time.sleep(4)` en el thread `capture` a 5 o 6 segundos.

### `ModuleNotFoundError: No module named 'UI_qt'`
**Causa**: `sys.path` no incluye `Hoteles/Hoteles/` o el `os.chdir` no se ejecutó.  
**Fix**: Verificar que ambas entradas de `sys.path` y el `os.chdir` estén al inicio del script.

### `ModuleNotFoundError: No module named 'PySide6'`
**Causa**: Se está usando el Python del sistema en vez del env `crawler`.  
**Fix**: Usar siempre `conda run -n crawler python ...` en lugar de llamar a `python` directamente.

### La ventana se abre pero el screenshot captura el fondo de escritorio
**Causa**: La ventana Qt no terminó de pintarse o quedó detrás de otra ventana.  
**Fix**: Agregar `win.raise_()` y `win.activateWindow()` justo después de `win.show()`.

## Ver también

- [docs/ui/troubleshooting-ctk.md](../../docs/ui/troubleshooting-ctk.md) - Problemas visuales (legacy CTk, referencia histórica)
- [Hoteles/UI_qt/interfaz_qt.py](../../Hoteles/UI_qt/interfaz_qt.py) - Interfaz principal PySide6
- [docs/arquitectura/tree-directory.md](../../docs/arquitectura/tree-directory.md) - Estructura del proyecto
