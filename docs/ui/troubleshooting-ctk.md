# Troubleshooting CustomTkinter (CTk)

Problemas conocidos, causas y soluciones encontradas durante el desarrollo.

> Antes de debuggear un problema de UI, revisá esta guía para ver si ya fue investigado.

> **Referencia oficial**: Si el problema no está documentado acá, consultar la documentación de CustomTkinter en https://customtkinter.tomschimansky.com para confirmar features, parámetros soportados y limitaciones de widgets antes de proponer soluciones.

---

## Índice

- [Scaling / DPI — Doble escalado de widgets](#scaling--dpi--doble-escalado-de-widgets)
- [Scroll / MouseWheel — CTkScrollableFrame con CTkToplevel](#scroll--mousewheel--ctkscrollableframe-con-ctktoplevel)
- [Scroll / MouseWheel — tk.Text dentro de CTkScrollableFrame](#scroll--mousewheel--tktext-dentro-de-ctkscrollableframe)
- [CTkCustomDropdown — Altura dinámica del popup](#ctkcustomdropdown--altura-dinámica-del-popup)
- [Rendering — Esquinas redondeadas borrosas en Windows](#rendering--esquinas-redondeadas-borrosas-en-windows)
- [Rendering — tk.Frame rectangular tapando esquinas de CTkFrame](#rendering--tkframe-rectangular-tapando-esquinas-de-ctkframe)
- [CTkCustomDropdown — Texto del listado se clipea por la izquierda](#ctkcustomdropdown--texto-del-listado-se-clipea-por-la-izquierda)
- [CTkCustomDropdown — Seleccionar una opción reabre el dropdown inmediatamente](#ctkcustomdropdown--seleccionar-una-opción-reabre-el-dropdown-inmediatamente)
- [Layout — Dos columnas de igual ancho y alto](#layout--dos-columnas-de-igual-ancho-y-alto)
- [CTkToplevel — Botón minimizar bloqueado por grab_set()](#ctktoplevel--botón-minimizar-bloqueado-por-grab_set)
- [Rendering — tk.Text rectangular dentro de CTkFrame redondeado (Modal Email)](#rendering--tktext-rectangular-dentro-de-ctkframe-redondeado-modal-email)
- [Scroll / MouseWheel — Scroll lento al pasar el mouse sobre la scrollbar](#scroll--mousewheel--scroll-lento-al-pasar-el-mouse-sobre-la-scrollbar)
- [Scroll / Scrollbar — CTkScrollableFrame muestra scrollbar aunque el contenido cabe](#scroll--scrollbar--ctkscrollableframe-muestra-scrollbar-aunque-el-contenido-cabe)
- [Layout — CTkScrollableFrame cambia el ancho del contenido al aparecer/desaparecer la scrollbar](#layout--ctkscrollableframe-cambia-el-ancho-del-contenido-al-aparerecerdesaparecer-la-scrollbar)
- [Layout — grid_remove() en constructor no tiene efecto](#layout--grid_remove-en-constructor-no-tiene-efecto)
- [CTkLabel — wraplength dinámico no funciona si width=1 está seteado](#ctklabel--wraplength-dinámico-no-funciona-si-width1-está-seteado)
- [Scroll / MouseWheel — Dos CTkScrollableFrame anidados se scrollean simultáneamente](#scroll--mousewheel--dos-ctkscrollableframe-anidados-se-scrollean-simultáneamente)
- [Layout — Threshold numérico para decidir si usar CTkScrollableFrame](#layout--threshold-numérico-para-decidir-si-usar-ctkscrollableframe)

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

## Rendering — Widget rectangular dentro de CTkFrame redondeado (Modal Email)

**Estado**: 🔬 Pendiente — esquinas del hijo rectangular siguen visibles dentro del frame redondeado

**Archivos afectados**: [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

El editor de email (toolbar + área de texto) tiene esquinas rectas que sobresalen del frame contenedor redondeado. Cualquier widget hijo rectangular se renderiza por encima de las esquinas curvas del padre CTkFrame.

### Causa raíz

**Tkinter/CustomTkinter no soporta `overflow: hidden` ni z-index.** Confirmado en la [documentación oficial de CTk](https://customtkinter.tomschimansky.com). Los CTkFrame dibujan sus esquinas redondeadas en un canvas, pero los widgets hijos se renderizan encima sin clipping. No hay forma nativa de que el padre recorte a sus hijos.

### Intentos (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | Cambiar `fg_color` del `editor_frame` contenedor | No visible — el widget de texto tapa completamente al frame |
| 2 | Shadow frame wrapeando al editor (`corner_radius` en shadow, `corner_radius=0` en editor) | Esquinas rectas del editor se asoman por las esquinas redondeadas del shadow |
| 3 | `corner_radius=0` en editor_frame + padding `(2,4)` en shadow | Padding insuficiente para radio 10 (mínimo seguro: `R × 0.29 ≈ 3px`) |
| 4 | Aumentar padding del shadow a `5px` con `corner_radius=12` | Esquinas ya no se asoman pero el "borde" de 5px queda visualmente grueso, no parece sombra |
| 5 | Reemplazar `tk.Text` por `ctk.CTkTextbox` | Resuelve el error de `tag_config` con font, pero la toolbar (`CTkFrame corner_radius=0`) sigue siendo rectangular y se asoma por las esquinas del padre |

### Estado actual

Se migró de `tk.Text` a `ctk.CTkTextbox` (mejora de compatibilidad con CTk). El editor_frame usa borde simple sin shadow frame. Las esquinas del frame son redondeadas pero los hijos internos (toolbar, textbox) se asoman en las esquinas.

### Migración tk.Text → CTkTextbox (referencia)

La migración se hizo y se mantiene independientemente de las esquinas, porque CTkTextbox es más consistente con el resto de la UI.

| Aspecto | `tk.Text` | `ctk.CTkTextbox` |
|---------|-----------|-------------------|
| Esquinas | Siempre rectas | Soporta `corner_radius` |
| `height` | En **líneas** | En **píxeles** |
| Color fondo | `bg=` | `fg_color=` |
| Color texto | `fg=` | `text_color=` |
| Borde | `relief=`, `bd=` | `border_width=`, `border_color=` |
| Métodos directos | Todos los de tk.Text | `insert`, `get`, `delete`, `tag_add`, `tag_remove`, `tag_config`, `bind` |
| Métodos via `._textbox` | N/A | `index`, `tag_ranges`, `compare`, `edit_undo`, `edit_redo` |
| `font` en `tag_config` | ✅ Funciona | ❌ Prohibido — usar `._textbox.tag_configure()` |

### Posibles caminos a explorar

- Canvas con clipping region manual (dibujar contenido en un canvas con clip path)
- `overrideredirect` + render custom completo
- Aceptar esquinas rectas y usar borde simple (estado actual)

---

---

## Scroll / MouseWheel — Scroll lento al pasar el mouse sobre la scrollbar

**Estado**: ✅ Resuelto

**Archivos afectados**: [UI/interfaz_ctk.py](../../Hoteles/UI/interfaz_ctk.py), [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

Al posicionar el mouse sobre la scrollbar de un `CTkScrollableFrame` y scrollear, el scroll es ~7x más lento que al scrollear con el mouse sobre el contenido. Al sacar el mouse de la scrollbar, vuelve a la velocidad normal.

### Causa

`CTkScrollableFrame` tiene dos handlers de `<MouseWheel>` con fórmulas de sensibilidad distintas:

| Handler | Quién lo registra | Fórmula (Windows) | Delta=120 → unidades |
|---------|-------------------|-------------------|---------------------|
| `bind_all("<MouseWheel>")` | `CTkScrollableFrame` | `event.delta / 6` | **20 unidades** |
| `_mouse_scroll_event` | `CTkScrollbar._canvas` | `event.delta / 40` | **3 unidades** |

El `bind_all` del scrollable frame tiene una guardia `check_if_master_is_canvas()` que sube recursivamente por la jerarquía de `.master`. La scrollbar es **hermana** del canvas (ambas son hijas de `_parent_frame`), no hija. Entonces cuando el evento cae sobre la scrollbar, la guardia nunca encuentra el canvas y retorna `False` → el `bind_all` **no dispara**.

Solo queda activo el handler propio de la scrollbar, que usa `delta/40` → scroll 7x más lento.

```
_parent_frame
├── _parent_canvas  (row=1, col=0)  ← check_if_master_is_canvas busca esto
└── _scrollbar      (row=1, col=1)  ← sibling, no pasa por _parent_canvas al subir
    └── _canvas (CTkCanvas)         ← aquí cae el evento MouseWheel
```

### Intento fallido

Bindear sobre el `CTkScrollbar` directamente no funciona — el evento `<MouseWheel>` cae sobre el `_canvas` **interno** del CTkScrollbar (CTkCanvas), no sobre el widget wrapper:

```python
# ❌ No intercepta el evento — cae en _canvas interno, no en el CTkScrollbar
self._panel_izq._scrollbar.bind("<MouseWheel>", lambda e: "break")
```

### Solución

Bindear sobre el `_canvas` interno del `CTkScrollbar`, redirigir al `_parent_canvas` con la misma fórmula que usa el `CTkScrollableFrame` (`delta/6`), y cancelar el handler lento con `return "break"`:

```python
_sb_canvas = self._panel_izq._scrollbar._canvas
_parent_canvas = self._panel_izq._parent_canvas

def _fix_scrollbar_wheel(event):
    _parent_canvas.yview_scroll(int(-event.delta / 6), "units")
    return "break"  # cancela el handler lento de la scrollbar (delta/40)

_sb_canvas.bind("<MouseWheel>", _fix_scrollbar_wheel)
```

Aplicar inmediatamente después de crear el `CTkScrollableFrame`, antes de agregar contenido.

### Regla general

Si un `CTkScrollableFrame` tiene scroll lento sobre la scrollbar, el problema es la diferencia de sensibilidad entre los dos handlers. La fix siempre es: bindear sobre `_scrollbar._canvas` (no sobre `_scrollbar`), y redirigir al `_parent_canvas` con `delta/6`.

---

## CTkLabel — wraplength dinámico no funciona si width=1 está seteado

**Estado**: 🔬 En investigación

**Archivos afectados**: [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py)

### Síntoma

Los labels de texto largo en los banners del modal de email (hotel | habitacion, periodos, habitacion web) aparecen **recortados por la derecha**, sin wrappear, tanto al abrir el modal como al redimensionar la ventana.

### Causa confirmada (parcial)

El patrón usado es `wraplength=1` + `width=1` como valores dummy, con actualización dinámica vía `<Configure>` en el frame padre:

```python
lbl = ctk.CTkLabel(inner, ..., wraplength=1, width=1)
inner.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(1, e.width)), add="+")
```

Se confirmó mediante debug que:
1. El evento `<Configure>` **sí llega** a `inner` con valores correctos (ej. `w=534`)
2. El `wraplength` **sí se setea** al valor correcto en el label

Sin embargo el texto sigue recortado. Se sospecha que `width=1` restringe el ancho físico del widget independientemente del `wraplength`.

### Intentos

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | Eliminar `width=1` de todos los CTkLabel con wraplength dinámico | Texto sigue recortado — en investigación |

### Pendiente

Determinar por qué `wraplength` correcto + `fill="x"` en pack no es suficiente para que el texto wrappee. Posibles causas a investigar:
- CTkLabel ignora `wraplength` si el widget subyacente (`tk.Label`) tiene un ancho fijo seteado internamente por CTk
- El `fill="x"` no se propaga correctamente dentro de la jerarquía `banner (grid) → inner (pack side=left)`

---

---

## Scroll / Scrollbar — CTkScrollableFrame muestra scrollbar aunque el contenido cabe

**Estado**: ✅ Resuelto

**Archivos afectados**: [UI/interfaz_ctk.py](../../Hoteles/UI/interfaz_ctk.py) — `_panel_izq` (panel selección de reserva) y panel derecho de resultados

### Síntoma

Un `CTkScrollableFrame` muestra su scrollbar vertical aunque el contenido entra perfectamente en el viewport. Además:
- Al scrollear con la rueda sobre el contenido no pasa nada (parece que no funciona)
- Al posicionar el mouse sobre la scrollbar y scrollear, sí se mueve — pero hay más espacio virtual "arriba" que "abajo"

### Causa

`CTkScrollableFrame` **siempre renderiza su scrollbar**, no tiene lógica de auto-ocultamiento. La scrollbar aparece incluso cuando `scrollregion == viewport`.

El phantom overflow de 1-2px se explica así: `CTkScrollableFrame` dimensiona su ventana interna (`canvas_window`) al menos tan grande como el viewport del canvas. Con hijos que usan `expand=True`, el frame interno solicita exactamente esa altura. Por diferencias de DPI scaling entre píxeles reales y unidades CTk, el `scrollregion` puede quedar 1-2px por encima del viewport → la scrollbar aparece pero prácticamente no hay nada que scrollear.

El efecto "más espacio arriba que abajo": el contenido está al inicio pero hay 1-2px de espacio virtual al fondo. El thumb de la scrollbar parece "lleno" (ocupa casi todo el track) pero la posición yview no está exactamente en 0.

El "wheel no funciona sobre el contenido": `bind_all` sí dispara pero `yview_scroll(20, "units")` sobre 1-2px de overflow se clampea a 0 → nada se mueve → el usuario percibe que el scroll está roto.

### Por qué no basta con reemplazar `CTkScrollableFrame` por `CTkFrame`

La solución obvia (reemplazar por `CTkFrame`) elimina el phantom scrollbar **pero también elimina el scroll cuando el contenido genuinamente desborda** (ej: CTkPrecioPanel con muchos periodos de precio). La solución debe preservar ambos comportamientos.

### Solución — hook en `yscrollcommand` con auto-hide vía `grid_remove`/`grid`

Tk llama a `yscrollcommand` en cada actualización de posición, pasando dos fracciones `lo` y `hi` que representan qué porción del contenido total es actualmente visible:

```
contenido = 1000px, viewport = 600px, posición al tope:
  lo = 0/1000  = 0.0   (tope del área visible / contenido total)
  hi = 600/1000 = 0.6   (fondo del área visible / contenido total)

cuando todo cabe (sin overflow):
  lo = 0.0, hi = 1.0   ← la scrollbar no hace falta
```

Hookeamos `yscrollcommand` para decidir si la scrollbar debe mostrarse:

```python
_sb_der = container._scrollbar
_canvas_der = container._parent_canvas

def _auto_hide_der(lo, hi):
    _sb_der.set(lo, hi)                                          # actualizar posición normal
    should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)
    _canvas_der.after(0, _sb_der.grid if should_show else _sb_der.grid_remove)

_canvas_der.configure(yscrollcommand=_auto_hide_der)
```

**Tabla de decisión:**

| Situación | lo | hi | `should_show` |
|---|---|---|---|
| Todo visible, sin overflow | 0.0 | 1.0 | False — oculta ✓ |
| Phantom overflow DPI (1-2px) | 0.0 | 0.998 | False — oculta ✓ |
| Overflow real, vista al tope | 0.0 | 0.7 | True — muestra ✓ |
| Overflow real, vista al fondo | 0.3 | 1.0 | True — muestra ✓ |

**Por qué `grid_remove` / `grid` y no `pack_forget`:** `CTkScrollableFrame` organiza sus internos con `grid` (`_parent_canvas` en col=0, `_scrollbar` en col=1). `grid_remove()` elimina la scrollbar del grid pero **recuerda sus opciones** → `grid()` sin argumentos la restaura exactamente donde estaba. `pack_forget()` no aplica porque el layout interno es grid.

**Por qué `after(0, ...)`:** `_auto_hide_der` se llama desde el sistema interno de scroll de Tk. Modificar el layout (grid_remove/grid) dentro de ese callback puede causar re-entradas. Diferir con `after(0)` lo ejecuta en el siguiente ciclo del event loop, evitando el conflicto.

**Margen de 0.005 / 0.995:** absorbe el DPI rounding de 1-2px. Para un viewport de 600px, un overflow de hasta 3px se trata como "sin overflow". Overflow genuino de más de ~3px siempre supera el umbral y muestra la scrollbar.

### Aplicar junto con el fix de velocidad de scrollbar

Conviene aplicar ambos fixes juntos (auto-hide + velocidad uniforme):

```python
container = ctk.CTkScrollableFrame(panel_der, fg_color="transparent")
container.pack(fill="both", expand=True, padx=Spacing.LG, pady=Spacing.LG)

# Fix 1: auto-ocultar scrollbar cuando el contenido cabe en el viewport
_sb_der = container._scrollbar
_canvas_der = container._parent_canvas

def _auto_hide_der(lo, hi):
    _sb_der.set(lo, hi)
    should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)
    _canvas_der.after(0, _sb_der.grid if should_show else _sb_der.grid_remove)

_canvas_der.configure(yscrollcommand=_auto_hide_der)

# Fix 2: velocidad uniforme al scrollear sobre la scrollbar (ver sección anterior)
def _fix_scrollbar_wheel_der(event):
    _canvas_der.yview_scroll(int(-event.delta / 6), "units")
    return "break"

container._scrollbar._canvas.bind("<MouseWheel>", _fix_scrollbar_wheel_der)
```

### Regla general

`CTkScrollableFrame` nunca auto-oculta su scrollbar. Si necesitás que la scrollbar aparezca solo cuando el contenido genuinamente desborda, siempre aplicá el hook en `yscrollcommand` con el patrón `grid_remove`/`grid` y umbral 0.005/0.995.

---

## Layout — CTkScrollableFrame cambia el ancho del contenido al aparecer/desaparecer la scrollbar

**Estado**: ✅ Resuelto — Opción B (place overlay, ver más abajo)

**Archivo afectado**: `Hoteles/UI/interfaz_ctk.py` — `_crear_panel_izquierdo()`

### Síntoma

El panel izquierdo (formulario de inputs) cambia su ancho visualmente cuando aparece o desaparece la scrollbar vertical. Ocurre en dos situaciones:
- Al seleccionar un hotel con edificio: los nuevos inputs hacen que el contenido crezca → scrollbar aparece → panel se redimensiona
- Al hacer resize vertical de la ventana: el contenido entra o no → scrollbar aparece/desaparece → panel salta

### Estructura interna de CTkScrollableFrame

```
_parent_frame (CTkFrame) — este es el widget real en el layout externo
  ├── col=0, weight=1 → _parent_canvas   (row=1)
  └── col=1, sin minsize → _scrollbar    (row=1)
```

`CTkScrollableFrame` hereda de `tkinter.Frame` pero ese frame vive **dentro del `_parent_canvas`**, no en el layout externo. El widget que realmente ocupa espacio en el grid del padre es `_parent_frame`.

### Causa raíz identificada

El `_content_frame` tiene `uniform="cols"` en sus columnas:

```python
self._content_frame.grid_columnconfigure(0, weight=55, minsize=480, uniform="cols")
self._content_frame.grid_columnconfigure(1, weight=45, minsize=360, uniform="cols")
```

`uniform` hace que ambas columnas se recalculen juntas cada vez que el contenido natural de cualquiera de ellas cambia. Cuando la scrollbar desaparece vía `grid_remove()`, el contenido natural del panel izquierdo "encoge" → tkinter recalcula → `uniform` redistribuye **ambas columnas** → el `_parent_frame` cambia de ancho.

Confirmado con datos de diagnóstico:
```
show=True  | _parent_frame=1155  _parent_canvas=1139  _scrollbar=24
show=False | _parent_frame=1408  _parent_canvas=1392  _scrollbar=24
```
El `_parent_frame` salta de 1155 a 1408px — es el frame externo, no algo interno al CTkScrollableFrame. El `minsize=16` en col=1 del `_parent_frame` interno estaba funcionando correctamente (nunca se perdió), pero el problema era un nivel más arriba.

### Intentos fallidos

**Intento 1 — `configure(width=0)` en la scrollbar**
```python
# ❌ CTk redistribuye el espacio igual al hacer width=0
_sb_izq.configure(width=0 if not should_show else _sb_izq_width)
```
CTk no respeta `width=0` como "reservar espacio".

**Intento 2 — `grid_columnconfigure(1, minsize=...)` en `_parent_frame` interno**
```python
# ❌ El minsize se aplica bien y nunca se pierde, pero el problema
#    está un nivel más arriba (en _content_frame con uniform="cols")
self._panel_izq._parent_frame.grid_columnconfigure(1, minsize=_sb_izq_width)
```
El minsize funcionó correctamente (confirmado con prints), pero no resuelve el layout shift porque la causa es el `uniform` del contenedor externo.

**Intento 3 — Sacar `uniform="cols"` del `_content_frame`**
```python
# ❌ Rompe la proporción visual 55/45 — los paneles quedan ~30/70
self._content_frame.grid_columnconfigure(0, weight=55, minsize=480)
self._content_frame.grid_columnconfigure(1, weight=45, minsize=360)
```
Sin `uniform`, el `weight` no reparte el espacio de forma proporcional cuando los contenidos tienen tamaños naturales distintos. Los paneles pierden la proporción visual deseada.

### Por qué oscila: el chicken-and-egg de layout

El análisis con prints confirma que es un problema de **orden de cálculo**:

```
panel necesita width → ¿cabe el contenido? → ¿aparece scrollbar?
       ↑                                              ↓
       └──── uniform recalcula ←── scrollbar cambia req ←┘
```

`grid_remove` / `grid` cambia el `req` de `_parent_frame` entre 300px (sin scrollbar) y 324px (con scrollbar). Ese delta de 24px se propaga hacia arriba hasta `_content_frame`, donde el `uniform="cols"` redistribuye **ambas columnas**, causando que el panel salte entre 1155px y 1408px. El mismo loop ocurre al seleccionar un hotel: agregar inputs crece el contenido → scrollbar aparece → req cambia → uniform redistribuye → panel se ensancha → contenido cabe → scrollbar desaparece → loop.

**Causa raíz:** cualquier técnica basada en `grid_remove`/`grid` tiene este problema porque inevitablemente cambia el `req` del contenedor padre.

### Opción A — Color trick (siempre en grid, colores transparentes)

La scrollbar **permanece en grid** en todo momento, conservando su col=1 de 24px. Cuando hay que "ocultarla", se configura con los mismos colores que el fondo. El `req` del `_parent_frame` nunca cambia → `uniform` nunca recalcula.

```python
BG = Colors.SURFACE

def _aplicar():
    if should_show:
        _sb_izq.configure(fg_color=SCROLLBAR_BG, button_color=SCROLLBAR_THUMB,
                          button_hover_color=SCROLLBAR_THUMB_HOVER)
    else:
        _sb_izq.configure(fg_color=BG, button_color=BG, button_hover_color=BG)
```

✅ Req estable, sin layout shift  
❌ Siempre hay 24px "muertos" a la derecha del panel cuando no hay scroll  
❌ El usuario puede hacer click en el área aunque sea invisible

### Opción B — Place trick (overlay, fuera del grid) ← aplicada

La scrollbar se saca del grid **una sola vez** al init con `grid_remove()`. Se reposiciona con `place()` flotando sobre el canvas cuando hay overflow. El grid de `_parent_frame` queda con una sola columna activa → `req` siempre estable → sin layout shift.

```python
_sb_izq.grid_remove()   # una sola vez, al init
_sb_w = max(_sb_izq.winfo_reqwidth(), 12)
_sb_izq.configure(width=_sb_w)  # CTk.place() prohíbe pasar width — se fija acá

def _auto_hide_izq(lo, hi):
    _sb_izq.set(lo, hi)
    should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)

    def _aplicar():
        if should_show:
            _sb_izq.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")
        else:
            _sb_izq.place_forget()

    _parent_canvas.after(0, _aplicar)

_parent_canvas.configure(yscrollcommand=_auto_hide_izq)
```

> **CTK quirk:** `CTkBaseClass.place()` lanza `ValueError` si recibís `width` o `height` como kwargs — los quiere en `configure()` o en el constructor. `relwidth`/`relheight` sí se aceptan porque son del geometry manager de Tk, no de CTK.

✅ Req estable, sin layout shift  
✅ Canvas usa el 100% del ancho (sin gap permanente)  
❌ Scrollbar overlayea ~24px del contenido en el borde derecho al hacer scroll

**Por qué `place()` no afecta el req:** `place` es un geometry manager posicional puro. A diferencia de `grid` y `pack`, no participa en el cálculo del `req` del contenedor padre — el contenedor actúa como si el widget colocado con `place` no existiera a efectos de sizing. Por eso `grid_remove()` al init + `place()`/`place_forget()` después no genera ningún recálculo de `uniform`.

### Solución aplicada ✅

Opción B implementada en `Hoteles/UI/interfaz_ctk.py` → `_crear_panel_izquierdo()`. **Confirmada: sin layout shift al startup ni al seleccionar hotel con edificio.**

#### Pendiente estético

La scrollbar se ve visualmente ancha (24px) porque `winfo_reqwidth()` devuelve el ancho original del widget, dimensionado para vivir en el grid. Al flotar como overlay encima del contenido ese grosor se nota más. Se puede reducir ajustando `_sb_w` directamente:

```python
_sb_w = 8   # en lugar de max(_sb_izq.winfo_reqwidth(), 12)
_sb_izq.configure(width=_sb_w)
```

---

## Layout — grid_remove() en constructor no tiene efecto

**Estado**: ✅ Resuelto

**Archivos afectados**: [UI/components/ctk_progress_panel.py](../../Hoteles/UI/components/ctk_progress_panel.py), [UI/interfaz_ctk.py](../../Hoteles/UI/interfaz_ctk.py)

### Síntoma

Un widget CTk aparece visible al iniciar la app aunque su `__init__` llama a `self.grid_remove()`.

### Causa

`grid_remove()` solo funciona si el widget **ya fue gridd-eado al menos una vez** previamente. Si nunca se llamó `.grid(...)`, `grid_remove()` no tiene efecto y el widget queda visible.

El orden incorrecto era:
```
__init__ → super().__init__() → self.grid_remove()   # sin slot registrado → no-op
interfaz → self.progress_panel.grid(row=0, ...)       # recién acá se registra el slot
```

### Solución

Usar el patrón `mostrar()`/`ocultar()` con `_grid_kwargs`. El componente arranca **sin slot registrado** y lo registra solo cuando se llama `mostrar()`:

```python
class MiPanel(ctk.CTkFrame):
    def __init__(self, master, grid_kwargs: dict | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self._grid_kwargs = grid_kwargs or {}
        # NO llamar grid() aquí

    def mostrar(self):
        self.grid(**self._grid_kwargs)   # registra slot + muestra

    def ocultar(self):
        self.grid_forget()               # libera slot y espacio
```

En la interfaz:
```python
self.panel = MiPanel(
    parent,
    grid_kwargs={"row": 0, "column": 0, "sticky": "ew"},
)
# panel arranca invisible sin ocupar espacio — sin llamadas extra
```

> Ver convención completa en [convenciones.md — Visibilidad dinámica](../desarrollo/convenciones.md#visibilidad-dinámica-mostrar--ocultar)

---

---

## CTkCustomDropdown — Seleccionar una opción reabre el dropdown inmediatamente

**Estado**: ✅ Resuelto

**Archivo afectado**: [UI/components/ctk_custom_dropdown.py](../../Hoteles/UI/components/ctk_custom_dropdown.py)

### Síntoma

Al hacer click en una opción del dropdown:
1. Por un microsegundo se ve la opción seleccionada en el input (label)
2. El dropdown reabre solo
3. El label vuelve a mostrar el placeholder ("Seleccionar..." / "Buscar...")
4. Solo al hacer click fuera se cierra y se ve la opción correcta

### Causa

El mismo evento `<Button-1>` del mouse que dispara el `command` del botón de la opción se propaga al widget que quedó debajo al cerrarse el Toplevel.

El flujo es:

1. Usuario hace click sobre el botón de una opción → `_select_option(value)` corre
2. `_close_dropdown()` destruye el `Toplevel` → el widget que queda "encima" es el `_display_label`
3. `_desactivar_modo_busqueda()` oculta el `_search_entry` y re-empaqueta el `_display_label`
4. El evento `<Button-1>` que originó el click **sigue propagándose** en la cola de eventos de Tk
5. Ese mismo evento cae sobre el `_display_label` recién visible, que tiene binding:
   ```python
   self._display_label.bind("<Button-1>", lambda _: self._activar_modo_busqueda(), add="+")
   ```
6. `_activar_modo_busqueda()` se ejecuta → el dropdown vuelve a abrirse

Es un clásico problema de **event propagation** en tkinter con Toplevel: el click que cierra la ventana flotante alcanza al widget subyacente en el mismo ciclo de eventos.

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `_set_display(value)` directo antes de `textvariable.set()` | El label se actualiza antes que el trace, pero el reopen sigue — no resuelve la propagación del evento |
| 2 | Agregar `update_idletasks()` entre `_set_display` y `textvariable.set` | Contraproducente: `update_idletasks()` procesa eventos pendientes de Tk (incluyendo `<FocusIn>` y `<Button-1>`) anticipadamente, agravando el reopen en lugar de resolverlo |

### Solución — flag de cooldown `_just_selected`

Agregar un flag de cooldown que bloquea `_activar_modo_busqueda` durante 200ms después de una selección. El display se actualiza llamando `_set_display(value)` directamente **después** de `_desactivar_modo_busqueda()`, antes de `textvariable.set()`, para que el label tenga el valor correcto en el mismo tick sin depender del trace:

```python
# En __init__:
self._just_selected = False  # bloquea _activar_modo_busqueda: el <Button-1> que cerró
                              # el Toplevel se propaga al display_label recién visible

# En _activar_modo_busqueda:
def _activar_modo_busqueda(self):
    if self._search_mode or self._just_selected:   # ← bloqueo por cooldown
        return
    ...

# En _select_option:
def _select_option(self, value):
    self._just_selected = True
    self.after(200, lambda: setattr(self, "_just_selected", False))  # ← reset tras 200ms
    self._close_dropdown()
    if self._search_mode:
        self._desactivar_modo_busqueda()       # re-packea el display_label (con texto viejo)
    self._set_display(value)                   # actualiza el label síncronamente
    if self.textvariable:
        self.textvariable.set(value)           # sincroniza la StringVar (trace llama _set_display de nuevo, no-op visual)
    if self.command:
        self.command(value)
```

**Por qué `_set_display` antes de `textvariable.set`**: `_desactivar_modo_busqueda()` re-packea el `_display_label` con el texto que tenía antes (placeholder o valor anterior). Llamar `_set_display(value)` inmediatamente después lo corrige en el mismo tick, antes de que el event loop procese cualquier render. El `textvariable.set()` que viene después dispara el trace que llama `_set_display` de nuevo, pero es un no-op visual porque el texto ya es correcto.

**Por qué 200ms**: es suficiente para que el evento `<Button-1>` se drene completamente de la cola de eventos de Tk (típicamente < 16ms), pero imperceptible para el usuario.

**Por qué `setattr`**: `lambda: setattr(self, "_just_selected", False)` es equivalente a un método nombrado pero más compacto para un reset de una sola variable. `after` acepta cualquier callable.

### Regla general

Cuando un `Toplevel` con `wm_overrideredirect(True)` se cierra en respuesta a un click, el evento `<Button-1>` puede propagarse al widget que quedó debajo. Si ese widget tiene un binding que reabre el popup, se genera un loop de open/close. La solución es un **flag de cooldown** que bloquea el reopen durante el tiempo mínimo para que el evento se drene (~200ms).

---

Ver también:
- [componentes.md](componentes.md) — Componentes CTk y CTkCustomDropdown

---

## Layout — Threshold numérico para decidir si usar CTkScrollableFrame

**Estado**: ✅ Resuelto

**Archivo afectado**: [UI/components/ctk_precio_panel.py](../../Hoteles/UI/components/ctk_precio_panel.py)

### Síntoma

Un panel que muestra N items dinámicos (periodos de precio) los clipeaba silenciosamente cuando la cantidad superaba el espacio visible, sin mostrar scrollbar. La cantidad máxima que se veía era siempre la misma (1 o 2 de 3-4 posibles), sin error ni advertencia.

### Causa

El código condicionaba la creación del `CTkScrollableFrame` con un número hardcodeado:

```python
# ❌ MALA PRÁCTICA — número arbitrario que depende del tamaño de pantalla
if len(precios_data) > 3:
    scroll_frame = ctk.CTkScrollableFrame(...)
    container = scroll_frame
else:
    container = self.content_frame  # CTkFrame sin scroll → items clippeados
```

El threshold `> 3` asume que 3 items siempre van a caber visualmente. Eso depende de:
- El tamaño de la ventana (que el usuario puede cambiar)
- La resolución y DPI del monitor del usuario
- El tamaño de cada item (que puede crecer si tiene más texto)

Cualquier número hardcodeado va a ser **correcto para la pantalla del desarrollador y roto para la del usuario**.

### Por qué el clippeo es silencioso

Un `CTkFrame` regular (sin scroll) renderiza sus hijos con `pack` normalmente — no hay error. El contenido simplemente se dibuja fuera del área visible del frame. CTk no lanza advertencia ni recorta visualmente con una línea clara.

### Solución — siempre `CTkScrollableFrame` + auto-hide via `yscrollcommand`

`CTkScrollableFrame` **no auto-oculta su scrollbar** (ver sección [Scroll / Scrollbar — CTkScrollableFrame muestra scrollbar aunque el contenido cabe](#scroll--scrollbar--ctkscrollableframe-muestra-scrollbar-aunque-el-contenido-cabe)). Hay que combinar dos cosas:

1. Eliminar el threshold — siempre usar `CTkScrollableFrame` como container
2. Hookear `yscrollcommand` para ocultar la scrollbar cuando el contenido cabe

```python
# ✅ CORRECTO — sin threshold + auto-hide
scroll_frame = ctk.CTkScrollableFrame(
    self.content_frame,
    fg_color="transparent",
    scrollbar_button_color=Colors.PRIMARY,
    scrollbar_button_hover_color=Colors.PRIMARY_HOVER
)
scroll_frame.pack(fill='both', expand=True)

_sb = scroll_frame._scrollbar
_canvas = scroll_frame._parent_canvas

def _auto_hide(lo, hi):
    _sb.set(lo, hi)
    should_show = not (float(lo) <= 0.005 and float(hi) >= 0.995)
    _canvas.after(0, _sb.grid if should_show else _sb.grid_remove)

_canvas.configure(yscrollcommand=_auto_hide)
container = scroll_frame
```

### Regla general

**Nunca** condicionar la creación de un `CTkScrollableFrame` con un número hardcodeado de items. Siempre usarlo como container cuando el contenido es dinámico, y siempre aplicar el hook `yscrollcommand` para auto-ocultar la scrollbar. Sin el hook, la scrollbar aparece aunque el contenido entre perfectamente en el viewport.

---

## Scroll / MouseWheel — Dos CTkScrollableFrame anidados se scrollean simultáneamente

**Estado**: ✅ Resuelto

**Archivo afectado**: [UI/components/ctk_periodos_panel.py](../../Hoteles/UI/components/ctk_periodos_panel.py)

### Síntoma

Al scrollear dentro de un `CTkScrollableFrame` interno (panel de periodos), el `CTkScrollableFrame` externo (panel derecho completo) también se scrollea. El problema se nota especialmente en los gaps entre cards de periodo, donde no hay widgets hijos directos.

### Causa

`CTkScrollableFrame` usa `bind_all("<MouseWheel>", ...)` — un binding global que dispara para cualquier evento de scroll en toda la aplicación. Cuando hay dos `CTkScrollableFrame` anidados, ambos tienen su `bind_all` activo simultáneamente.

La guardia interna `check_if_master_is_canvas()` sube por `.master` para determinar si el widget bajo el cursor le pertenece. En los **gaps entre widgets hijos** (zonas vacías del scroll_frame interno), el widget bajo el cursor pertenece a la jerarquía del outer también → ambos `bind_all` disparan al mismo tiempo.

### Intentos anteriores (descartados)

| # | Intento | Resultado |
|---|---------|-----------|
| 1 | `bind("<Enter>/<Leave>")` sobre el `scroll_frame` para activar/desactivar un override | `<Enter>/<Leave>` nunca dispara en `CTkScrollableFrame` — la estructura interna (canvas, frame) intercepta los eventos antes de que lleguen al frame raíz |

### Solución — `bind_all` con guardia `winfo_containing` + cleanup en `<Destroy>`

Registrar un `bind_all` adicional en la root que, en cada evento de scroll, verifica si el widget bajo el cursor está dentro del `scroll_frame` interno. Si sí, scrollea ese canvas y devuelve `"break"` para bloquear el handler del outer.

```python
def _aislar_scroll(self, scroll_frame):
    root = self.winfo_toplevel()
    _canvas = scroll_frame._parent_canvas

    def _solo_aqui(event):
        widget_bajo_cursor = root.winfo_containing(event.x_root, event.y_root)
        if not self._es_hijo_de(widget_bajo_cursor, scroll_frame):
            return
        _canvas.yview_scroll(int(-event.delta / 6), "units")
        return "break"

    bid = root.bind("<MouseWheel>", _solo_aqui, add="+")
    scroll_frame.bind("<Destroy>", lambda _: root.unbind("<MouseWheel>", bid), add="+")

def _es_hijo_de(self, widget, contenedor):
    w = widget
    while w is not None:
        if w is contenedor:
            return True
        w = getattr(w, "master", None)
    return False
```

**Por qué `winfo_containing(event.x_root, event.y_root)`**: devuelve el widget que está visualmente bajo el cursor en coordenadas absolutas de pantalla. Es la forma correcta de saber "¿dónde está el mouse ahora mismo?" independientemente de en qué widget se originó el evento.

**Por qué `return "break"`**: en Tkinter, devolver `"break"` desde un handler cancela la ejecución de los handlers siguientes en la cadena de bindings. Como el nuestro se registra con `add="+"` (último en registrarse = primero en ejecutarse), el `"break"` evita que el `bind_all` del outer se ejecute.

**Por qué `<Destroy>` para cleanup**: `actualizar_periodos()` llama `widget.destroy()` sobre los hijos al reconstruir el contenido. Cuando el `scroll_frame` se destruye, dispara `<Destroy>` automáticamente. Ahí se llama `root.unbind("<MouseWheel>", bid)` con el ID específico del binding — solo desregistra ese handler, sin afectar otros `bind_all` activos. Evita la acumulación de bindings con cada selección de habitación.

### Regla general

Cuando haya dos `CTkScrollableFrame` anidados y el outer interfiera con el scroll del inner:
1. Usar `root.bind("<MouseWheel>", handler, add="+")` con guardia `winfo_containing` + `_es_hijo_de`
2. Guardar el `bid` que devuelve `bind()` y liberarlo en `<Destroy>` del inner frame
3. No usar `<Enter>/<Leave>` — no disparan en `CTkScrollableFrame`
- [../desarrollo/debugging.md](../desarrollo/debugging.md) — Debugging general
