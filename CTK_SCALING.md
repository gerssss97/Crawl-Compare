# CTk Scaling - Problema y Solución

## El problema del doble escalado

CustomTkinter tiene su propio sistema de escala ENCIMA del DPI scaling de Windows.

Cuando creás un widget CTk con `width=100`:
- CTk internamente hace: `tkinter_width = int(100 * ctk_widget_scaling)`
- `winfo_width()` devuelve los píxeles reales ya escalados

Si pasás ese valor a OTRO widget CTk, se escala de nuevo:
```
winfo_width() = 860  (píxeles reales, post-scaling)
CTkFrame(width=860)  → CTk escala otra vez: 860 * 1.5 = 1290px  ← OVERFLOW!
```

## La solución: dividir por el factor de escala

```python
scaling = self._get_widget_scaling()   # método interno disponible en todo CTk widget
width_ctk = int(self.winfo_width() / scaling)
# Ahora: CTkFrame(width=width_ctk) → width_ctk * scaling = winfo_width() ✓
```

## Cuándo aplica

Siempre que necesites pasarle a un CTk widget un valor que obtuviste de `winfo_width()` o `winfo_height()`:
- `CTkFrame(width=..., height=...)`
- `CTkToplevel.geometry(f"{width}x{height}+{x}+{y}")`  ← el width/height, NO el x/y

## Las coordenadas x, y NO necesitan corrección

`winfo_rootx()` y `winfo_rooty()` devuelven coordenadas absolutas de pantalla.
`geometry(f"...+{x}+{y}")` también usa coordenadas absolutas de pantalla.
Son consistentes entre sí → no hace falta dividir por scaling.

## Caso real: CTkCustomDropdown

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

## Nota sobre la API

```python
self._get_widget_scaling()    # ✅ método privado pero estable, disponible en todo CTk widget
ctk.get_widget_scaling()      # ❌ NO existe como función global
ctk.set_widget_scaling(1.5)   # ✅ sí existe, pero es para forzar un valor global
```
