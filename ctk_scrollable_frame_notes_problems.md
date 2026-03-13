# CTkScrollableFrame y MouseWheel — Notas de arquitectura

## El problema

Si tenés un `CTkScrollableFrame` (ej: panel izquierdo) y dentro de él un widget que abre
un `CTkToplevel` con otro `CTkScrollableFrame` (ej: un dropdown), scrollear sobre el
dropdown también scrollea el panel de fondo.

## Por qué ocurre

`CTkScrollableFrame` usa `bind_all("<MouseWheel>", ...)` — un binding global que dispara
para cualquier evento de scroll en toda la aplicación. Para discriminar, usa una guardia:

```python
def _mouse_wheel_all(self, event):
    if self.check_if_master_is_canvas(event.widget):
        # scrollear este frame
```

```python
def check_if_master_is_canvas(self, widget):
    if widget == self._parent_canvas:
        return True
    elif widget.master is not None:
        return self.check_if_master_is_canvas(widget.master)  # sube por .master
    else:
        return False
```

Sube recursivamente por `.master` para ver si el widget bajo el cursor es descendiente
de su propio canvas. Si el `CTkToplevel` del dropdown tiene como padre a `self` (un widget
dentro del panel izquierdo), la cadena `.master` del dropdown pasa por el canvas del panel:

```
btn_dropdown → canvas_dropdown → CTkToplevel → CTkCustomDropdown → ... → canvas_panel → Tk
```

La guardia del panel izquierdo ve su canvas en la cadena → cree que le pertenece → scrollea.

## La solución

Crear el `CTkToplevel` como hijo del toplevel raíz, NO del widget que lo abre:

```python
# MAL — el CTkToplevel hereda la jerarquía del widget dentro del panel
self._dropdown_window = ctk.CTkToplevel(self)

# BIEN — el CTkToplevel queda fuera de la jerarquía del panel
self._dropdown_window = ctk.CTkToplevel(self.winfo_toplevel())
```

Con esto la cadena `.master` del dropdown nunca pasa por el canvas del panel:

```
btn_dropdown → canvas_dropdown → CTkToplevel → Tk root
```

La guardia del panel devuelve `False` → no scrollea. Cada frame scrollea solo cuando
el cursor está sobre sus propios widgets.

## Regla general

Siempre que crees un `CTkToplevel` flotante (dropdown, tooltip, popup) desde un widget
que vive dentro de un `CTkScrollableFrame`, usar `self.winfo_toplevel()` como padre
para no contaminar la jerarquía `.master`.

---

# CTkCustomDropdown - Problema altura dinámica del popup

## Objetivo
Que el dropdown tenga exactamente la altura del contenido (sin espacio fantasma al final).

## Intentos y descubrimientos

### 1. `item_height = 38` hardcodeado (código original)
- Calculaba `height = len(values) * 38` antes de crear los items
- Problemático con distintos tamaños de fuente. Reemplazado.

### 2. `scroll_frame.winfo_reqheight()` después de `update_idletasks()`
- **Valor correcto**: 3 items → 123px, 5 items → 205px. Varía bien.
- **Problema**: la ventana igual quedaba grande porque se expandía sola.

### 3. `scroll_frame._parent_frame.winfo_reqheight()`
- `_parent_frame` NO es el frame del contenido. Contiene: Canvas + CTkScrollbar + CTkLabel.
- Su `reqheight` era siempre 268 (fijo). Descartado.

### 4. `CTkToplevel` con `wm_minsize(1,1)`
- `CTkToplevel` impone internamente un tamaño mínimo de 200x200.
- `wm_minsize(1,1)` antes o después de `update_idletasks()` no lo pisa.
- `wm_geometry()` confirmó siempre `200x200`.

### 5. Cambio a `tk.Toplevel` (tkinter puro)
- Solucionó el minsize 200x200. El geometry SÍ se respeta: `835x123` ✓
- Pero la última opción seguía cortada visualmente.

