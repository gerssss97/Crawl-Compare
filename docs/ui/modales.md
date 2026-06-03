# Modales y Ventanas Secundarias

Documentación de ventanas modales (Toplevel) del proyecto.

## Envío de Email (mailto)

### Propósito

Tras una comparación con discrepancias, el botón "Enviar Email" del
`ResultadosModal` **no abre un modal propio**: genera el cuerpo del reporte y
abre el cliente de email predeterminado del SO vía `mailto:`.

> Histórico: existía un modal de redacción (`ModalEmail`) que enviaba por SMTP.
> Se eliminó. El editor de redacción ahora es el propio cliente de email del SO.

### Flujo

1. Comparación completada con discrepancias → `ResultadosModal` muestra el botón.
2. Usuario click "Enviar Email" → `ResultadosModal._abrir_email()`.
3. Se genera el cuerpo con `generar_texto_email_multiperiodo(...)` (template + firma de `ConfigService`).
4. `MailtoSender().enviar(destinatario="", asunto, cuerpo)` abre el cliente del SO.
5. El usuario completa destinatario y envía desde su cliente.

Detalle de límites de longitud y fallback a portapapeles: ver
[../negocio/email.md](../negocio/email.md).

<details>
<summary>Layout del modal viejo (eliminado, solo referencia histórica)</summary>

```
┌────────────────────────────────────────────────────────────────┐
│ Enviar Email - Discrepancia de Precio                    [×]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Preview del email (editable):                                │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ======================================================== │ │
│  │ DISCREPANCIAS DE PRECIO DETECTADAS                      │ │
│  │ ======================================================== │ │
│  │                                                          │ │
│  │ Habitación (Excel): dbl superior w/breakfast            │ │
│  │ Habitación (Web):   Double Superior Room with Breakfast │ │
│  │ Match: 85.50                                             │ │
│  │                                                          │ │
│  │ -------------------------------------------------------- │ │
│  │ PERIODO            EXCEL       WEB     DIFERENCIA STATUS │ │
│  │ -------------------------------------------------------- │ │
│  │ low season         $450.00    $455.00  $5.00      DIFF  │ │
│  │ high season        $680.00    $680.00  $0.00      OK    │ │
│  │ easter             $720.00    $750.00  $30.00     DIFF  │ │
│  │ -------------------------------------------------------- │ │
│  │                                                          │ │
│  │ Total periodos:          3                              │ │
│  │ Con discrepancias:       2                              │ │
│  │                                                          │ │
│  │ Verificar y actualizar tarifas según corresponda.       │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│                   [Enviar Email]  [Cancelar]                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Componentes

**Text Widget**: Editable, con scrollbar, fuente monospace
**Botón "Enviar Email"**: Verde, ejecuta envío
**Botón "Cancelar"**: Rojo, cierra sin enviar

### Código

**Función**: `crear_pantalla_mail()`
**Archivo**: `UI/interfaz.py:450-550`

```python
def crear_pantalla_mail(self, texto_email):
    """
    Crea modal de preview de email.

    Args:
        texto_email: str - Texto generado automáticamente
    """
    ventana = tk.Toplevel(self.root)
    ventana.title("Enviar Email - Discrepancia de Precio")
    ventana.geometry("800x600")
    ventana.transient(self.root)  # Modal sobre ventana principal
    ventana.grab_set()             # Bloquea interacción con ventana principal

    # ... componentes UI ...

    def enviar_email():
        texto_final = text_widget.get('1.0', tk.END).strip()

        try:
            from Core.controller import enviar_email_multiperiodo
            enviar_email_multiperiodo(texto_final)

            messagebox.showinfo("Éxito", "Email enviado correctamente")
            ventana.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar el email:\n{str(e)}")

    btn_enviar = tk.Button(
        button_frame,
        text="Enviar Email",
        command=enviar_email,
        bg="#4CAF50",
        fg="white"
    )

    btn_cancelar = tk.Button(
        button_frame,
        text="Cancelar",
        command=ventana.destroy,
        bg="#f44336",
        fg="white"
    )
