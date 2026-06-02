# CTkInlineSuggester — Autocomplete inline para editors de texto

## Qué hace

Popup de sugerencias que se activa mientras el usuario escribe dentro de un contexto delimitado (ej: `{`). Similar al autocomplete de VSCode para variables de template.

## Componentes involucrados

| Archivo | Cambio |
|---------|--------|
| `UI/components/ctk_inline_suggester.py` | Nuevo componente |
| `UI/components/ctk_text_editor.py` | Recibe `autocomplete_options`, `trigger_char`, `close_char`, `n` |
| `UI/views/config_modal.py` | Pasa `EMAIL_TAGS` al `CTkTextEditor` del tab Email |
| `Core/email_templates.py` | Exporta `EMAIL_TAGS` como constante |

## API del componente

```python
suggester = CTkInlineSuggester(
    text_widget=tk.Text,       # el tk.Text interno del editor
    options=["hotel", ...],    # lista de opciones
    trigger_char="{",          # char que activa el popup (default "{")
    close_char="}",            # char que se agrega al completar (default "}")
    n=1,                       # mínimo de letras después del trigger para activar
)
suggester.attach()   # bindea los eventos al text_widget
suggester.detach()   # desvincula
```

## Integración en CTkTextEditor

```python
CTkTextEditor(
    parent,
    autocomplete_options=["hotel", "habitacion_excel", ...],
    trigger_char="{",
    close_char="}",
    n=1,
)
```

## Lógica de detección

En cada `KeyRelease`, busca hacia atrás desde `INSERT`:
1. Si encuentra `trigger_char` sin `close_char` intermedio → extrae prefijo
2. Si `len(prefijo) >= n` → filtra opciones con `option.lower().startswith(prefijo.lower())`
3. Si hay matches → muestra popup posicionado bajo el cursor
4. Si no hay matches o se cerró el contexto → cierra popup

## Navegación del popup

- `↑` / `↓` — moverse entre opciones
- `Tab` / `Return` — confirmar selección → reemplaza `{prefijo` por `{tag}`
- `Escape` — cerrar sin seleccionar

## Tags de email disponibles

Definidos en `Core/email_templates.py` como `EMAIL_TAGS`:

```python
EMAIL_TAGS = [
    "hotel", "habitacion_excel", "habitacion_web",
    "periodo_id", "fecha_inicio_periodo", "fecha_fin_periodo",
    "fecha_inicio_busqueda", "fecha_fin_busqueda",
    "precio_excel", "precio_web", "diferencia", "estado",
    "firma",
]
```