### 6. Diagnóstico con prints
```
[DD] values=3 scroll_frame.reqh=123 win.reqh=268
  scroll_frame child: CTkButton reqh=35  ← botones directamente en scroll_frame
  scroll_frame child: CTkButton reqh=35
  scroll_frame child: CTkButton reqh=35
```
- `scroll_frame.winfo_reqheight()` = 123 ← correcto
- `win.winfo_reqheight()` = 268 ← expansivo, este es el problema
- Los botones están **directamente** en `scroll_frame.winfo_children()` (no dentro de canvas)

### 7. `resizable(False, False)` en `tk.Toplevel`
- Intento de evitar que `win.winfo_reqheight=268` expanda la ventana.
- **No funcionó** — última opción sigue cortada.

## Estado al pausar
- `tk.Toplevel` + `resizable(False, False)` + `scroll_frame.winfo_reqheight()`
- El geometry se aplica correctamente según `wm_geometry()`
- Pero visualmente la última opción aparece cortada
- Hipótesis: `CTkScrollableFrame` expande su canvas interno después del render final
  (fuera de `update_idletasks()`), empujando contenido que queda fuera del clip

## Próximos pasos sugeridos
- **Opción A** (recomendada): Usar `CTkFrame` simple en vez de `CTkScrollableFrame` cuando
  `content_height_px <= max_height_px`. Solo usar scroll cuando haya overflow real.
  Elimina el overhead del canvas y el problema de `win.reqheight=268`.
- **Opción B**: Canvas tkinter puro + frame interno manual, altura calculada exactamente.
- **Opción C**: Aplicar geometry definitivo con `after(1, lambda: ...)` para que ocurra
  después del render completo del canvas de CTkScrollableFrame.
- **Opción D**: Investigar si `CTkScrollableFrame` tiene parámetro de altura mínima.

---

# CTkFrame — Esquinas redondeadas "borrosas" (anti-aliasing de font_shapes)

## El problema

Las esquinas redondeadas de `CTkFrame` con `corner_radius > 0` se ven "difusas" o
"borrosas" en Windows. El efecto es sutil pero visible: un halo semi-transparente
alrededor de cada esquina redondeada. También se observa en flechas nativas de
tkinter dropdown (misma raíz).

## Por qué ocurre

### Pipeline de renderizado de CTk en Windows

En `core_rendering/__init__.py`:
```python
if sys.platform == "darwin":
    DrawEngine.preferred_drawing_method = "polygon_shapes"  # macOS
else:
    DrawEngine.preferred_drawing_method = "font_shapes"     # Windows/Linux
```

`font_shapes` usa una fuente especial (`CustomTkinter_shapes_font`) con caracteres
circulares pre-renderizados para dibujar las esquinas. Estos caracteres tienen
**anti-aliasing nativo del motor de fuentes**, lo que produce píxeles semi-transparentes
en los bordes de cada esquina.

### Estructura interna de CTkFrame

```
CTkFrame (hereda tkinter.Frame)
└── _canvas: CTkCanvas (place x=0, y=0, relwidth=1, relheight=1)
    ├── background_parts (rectángulos en esquinas, solo si background_corner_colors)
    ├── border_parts (polígono/font del borde redondeado)
    └── inner_parts (polígono/font del relleno interior)
```

El Canvas `bg` se configura con `_bg_color` (línea 129 de ctk_frame.py):
```python
self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
```

Los píxeles anti-aliased de `font_shapes` mezclan el color del borde/relleno
con el Canvas `bg`. Si el Canvas bg no coincide con el fondo visual real,
aparece el "halo".

### Detección automática de bg_color

`CTkBaseClass._detect_color_of_master()` camina la jerarquía `.master` buscando
un widget CTk con `fg_color` no-transparente. Dentro de `CTkScrollableFrame`,
esta detección puede fallar por la estructura interna compleja:

```
CTkScrollableFrame
├── _parent_frame: CTkFrame (el frame visual exterior)
│   ├── _parent_canvas: tkinter.Canvas (el canvas scrollable)
│   │   └── self (tkinter.Frame — donde van los hijos del usuario)
│   │       └── [widgets hijos aquí]
│   └── _scrollbar: CTkScrollbar
```