```

### Flujo

1. Usuario completa comparación
2. Sistema detecta discrepancias
3. Genera texto de email
4. `crear_pantalla_mail(texto_email)` abre modal
5. Usuario puede editar texto en Text widget
6. **Opción A**: Click "Enviar Email"
   - Ejecuta `enviar_email_multiperiodo()`
   - Muestra confirmación de éxito/error
   - Cierra modal
7. **Opción B**: Click "Cancelar"
   - Cierra modal sin enviar

</details>

---

## MessageBox (Confirmaciones y Errores)

### Tipos Usados

#### 1. showinfo - Información

```python
from tkinter import messagebox

messagebox.showinfo("Éxito", "Email enviado correctamente")
```

**Uso**: Confirmación de acciones exitosas

#### 2. showerror - Error

```python
messagebox.showerror("Error", "No se pudo enviar el email:\nTimeout de conexión")
```

**Uso**: Mostrar errores al usuario

#### 3. showwarning - Advertencia

```python
messagebox.showwarning("Advertencia", "Las fechas ingresadas no tienen periodos aplicables")
```

**Uso**: Validaciones fallidas, advertencias

#### 4. askyesno - Confirmación

```python
respuesta = messagebox.askyesno(
    "Confirmar",
    "¿Seguro que desea re-ejecutar la comparación?\nEsto consumirá API calls."
)

if respuesta:
    # Usuario eligió "Sí"
    ejecutar_comparacion()
```

**Uso**: Pedir confirmación antes de acciones destructivas

---

## Futuros Modales (Diseño)

### Modal de Progress (Scraping Multi-Período)

**Propósito**: Mostrar progreso detallado durante scraping de múltiples periodos

```
┌───────────────────────────────────────────────────┐
│ Comparación Multi-Período en Progreso       [×]  │
├───────────────────────────────────────────────────┤
│                                                   │
│  Scrapeando 3 periodos...                        │
│                                                   │
│  ✅ Periodo 1/3: low season                      │
│     Scraping completado (7s)                     │
│     Match encontrado (score: 85.50)              │
│                                                   │
│  🔄 Periodo 2/3: high season                     │
│     Scraping en progreso...                      │
│                                                   │
│  ⏳ Periodo 3/3: easter                          │
│     Esperando...                                 │
│                                                   │
│  ████████████░░░░░░░░░░░░░  50%                 │
│                                                   │
│  Tiempo transcurrido: 14s                        │
│  Tiempo estimado restante: 14s                   │
│                                                   │
│                    [Cancelar]                    │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Implementación sugerida**:

```python
class ProgressModal:
    def __init__(self, root, total_periodos):
        self.ventana = tk.Toplevel(root)
        self.ventana.title("Comparación Multi-Período en Progreso")
        self.total_periodos = total_periodos
        self.current_periodo = 0

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.ventana,
            length=400,
            mode='determinate',
            maximum=total_periodos
        )
        self.progress_bar.pack(pady=10)

        # Label de estado
        self.status_label = tk.Label(self.ventana, text="")
        self.status_label.pack()

    def actualizar_periodo(self, periodo_idx, nombre, mensaje):
        self.current_periodo = periodo_idx
        self.progress_bar['value'] = periodo_idx
        self.status_label.config(
            text=f"Periodo {periodo_idx}/{self.total_periodos}: {nombre} - {mensaje}"
        )
        self.ventana.update()

# Uso en ControladorComparacion
progress = ProgressModal(root, len(periodos_aplicables))

for i, periodo in enumerate(periodos_aplicables, 1):
    progress.actualizar_periodo(i, periodo.nombre, "Scraping...")
    # ... scraping ...
    progress.actualizar_periodo(i, periodo.nombre, "Completado")

progress.ventana.destroy()
```

### Modal de Configuración

**Propósito**: Configurar parámetros del scraper sin editar .env

