# Troubleshooting CustomTkinter (CTk)

Problemas conocidos, causas y soluciones encontradas durante el desarrollo.

> Antes de debuggear un problema de UI, revisá esta guía para ver si ya fue investigado.

---

## Índice

- [Scaling / DPI — Doble escalado de widgets](#scaling--dpi--doble-escalado-de-widgets)
- [Scroll / MouseWheel — CTkScrollableFrame con CTkToplevel](#scroll--mousewheel--ctkscrollableframe-con-ctktoplevel)
- [Scroll / MouseWheel — tk.Text dentro de CTkScrollableFrame](#scroll--mousewheel--tktext-dentro-de-ctkscrollableframe)
- [CTkCustomDropdown — Altura dinámica del popup](#ctkcustomdropdown--altura-dinámica-del-popup)
- [Rendering — Esquinas redondeadas borrosas en Windows](#rendering--esquinas-redondeadas-borrosas-en-windows)
- [Rendering — tk.Frame rectangular tapando esquinas de CTkFrame](#rendering--tkframe-rectangular-tapando-esquinas-de-ctkframe)
- [CTkCustomDropdown — Texto del listado se clipea por la izquierda](#ctkcustomdropdown--texto-del-listado-se-clipea-por-la-izquierda)
- [Layout — Dos columnas de igual ancho y alto](#layout--dos-columnas-de-igual-ancho-y-alto)
- [CTkToplevel — Botón minimizar bloqueado por grab_set()](#ctktoplevel--botón-minimizar-bloqueado-por-grab_set)

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

## Scroll / MouseWheel — tk.Text dentro de CTkScrollableFrame

**Estado**: ✅ Resuelto

**Archivos afectados**: [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

Un `tk.Text` (editor de texto) está dentro de un `CTkScrollableFrame`. Al pasar el mouse sobre el editor:
- El scroll **no mueve el modal** (se lo come el `tk.Text`)
- Si se intenta redirigir el evento al canvas del scroll frame con un bind, el modal scrollea pero **más lento** que fuera del editor
- Al sacar el mouse del editor, el scroll vuelve a funcionar normal

### Causa

`tk.Text` captura `<MouseWheel>` por defecto — es su comportamiento nativo para scrollear su propio contenido. Si hay más texto del que entra en la altura fija, scrollea internamente. Si no hay overflow, el evento igual queda "consumido" por el widget y no llega al `CTkScrollableFrame`.

El intento de redirigir via binding (`yview_scroll`) genera el efecto "más lento" porque hay dos handlers disparando: el binding propio del `tk.Text` y el bind global del `CTkScrollableFrame` (que usa `bind_all`).

### Solución

Eliminar el conflicto de raíz: **no usar altura fija en el `tk.Text`**. En vez de `height=16` fijo con scroll interno, hacer que el editor crezca automáticamente con el contenido. Así todo el scroll lo maneja el modal.

```python
# tk.Text sin altura fija, crece con el contenido
email_text = tk.Text(
    editor_frame,
    wrap="word",
    height=10,   # altura mínima inicial
    undo=True,
    ...
)
email_text.pack(fill="x")   # sin expand=True

# Actualizar altura al tipear
def _actualizar_altura(_=None):
    lineas = int(email_text.index(tk.END).split(".")[0]) - 1
    email_text.configure(height=max(10, lineas))

email_text.bind("<KeyRelease>", _actualizar_altura)
_actualizar_altura()   # inicializar con el texto default ya cargado
```

### Por qué funciona

El `tk.Text` nunca tiene más contenido del que muestra → su scroll interno nunca se activa → el `<MouseWheel>` queda libre para que lo tome el `CTkScrollableFrame` via su `bind_all` global. No hace falta ningún binding extra.

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `email_text.bind("<MouseWheel>", redirect_al_canvas)` | El modal scrolleaba pero más lento — el `bind_all` del CTkScrollableFrame también disparaba |
| 2 | `redirect + return "break"` | El scroll del modal funcionaba pero el editor nunca scrolleaba su propio contenido (roto para textos largos) |

### Regla general

Si necesitás un `tk.Text` editable dentro de un `CTkScrollableFrame`, hacé que el widget crezca dinámicamente con el contenido en vez de tener altura fija. Eliminás el conflicto de scroll sin necesidad de bindings adicionales.

---

## CTkCustomDropdown — Altura dinámica del popup

**Estado**: ✅ Resuelto

**Archivo afectado**: [UI/components/ctk_custom_dropdown.py](../../Hoteles/UI/components/ctk_custom_dropdown.py)

### Síntoma

La última opción del dropdown siempre se cortaba a la mitad, sin importar cuántas opciones hubiera.

### Causa

`CTkScrollableFrame` tiene estructura interna con overhead invisible:

```
tk.Toplevel (ventana)
└── CTkScrollableFrame
    └── _parent_frame (CTkFrame, corner_radius=6)  ← agrega ~12px (6 top + 6 bottom)
        ├── _parent_canvas (Canvas)                ← agrega ~6px de padding interno
        │   └── tkinter.Frame (scroll_frame)       ← acá van los botones
        └── _scrollbar (CTkScrollbar)
```

Si se usaba `scroll_frame.winfo_reqheight()` como altura de la ventana (ej: 144px), el canvas viewport real terminaba siendo `144 - 18 = 126px`, cortando ~18px de contenido (media opción).

El overhead total medido: **18px** (con `corner_radius=6`, `border_width=0`).

### Solución

Medir el contenido y el overhead directamente desde los hijos, sin depender de la geometría de la ventana:

```python
self._dropdown_window.update_idletasks()
children = scroll_frame.winfo_children()

# 1. Contenido = suma de alturas reales de cada botón + pady
content_height_px = sum(c.winfo_reqheight() + 4 for c in children)

# 2. Overhead = estructura interna del CTkScrollableFrame
parent_canvas = scroll_frame._parent_canvas
parent_frame = scroll_frame._parent_frame
overhead = parent_frame.winfo_reqheight() - parent_canvas.winfo_reqheight()
if overhead <= 0:
    overhead = 18  # fallback

# 3. Altura final = contenido + overhead (con límite si hay max_visible)
height_px_final = min(content_height_px + overhead, max_height_px)
self._dropdown_window.geometry(f"{width_px}x{height_px_final}+{x}+{y}")
```

**Por qué funciona**: mide cada botón hijo individualmente con `winfo_reqheight()` y suma el overhead estructural (`_parent_frame - _parent_canvas`). No depende de la geometría de la ventana.

**Por qué es dinámico**: no hardcodea los 18px de overhead (salvo fallback). Si cambia el `corner_radius`, `border_width`, o CTk cambia su padding interno, se recalcula automáticamente.

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `item_height = 38` hardcodeado | Fallaba con distintas fuentes |
| 2 | `scroll_frame.winfo_reqheight()` directo | Valor correcto pero no cuenta el overhead → última opción cortada |
| 3 | `_parent_frame.winfo_reqheight()` | Siempre 268 (valor fijo inflado). Descartado |
| 4 | `CTkToplevel` + `wm_minsize(1,1)` | CTkToplevel impone minsize 200×200, no se puede pisar |
| 5 | `tk.Toplevel` (tkinter puro) | Resolvió minsize, pero el overhead seguía cortando |
| 6 | `resizable(False, False)` | No resolvió el overhead |
| 7 | `ventana.winfo_height() - canvas.winfo_height()` con geometría 500px | Funciona cuando el contenido llena la ventana, pero con pocos items el canvas no se expande y el overhead queda inflado (ej: 418px en vez de 18px) |

### Regla general

Cuando uses `CTkScrollableFrame` y necesites controlar su altura exacta, sumar las alturas de los hijos + el overhead. El overhead se obtiene con `_parent_frame.winfo_reqheight() - _parent_canvas.winfo_reqheight()`. No usar `ventana - canvas` porque falla con pocos items.

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

## CTkCustomDropdown — Texto del listado se clipea por la izquierda

**Estado**: ✅ Resuelto

**Archivo afectado**: [UI/components/ctk_custom_dropdown.py](../../Hoteles/UI/components/ctk_custom_dropdown.py)

### Síntoma

Las opciones del listado desplegable se recortan por la izquierda cuando el texto es más largo que el ancho del botón. En vez de ver `sgl/dbl/tpl diplomatic suite...`, se ve `l/dbl/tpl diplomatic suite...`.

### Causa

`CTkButton` con `anchor="w"` y texto que excede el ancho disponible hace clip desde la izquierda en vez de la derecha. Es un comportamiento interno de CTk/tkinter que no respeta el anchor al truncar.

El problema se introdujo al agregar `pack_propagate(False)` en el `entry` frame para corregir el bug del botón `▼` que se desplazaba fuera de pantalla con textos largos. Antes de ese fix el Toplevel del listado era más ancho (porque el entry inflaba su tamaño), y el clip no se notaba.

### Solución

Truncar explícitamente el texto con "…" por la derecha antes de crear cada botón del listado. El desafío fue medir el ancho disponible real dentro del Toplevel.

```python
# 1. Botón sonda con texto largo → fuerza _text_label a expandirse al máximo
probe_btn = ctk.CTkButton(scroll_frame, text="X" * 200, anchor="w")
probe_btn.pack(fill="x")
window.geometry(f"{width_px}x100+-9999+-9999")
window.update_idletasks()

# 2. Medir el ancho del _text_label (= espacio real para texto)
list_available_px = probe_btn._text_label.winfo_width()

# 3. Obtener la font real del CTkButton (CTk escala internamente)
real_font_str = probe_btn._text_label.cget("font")  # ej: "Roboto -20 {normal roman}"
# Parsear → tkfont.Font(family="Roboto", size=-20)

probe_btn.destroy()

# 4. Crear botones con texto ya truncado
for value in values:
    display = _truncate_text(value, available_px=list_available_px, font=real_font)
    btn = ctk.CTkButton(scroll_frame, text=display, anchor="w", ...)
```

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `width_px - 20` (padding hardcodeado) | `width_px` es el ancho de la ventana, no del botón. El `CTkScrollableFrame` consume ~33px de overhead de ancho. El texto "entraba" según `font.measure()` pero visualmente se clipeaba |
| 2 | Truncar post-render con `btn.configure(text=display)` | `cget("text")` mostraba el texto truncado, pero el canvas del CTkButton no se re-renderizaba visualmente — el texto seguía apareciendo completo |
| 3 | Medir `btn._text_label.winfo_width()` post-render | Con texto corto (hoteles), el label se ajustaba al contenido (125px) en vez de expandirse al espacio disponible (770px). Truncaba de más |
| 4 | Medir `btn._canvas.winfo_width()` | Devolvía el mismo valor que `btn.winfo_width()` (770px), padding=0. No servía para calcular espacio de texto |
| 5 | `font.measure()` con `Typography.FAMILY`/`Typography.BODY` (Inter 14) | CTkButton usa internamente otra font escalada (Roboto -20). Mediciones inconsistentes: `font.measure()` decía que entraba, visualmente no |

### Lecciones aprendidas

1. **CTkButton no re-renderiza texto** al hacer `configure(text=...)` después del layout — hay que crear el botón con el texto final desde el inicio
2. **`_text_label.winfo_width()` depende del contenido** — con texto corto da el ancho del texto, no el espacio disponible. Para medir el máximo, usar texto largo que fuerce la expansión
3. **La font de medición debe ser la real del widget**, no la que uno le pasó. CTk escala la font internamente (ej: `(Inter, 14)` → `Roboto -20`). Obtenerla de `_text_label.cget("font")`
4. **`width_px` (ventana) ≠ ancho del botón** — el `CTkScrollableFrame` consume overhead de ancho (scrollbar, corner_radius, padding interno)

---

## Layout — Dos columnas de igual ancho y alto

**Estado**: ✅ Resuelto

**Archivos afectados**: [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

Dos widgets hermanos con `pack(side="left", fill="both", expand=True)` no quedan de igual ancho ni de igual alto. El que tiene más contenido se ve más ancho, y el más bajo no se estira para igualar al más alto.

### Causa

`pack` con `side="left"` y `expand=True` divide el **espacio extra** equitativamente, pero el **espacio base** lo determina el contenido de cada widget. Si uno tiene más texto/hijos que el otro, arranca con más espacio base y el `expand` no lo iguala.

### Regla: no mezclar `pack` y `grid` en hijos del **mismo padre**

Mezclar `pack` y `grid` en hijos del mismo padre provoca un deadlock en Tk. La restricción es **por contenedor**, no global. Si `banners_row` usa `grid` para sus hijos, y `content` usa `pack` para los suyos (incluyendo `banners_row`), no hay conflicto.

### Solución definitiva — `grid` con `uniform` en el contenedor

```python
# _crear_banners:
banners_row = ctk.CTkFrame(parent, fg_color="transparent")
banners_row.pack(fill="x", pady=(0, 16))          # pack hacia content — OK
banners_row.grid_columnconfigure(0, weight=1, uniform="banners")
banners_row.grid_columnconfigure(1, weight=1, uniform="banners")

# _crear_banner_busqueda:
banner.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

# _crear_banner_resultados:
banner.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
```

**Por qué funciona**: `uniform="banners"` fuerza que ambas columnas tengan **exactamente el mismo ancho en todo momento**, incluso al resize de la ventana. Sin `uniform`, `weight=1` reparte el espacio extra equitativamente pero puede desfasarse si el contenido tiene preferencias distintas. Con `uniform`, las columnas están forzadas a ser iguales siempre.

El `sticky="nsew"` en cada banner hace que se estire tanto en ancho como en alto — el más bajo se iguala automáticamente al más alto.

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `expand=True` solo con `pack` | Divide espacio extra, no el total → desparejo cuando el contenido difiere |
| 2 | `width=1` en cada banner + `pack expand=True` | Anula preferencia de contenido pero pack sigue sin dividir exacto en 50-50 |
| 3 | `<Configure>` + `pack_configure(width=mitad)` + `pack_propagate(False)` | Complejo, loops de resize en CTk, no confiable |
| 4 | `place` con `relheight=1.0` desde `<Configure>` | Los banners desaparecen — `place` requiere que el padre tenga altura definida, que `pack fill="x"` no garantiza |
| 5 | `grid` con `weight=1` sin `uniform` | 50-50 al abrir, pero se desacomoda al redimensionar la ventana |

---

## CTkToplevel — Botón minimizar bloqueado (Windows)

**Estado**: ✅ Resuelto (workaround: ocultar el botón via Win32 API)

**Archivos afectados**: [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

En un `CTkToplevel` (modal), el botón minimizar (`_`) de la barra de título de Windows no responde. El botón de cerrar (`X`) y cualquier botón Python (`destroy()`) sí funcionan. Solo el minimizar está bloqueado.

### Causa

`CTkToplevel` en Windows combina dos mecanismos que bloquean WM_SYSCOMMAND (el mensaje nativo del minimizar):
- `grab_set()` captura todos los eventos de input hacia la ventana
- `transient(parent)` que CTkToplevel aplica internamente hace que Windows trate la ventana como dependiente del padre, bloqueando el minimize independiente

El botón `X` y los botones Python funcionan porque llaman `destroy()` directamente, sin pasar por WM_SYSCOMMAND.

### Intentos fallidos

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `self.after(100, self.grab_set)` — diferir grab_set | No resolvió — la causa no era el timing del grab |
| 2 | `self.transient("")` — desvincular del padre | No resolvió — CTkToplevel restablece el transient internamente |

### Solución — ocultar el botón via Win32 API

Como el botón no se puede habilitar desde tkinter/CTk, la solución es ocultarlo con la API de Windows:

```python
def _ocultar_boton_minimizar(self):
    import ctypes
    hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
    GWL_STYLE = -16
    WS_MINIMIZEBOX = 0x00020000
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MINIMIZEBOX)
    SWP_FLAGS = 0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
    ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
```

Llamarlo diferido para que la ventana ya tenga hwnd válido:

```python
self.after(150, self._ocultar_boton_minimizar)
```

### Regla general

En modales `CTkToplevel` en Windows donde el botón minimizar queda bloqueado: ocultarlo con `WS_MINIMIZEBOX` via ctypes. Es más honesto que dejarlo visible pero roto.

---

Ver también:
- [componentes.md](componentes.md) — Componentes CTk y CTkCustomDropdown
- [../desarrollo/debugging.md](../desarrollo/debugging.md) — Debugging general
