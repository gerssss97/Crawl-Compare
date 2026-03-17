# Troubleshooting CustomTkinter (CTk)

Problemas conocidos, causas y soluciones encontradas durante el desarrollo.

> Antes de debuggear un problema de UI, revisá esta guía para ver si ya fue investigado.

---

## Índice

- [Scaling / DPI — Doble escalado de widgets](#scaling--dpi--doble-escalado-de-widgets)
- [Scroll / MouseWheel — CTkScrollableFrame con CTkToplevel](#scroll--mousewheel--ctkscrollableframe-con-ctktoplevel)
- [CTkCustomDropdown — Altura dinámica del popup](#ctkcustomdropdown--altura-dinámica-del-popup)
- [Rendering — Esquinas redondeadas borrosas en Windows](#rendering--esquinas-redondeadas-borrosas-en-windows)
- [Rendering — tk.Frame rectangular tapando esquinas de CTkFrame](#rendering--tkframe-rectangular-tapando-esquinas-de-ctkframe)

---

## Scaling / DPI — Doble escalado de widgets

**Estado**: ✅ Resuelto

### Síntoma

Un widget aparece más grande de lo esperado, o desborda su contenedor. Típicamente al pasarle a un widget CTk un valor de ancho/alto obtenido con `winfo_width()` / `winfo_height()`.

### Causa

CTk tiene su propio sistema de escala **encima** del DPI scaling de Windows. Cuando creás un widget con `width=100`, CTk internamente hace `tkinter_width = int(100 * ctk_widget_scaling)`. Si tomás el valor ya escalado de `winfo_width()` y se lo pasás a otro widget CTk, se escala de nuevo:

```
winfo_width() = 860  (píxeles reales, post-scaling)
CTkFrame(width=860)  → CTk escala otra vez: 860 * 1.5 = 1290px  ← OVERFLOW
```

### Solución

Dividir por el factor de escala antes de pasarlo a cualquier widget CTk:

```python
scaling = self._get_widget_scaling()   # método interno disponible en todo CTk widget
width_ctk = int(self.winfo_width() / scaling)
# Ahora: CTkFrame(width=width_ctk) → width_ctk * scaling = winfo_width() ✓
```

### Cuándo aplica / no aplica

| Valor | Necesita corrección |
|-------|---------------------|
| `winfo_width()` / `winfo_height()` pasado a CTkFrame, CTkToplevel geometry | ✅ Sí — dividir por `_get_widget_scaling()` |
| `winfo_rootx()` / `winfo_rooty()` pasado a `geometry(f"...+{x}+{y}")` | ❌ No — coordenadas absolutas de pantalla, son consistentes |

### Ejemplo real: CTkCustomDropdown

```python
# En _open_dropdown():
self.update_idletasks()
x = self.winfo_rootx()                            # coordenada pantalla → OK directo
y = self.winfo_rooty() + self.winfo_height() + 2  # coordenada pantalla → OK directo
scaling = self._get_widget_scaling()
width_ctk = int(self.winfo_width() / scaling)     # píxeles reales → dividir!

self._dropdown_window = ctk.CTkToplevel(self)
self._dropdown_window.wm_overrideredirect(True)
self._dropdown_window.geometry(f"{width_ctk}x300+{x}+{y}")
```

### Nota sobre la API

```python
self._get_widget_scaling()    # ✅ método privado pero estable, disponible en todo CTk widget
ctk.get_widget_scaling()      # ❌ NO existe como función global
ctk.set_widget_scaling(1.5)   # ✅ sí existe, pero es para forzar un valor global
```

---

## Scroll / MouseWheel — CTkScrollableFrame con CTkToplevel

**Estado**: ✅ Resuelto

### Síntoma

Scrollear sobre un dropdown (u otro popup flotante) también scrollea el panel de fondo que está debajo.

### Causa

`CTkScrollableFrame` usa `bind_all("<MouseWheel>", ...)` — un binding **global** que dispara para cualquier evento de scroll en toda la aplicación. Para discriminar si el scroll le pertenece, usa una guardia que sube recursivamente por `.master`:

```python
def check_if_master_is_canvas(self, widget):
    if widget == self._parent_canvas:
        return True
    elif widget.master is not None:
        return self.check_if_master_is_canvas(widget.master)  # sube por .master
    else:
        return False
```

Si el `CTkToplevel` del popup se crea con `self` como padre (un widget dentro del panel izquierdo), la cadena `.master` del popup pasa por el canvas del panel:

```
btn_dropdown → canvas_dropdown → CTkToplevel → CTkCustomDropdown → ... → canvas_panel → Tk
```

La guardia del panel izquierdo ve su canvas en la cadena → cree que le pertenece → scrollea.

### Solución

Crear el `CTkToplevel` como hijo del **toplevel raíz**, no del widget que lo abre:

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

### Regla general

Siempre que crees un `CTkToplevel` flotante (dropdown, tooltip, popup) desde un widget que vive dentro de un `CTkScrollableFrame`, usar `self.winfo_toplevel()` como padre para no contaminar la jerarquía `.master`.

---

## CTkCustomDropdown — Altura dinámica del popup

**Estado**: 🔬 En investigación

**Archivo afectado**: [UI/components/ctk_custom_dropdown.py](../../Hoteles/UI/components/ctk_custom_dropdown.py)

### Objetivo

Que el dropdown tenga exactamente la altura del contenido, sin espacio fantasma al final.

### Intentos realizados y descubrimientos

#### 1. `item_height = 38` hardcodeado (código original)
- Calculaba `height = len(values) * 38` antes de crear los items.
- Problemático con distintos tamaños de fuente. Reemplazado.

#### 2. `scroll_frame.winfo_reqheight()` después de `update_idletasks()`
- **Valor correcto**: 3 items → 123px, 5 items → 205px. Varía bien con el contenido.
- **Problema**: la ventana igual quedaba grande porque se expandía sola.

#### 3. `scroll_frame._parent_frame.winfo_reqheight()`
- `_parent_frame` NO es el frame del contenido. Contiene: Canvas + CTkScrollbar + CTkLabel.
- Su `reqheight` era siempre 268 (fijo). Descartado.

#### 4. `CTkToplevel` con `wm_minsize(1,1)`
- `CTkToplevel` impone internamente un tamaño mínimo de 200×200.
- `wm_minsize(1,1)` antes o después de `update_idletasks()` no lo pisa.
- `wm_geometry()` confirmó siempre `200x200`.

#### 5. Cambio a `tk.Toplevel` (tkinter puro)
- Solucionó el minsize 200×200. El geometry SÍ se respeta: `835x123` ✓
- Pero la última opción seguía cortada visualmente.

#### 6. Diagnóstico con prints
```
[DD] values=3 scroll_frame.reqh=123 win.reqh=268
  scroll_frame child: CTkButton reqh=35  ← botones directamente en scroll_frame
  scroll_frame child: CTkButton reqh=35
  scroll_frame child: CTkButton reqh=35
```
- `scroll_frame.winfo_reqheight()` = 123 ← correcto
- `win.winfo_reqheight()` = 268 ← expansivo, este es el problema
- Los botones están **directamente** en `scroll_frame.winfo_children()` (no dentro del canvas)

#### 7. `resizable(False, False)` en `tk.Toplevel`
- Intento de evitar que `win.winfo_reqheight=268` expanda la ventana.
- No funcionó — última opción sigue cortada.

### Hipótesis actual

`CTkScrollableFrame` expande su canvas interno **después** del render final (fuera del ciclo de `update_idletasks()`), empujando contenido que queda fuera del clip visible.

### Estado actual del código

`tk.Toplevel` + `resizable(False, False)` + `scroll_frame.winfo_reqheight()`.
El geometry se aplica correctamente según `wm_geometry()`, pero visualmente la última opción aparece cortada.

### Próximos pasos sugeridos

| Opción | Descripción | Recomendación |
|--------|-------------|---------------|
| **A** | Usar `CTkFrame` simple en vez de `CTkScrollableFrame` cuando `content_height_px <= max_height_px`. Solo usar scroll cuando haya overflow real. Elimina el overhead del canvas y el problema de `win.reqheight=268`. | ⭐ Recomendada |
| **B** | Canvas tkinter puro + frame interno manual, altura calculada exactamente. | Alternativa robusta |
| **C** | Aplicar geometry definitivo con `after(1, lambda: ...)` para que ocurra después del render completo del canvas. | Parche rápido |
| **D** | Investigar si `CTkScrollableFrame` tiene parámetro de altura mínima configurable. | Por investigar |

---

## Rendering — Esquinas redondeadas borrosas en Windows

**Estado**: ✅ Resuelto

### Síntoma

Las esquinas redondeadas de `CTkFrame` se ven "difusas" o con un halo semi-transparente en Windows. También se observa en flechas nativas de tkinter dropdown.

### Causa

En Windows, CTk usa `font_shapes` como método de dibujo por defecto:

```python
# core_rendering/__init__.py
if sys.platform == "darwin":
    DrawEngine.preferred_drawing_method = "polygon_shapes"  # macOS — nítido
else:
    DrawEngine.preferred_drawing_method = "font_shapes"     # Windows/Linux — con anti-aliasing
```

`font_shapes` usa una fuente especial (`CustomTkinter_shapes_font`) con caracteres circulares pre-renderizados. Estos caracteres tienen **anti-aliasing nativo del motor de fuentes**, produciendo píxeles semi-transparentes en los bordes.

El problema se agrava dentro de `CTkScrollableFrame`: la detección automática de `bg_color` (`_detect_color_of_master()`) puede fallar por la estructura interna compleja:

```
CTkScrollableFrame
├── _parent_frame: CTkFrame (el frame visual exterior)
│   ├── _parent_canvas: tkinter.Canvas (el canvas scrollable)
│   │   └── self (tkinter.Frame — donde van los hijos del usuario)
│   │       └── [widgets hijos aquí]
│   └── _scrollbar: CTkScrollbar
```

Cuando un widget hijo pide `_detect_color_of_master()`, su `.master` es el `tkinter.Frame` interno del scrollable (no el `_parent_frame` CTk), y la detección puede terminar con un color incorrecto.

### Solución

Usar `overwrite_preferred_drawing_method="polygon_shapes"` en el frame afectado. Cambia el método **solo para ese frame**, sin afectar el resto de la app:

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

`polygon_shapes` dibuja con polígonos Canvas puros (sin font), que son nítidos (aliased, sin blur). Es el método que macOS usa por defecto.

### Métodos de dibujo disponibles

| Método | Cómo dibuja | Resultado | Plataforma default |
|--------|-------------|-----------|-------------------|
| `font_shapes` | Caracteres de fuente anti-aliased | Suave pero difuso | Windows, Linux |
| `polygon_shapes` | Polígonos Canvas puros | Nítido, sin blur | macOS |
| `circle_shapes` | Círculos + rectángulos Canvas | Intermedio | Fallback |

### Parámetros útiles de CTkFrame para control de esquinas

| Parámetro | Qué controla |
|-----------|-------------|
| `fg_color` | Color de relleno interior del widget |
| `bg_color` | Color fuera de las esquinas redondeadas (anti-aliasing) |
| `corner_radius` | Radio de la curva |
| `background_corner_colors` | Tupla (TL, TR, BR, BL) para pintar cada esquina distinta |
| `overwrite_preferred_drawing_method` | Fuerza `polygon_shapes`, `font_shapes` o `circle_shapes` |

### Regla general

Cuando veas esquinas "borrosas" en CTkFrame en Windows:
1. Usar `overwrite_preferred_drawing_method="polygon_shapes"` en el frame afectado
2. Forzar `bg_color` explícito que coincida con el fondo visual real
3. Si hay widgets tk puros dentro del CTkFrame redondeado, ver la sección siguiente

---

## Rendering — tk.Frame rectangular tapando esquinas de CTkFrame

**Estado**: ✅ Resuelto

### Síntoma

Un `CTkFrame` con `corner_radius > 0` y borde redondeado, pero al mirarle las esquinas se ven rectas (el redondeo desaparece visualmente).

### Causa

Si colocás un `tk.Frame` (tkinter puro, esquinas rectas) dentro de un `CTkFrame` con `corner_radius > 0`, el frame rectangular se superpone sobre las esquinas redondeadas, tapando la curva.

```
caja_resultados (CTkFrame, corner_radius=8, border)
├── _canvas ← dibuja el rectángulo redondeado
└── VistaResultados (tk.Frame, rectangular)  ← sus esquinas rectas tapan las curvas
    └── tk.Text + ttk.Scrollbar
```

Con `padx=2, pady=2`, el `tk.Frame` quedaba a solo 2px del borde, extendiéndose hasta la zona curva.

### Solución

Aumentar el padding para que el widget rectangular quede dentro del área plana:

```python
# MAL — padding insuficiente, esquinas rectas tapan la curva
self.vista_resultados.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

# BIEN — padding suficiente mantiene el frame dentro del área plana
self.vista_resultados.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
```

Para `corner_radius=R`, el padding mínimo seguro es `R * (1 - cos(45°)) ≈ R * 0.29`. En la práctica, usar `Spacing.SM` (8px) funciona bien para radios de 8–12px.

---

Ver también:
- [componentes.md](componentes.md) — Componentes CTk y CTkCustomDropdown
- [../desarrollo/debugging.md](../desarrollo/debugging.md) — Debugging general
