# app-screenshot

Lanza la app CTk completa, espera a que renderice, toma un screenshot automático y lo lee para análisis visual. Permite a Claude ver exactamente cómo luce la UI sin intervención manual del usuario.

## Cuándo usar

- Antes de proponer cambios visuales (spacing, layout, colores)
- Para verificar que un cambio de UI quedó bien
- Para detectar problemas visuales (overflow, clipping, elementos cortados)
- Cuando el usuario pregunta "¿cómo se ve?" o "¿podés ver la app?"

## Entorno

- **Python**: `C:\Users\German Lucero\anaconda3\envs\crawler\python.exe`
- **Captura**: `PIL.ImageGrab` (disponible en el env `crawler`)
- **Output**: `app_screenshot.png` en `.claude/skills/scripts/`

## Procedimiento

### 1. Ejecutar con PowerShell

El script ya existe en `.claude/skills/scripts/screenshot.py`, ejecutarlo directamente:

```powershell
$pyexe = "C:\Users\German Lucero\anaconda3\envs\crawler\python.exe"
& $pyexe "C:\Users\German Lucero\ProyectosChino\Crawl-Compare\.claude\skills\scripts\screenshot.py"
```

### 2. Leer el screenshot

Una vez generado `app_screenshot.png`, leerlo con el tool `Read` para análisis visual.

```
Read: c:\Users\German Lucero\ProyectosChino\Crawl-Compare\.claude\skills\scripts\app_screenshot.png
```

## Detalles técnicos clave

- **`os.chdir(hoteles_dir)`**: obligatorio, la app resuelve paths relativos desde `Hoteles/`
- **`sys.path` doble**: tanto la raíz del proyecto como `Hoteles/` deben estar en el path para resolver `debug_config` y otros módulos internos
- **`root = ctk.CTk()` + `CrawlCompareGUI(root)`**: la clase no es standalone, necesita la root window como argumento
- **`root.after(3000, ...)`**: 3 segundos es suficiente para que CTk renderice completamente
- **`PIL.ImageGrab.grab(bbox=...)`**: captura solo la ventana usando coordenadas reales de pantalla (`winfo_rootx/y/width/height`)

## Errores conocidos

### `ModuleNotFoundError: No module named 'debug_config'`
**Causa**: `sys.path` no incluye `Hoteles/`.  
**Fix**: Asegurarse de agregar `hoteles_dir` al `sys.path`.

### `CrawlCompareGUI.__init__() missing 1 required positional argument: 'root'`
**Causa**: La clase requiere `ctk.CTk()` como argumento.  
**Fix**: Crear `root = ctk.CTk()` y pasarlo: `CrawlCompareGUI(root)`.

### Screenshot en negro o vacío
**Causa**: La ventana no tuvo tiempo de renderizar.  
**Fix**: Aumentar el delay en `root.after(...)` de 3000 a 4000ms.

### `ModuleNotFoundError: No module named 'customtkinter'`
**Causa**: Se está usando el Python del sistema en vez del env `crawler`.  
**Fix**: Usar la ruta completa `C:\Users\German Lucero\anaconda3\envs\crawler\python.exe`.

## Ver también

- [ui-preview.md](ui-preview.md) - Preview de componentes individuales
- [docs/ui/troubleshooting-ctk.md](../../docs/ui/troubleshooting-ctk.md) - Problemas visuales CTk
- [Hoteles/UI/interfaz_ctk.py](../../Hoteles/UI/interfaz_ctk.py) - Interfaz principal