```
┌─────────────────────────────────────────────────────┐
│ Configuración                                  [×] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Scraper                                            │
│  ┌───────────────────────────────────────────────┐ │
│  │ Delay entre periodos (s): [2        ]        │ │
│  │ Timeout de página (s):     [60       ]        │ │
│  │ Máximo de reintentos:      [3        ]        │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Email (pestaña)                                    │
│  ┌───────────────────────────────────────────────┐ │
│  │ Firma:    [Germán Lucero                  ]   │ │
│  │ Template del email (editor + chips de tags)   │ │
│  │ [Estimado equipo de reservas, ...          ] │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│                 [Guardar]  [Cancelar]              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Modal de Ayuda/About

**Propósito**: Info del proyecto, versión, créditos

```
┌────────────────────────────────────────────────┐
│ Acerca de                                 [×] │
├────────────────────────────────────────────────┤
│                                                │
│  🏨 Comparador de Precios de Hoteles          │
│                                                │
│  Versión: 1.0.0                                │
│  Última actualización: 31 Enero 2026           │
│                                                │
│  Desarrollado con:                             │
│  • Python 3.12                                 │
│  • Tkinter (GUI)                               │
│  • Crawl4AI (Web Scraping)                     │
│  • DeepSeek-R1 (LLM Extraction)                │
│  • RapidFuzz (Fuzzy Matching)                  │
│                                                │
│  Co-Authored-By:                               │
│  Claude Sonnet 4.5 <noreply@anthropic.com>    │
│                                                │
│                  [Cerrar]                      │
│                                                │
└────────────────────────────────────────────────┘
```

---

## Pattern de Modal Genérico

### Template Base

```python
class ModalBase:
    """
    Clase base para modales.
    """
    def __init__(self, parent, titulo, ancho=600, alto=400):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(titulo)
        self.ventana.geometry(f"{ancho}x{alto}")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        # Centrar en pantalla
        self._centrar_ventana()

        # Frame principal
        self.frame = tk.Frame(self.ventana, padx=20, pady=20)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Construir UI (override en subclases)
        self._setup_ui()

    def _setup_ui(self):
        """Override en subclases."""
        pass

    def _centrar_ventana(self):
        """Centra ventana en pantalla."""
        self.ventana.update_idletasks()
        width = self.ventana.winfo_width()
        height = self.ventana.winfo_height()
        x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
        self.ventana.geometry(f'{width}x{height}+{x}+{y}')

    def cerrar(self):
        """Cierra el modal."""
        self.ventana.destroy()

# Uso
class MiModal(ModalBase):
    def _setup_ui(self):
        # Construir componentes específicos
        label = tk.Label(self.frame, text="Contenido del modal")
        label.pack()

        btn = tk.Button(self.frame, text="Cerrar", command=self.cerrar)
        btn.pack()
```

---

## Mejores Prácticas

### 1. Usar transient y grab_set

```python
ventana.transient(parent)  # Siempre sobre ventana principal
ventana.grab_set()         # Bloquea interacción con ventana principal
```

### 2. Centrar en Pantalla

Usar la función `_centrar_ventana()` del template base.

### 3. Destruir al Cerrar

Siempre llamar `ventana.destroy()` al cerrar (no `withdraw()`).

### 4. Manejo de Errores

Usar try-except dentro de callbacks de botones:

```python
def on_guardar():
    try:
        # ... lógica ...
        messagebox.showinfo("Éxito", "Guardado correctamente")
        ventana.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar:\n{str(e)}")
```

### 5. Validaciones Antes de Cerrar

```python
def on_cerrar():
    if datos_sin_guardar:
        respuesta = messagebox.askyesno(
            "Confirmar",
            "Hay cambios sin guardar. ¿Desea cerrar de todos modos?"
        )
        if respuesta:
            ventana.destroy()
    else:
        ventana.destroy()

ventana.protocol("WM_DELETE_WINDOW", on_cerrar)  # Handle [X] button
```

---

Ver también:
- [pantallas.md](pantallas.md) - Pantalla principal
- [componentes.md](componentes.md) - Componentes reutilizables
- [../negocio/email.md](../negocio/email.md) - Sistema de email