Cuando un widget hijo pide `_detect_color_of_master()`, el `self.master`
es el `tkinter.Frame` interno del scrollable, no el `_parent_frame` CTk.
La detección puede terminar con un color incorrecto del Canvas tkinter.

## La solución: `overwrite_preferred_drawing_method="polygon_shapes"`

CTkFrame acepta el parámetro `overwrite_preferred_drawing_method` que cambia
el método de dibujo **solo para ese frame**, sin afectar el resto de la app:

```python
titulo_frame = ctk.CTkFrame(
    parent,
    fg_color=Colors.BACKGROUND,
    bg_color=Colors.SURFACE,       # forzar color de anti-aliasing
    corner_radius=8,
    border_width=1,
    border_color=Colors.BORDER,
    overwrite_preferred_drawing_method="polygon_shapes",  # ← clave
)
```

`polygon_shapes` dibuja las esquinas con polígonos Canvas puros (sin font),
que son nítidos (aliased, sin blur). Es el método que macOS usa por defecto.

### Métodos de dibujo disponibles (DrawEngine)

| Método           | Cómo dibuja                        | Resultado          | Plataforma default |
|------------------|------------------------------------|--------------------|--------------------|
| `font_shapes`    | Caracteres de fuente anti-aliased  | Suave pero difuso  | Windows, Linux     |
| `polygon_shapes` | Polígonos Canvas puros             | Nítido, sin blur   | macOS              |
| `circle_shapes`  | Círculos + rectángulos Canvas      | Intermedio         | Fallback           |

## Problema adicional: tk.Frame rectangular dentro de CTkFrame redondeado

Si colocás un `tk.Frame` (tkinter puro, esquinas rectas) dentro de un `CTkFrame`
con `corner_radius > 0`, el frame rectangular se superpone sobre las esquinas
redondeadas, tapando la curva.

### Jerarquía visual del problema

```
caja_resultados (CTkFrame, corner_radius=8, border)
├── _canvas ← dibuja el rectángulo redondeado
└── VistaResultados (tk.Frame, rectangular)  ← sus esquinas rectas tapan las curvas
    └── tk.Text + ttk.Scrollbar
```

Con `padx=2, pady=2`, el tk.Frame quedaba a solo 2px del borde. Las esquinas
rectas del tk.Frame se extendían hasta la zona curva del CTkFrame, tapándola.

### La solución

Aumentar el padding del widget rectangular para que quede dentro del área plana:

```python
# MAL — padding insuficiente, esquinas rectas tapan la curva
self.vista_resultados.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

# BIEN — padding >= corner_radius * 0.3 mantiene el frame dentro del área plana
self.vista_resultados.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
```

Para `corner_radius=R`, el padding mínimo seguro es `R * (1 - cos(45°)) ≈ R * 0.29`.
En la práctica, usar `Spacing.SM` (8px) funciona bien para radios de 8-12px.

## Parámetros útiles de CTkFrame para control de esquinas

| Parámetro                            | Qué controla                                               |
|--------------------------------------|-------------------------------------------------------------|
| `fg_color`                           | Color de relleno interior del widget                        |
| `bg_color`                           | Color fuera de las esquinas redondeadas (anti-aliasing)     |
| `corner_radius`                      | Radio de la curva                                           |
| `background_corner_colors`           | Tupla (TL, TR, BR, BL) para pintar cada esquina distinta   |
| `overwrite_preferred_drawing_method` | Fuerza `polygon_shapes`, `font_shapes` o `circle_shapes`   |

## Regla general

Cuando veas esquinas "borrosas" o "difusas" en CTkFrame en Windows:
1. Usar `overwrite_preferred_drawing_method="polygon_shapes"` en el frame afectado
2. Forzar `bg_color` explícito que coincida con el fondo visual real
3. Si hay widgets tk puros (no-CTk) dentro del CTkFrame redondeado, usar padding
   suficiente para que no tapen las esquinas curvas
