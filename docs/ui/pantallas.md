# Pantallas de la Aplicación

Descripción visual y funcional de las pantallas principales.

> **Nota**: La interfaz fue migrada a **CustomTkinter** (`interfaz_ctk.py`, clase `CrawlCompareGUI`).
> La interfaz legacy Tkinter (`interfaz.py`, clase `InterfazApp`) se mantiene por compatibilidad.

## Pantalla Principal

### Layout General (CustomTkinter)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Crawl-Compare - Comparador de Precios                       [HEADER]   │
├──────────────────────────────────┬──────────────────────────────────────┤
│  PANEL IZQUIERDO (55%)           │  PANEL DERECHO (45%)                 │
│  (fondo blanco)                  │  (fondo #F8FAFC)                     │
│                                  │                                       │
│  ╔═══════════════════════╗       │  ╔════════════════════════════╗      │
│  ║ 🏨 SELECCIÓN RESERVA  ║       │  ║  PRECIO                    ║      │
│  ╠═══════════════════════╣       │  ╠════════════════════════════╣      │
│  ║ Hotel                  ║      │  ║  low season                ║      │
│  ║ [Alvear Palace      ▼] ║      │  ║    01/05 - 31/05: $450.00  ║      │
│  ║                        ║      │  ║  high season               ║      │
│  ║ Habitación             ║      │  ║    01/12 - 31/12: $680.00  ║      │
│  ║ [dbl superior       ▼] ║      │  ╚════════════════════════════╝      │
│  ╚═══════════════════════╝       │                                       │
│                                  │  ╔════════════════════════════╗      │
│  ╔═══════════════════════╗       │  ║  PERIODOS                  ║      │
│  ║ 📅 FECHAS Y HUÉSPEDES ║       │  ╠════════════════════════════╣      │
│  ╠═══════════════════════╣       │  ║  low season                ║      │
│  ║ Fecha de entrada       ║      │  ║    01/05/2025 - 30/09/2025 ║      │
│  ║ [DD][MM][AAAA]         ║      │  ║  high season               ║      │
│  ║                        ║      │  ║    21/12/2025 - 10/01/2026 ║      │
│  ║ Fecha de salida        ║      │  ║                            ║      │
│  ║ [DD][MM][AAAA]         ║      │  ╚════════════════════════════╝      │
│  ║                        ║      │                                       │
│  ║ Adultos    Ninos       ║      │                                       │
│  ║ [2    ]    [0    ]     ║      │                                       │
│  ╚═══════════════════════╝       │                                       │
│                                  │                                       │
│  [  Ejecutar Comparacion  ]      │                                       │
│                                  │                                       │
│  RESULTADOS DE LA COMPARACION    │                                       │
│  ┌──────────────────────────────┐ │                                      │
│  │  (tabla comparativa aquí)   │ │                                      │
│  └──────────────────────────────┘ │                                      │
└──────────────────────────────────┴──────────────────────────────────────┘
```

### Diferencias respecto al layout legacy

| Característica | Legacy (InterfazApp) | Actual (CrawlCompareGUI) |
|---|---|---|
| Framework | Tkinter clásico | CustomTkinter |
| Dimensiones | 1200x800 | 1400x860 (máx.) |
| Min. size | 1000x600 | 900x600 |
| Layout | Columnas 50/50 | Columnas 55/45 |
| Formularios | Izquierda arriba | Izquierda (tarjetas CTkCard) |
| Resultados | Derecha | Izquierda debajo del formulario |
| Precio + Periodos | Derecha abajo | Panel derecho completo |
| Header | Sin header dedicado | Header oscuro fijo 56px |
| Edificio | Siempre visible | Dinámico (oculto si no aplica) |

### Secciones

#### 1. Header

Barra superior fija de 56px con fondo `Colors.HEADER_BG` (`#1E293B`).
- Título "Crawl-Compare - Comparador de Precios" en blanco

#### 2. Panel Izquierdo — Formulario de Selección

**Card "SELECCIÓN DE RESERVA"** (`CTkCard` con ícono 🏨):
- `CTkLabeledComboBox` (Hotel)
- `CTkLabeledComboBox` (Edificio) — Dinámico: aparece entre Hotel y Habitación solo si el hotel tiene tipos
- `CTkLabeledComboBox` (Habitación)

**Comportamiento**:
- Seleccionar hotel → carga edificios (si aplica) o habitaciones directo + limpia periodos
- Seleccionar edificio → carga habitaciones del edificio
- Seleccionar habitación → emite `habitacion_unificada_changed` → actualiza precio + periodos

#### 3. Panel Izquierdo — Formulario de Fechas

**Card "FECHAS Y HUÉSPEDES"** (`CTkCard` con ícono 📅):
- `CTkDateInput` (Entrada) — binds sobre `state.fecha_dia/mes/ano_entrada`
- `CTkDateInput` (Salida) — binds sobre `state.fecha_dia/mes/ano_salida`
- 2x `CTkEntry` en grilla (Adultos / Niños) — en `state.adultos` / `state.ninos`

Las fechas se consolidan automáticamente en `state.fecha_entrada_completa` y `state.fecha_salida_completa` vía `trace_add`.

#### 4. Botón Ejecutar

`CTkButton` con fondo `Colors.PRIMARY` (`#2563EB`), alto 44px.
Atajo de teclado: `Shift+Enter`.

#### 5. Panel Izquierdo — Resultados

Sección "RESULTADOS DE LA COMPARACION" debajo del botón.
Usa `VistaResultados` (ocupa todo el espacio restante, crece con la ventana).

Estados de la vista de resultados:

**a) Vacío (inicial)**:
```
Iniciando comparacion...
```

**b) Resultado Multi-Período**:
```
✅ COMPARACIÓN MULTI-PERÍODO COMPLETADA

Habitación Excel:  dbl superior w/breakfast
Habitación Web:    Double Superior Room with Breakfast
Match Score:       85.50

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERIODO         EXCEL      WEB        DIFERENCIA  STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
low season      $450.00    $455.00    $5.00       ❌ DIFF
high season     $680.00    $680.00    $0.00       ✅ OK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total periodos:      2
Con discrepancias:   1
```

**c) Error**:
```
Error: <mensaje de error>
```

#### 6. Panel Derecho — Precio y Periodos

`CTkPrecioPanel` + `CTkPeriodosPanel` con padding lateral `Spacing.LG` (24px).
El botón de Email se agrega dinámicamente **dentro** de `precio_panel.content_frame` si hay discrepancias.

---

## Modal de Email

Se abre con `tk.Toplevel` (600x450px) al hacer click en "Enviar Email".

```
┌─────────────────────────────────────────────┐
│  Enviar Email                               │
├─────────────────────────────────────────────┤
│  Contenido del Email:                       │
│  ┌─────────────────────────────────────┐   │
│  │  [Texto pre-generado editable]      │   │
│  │  ...                                │   │
│  └─────────────────────────────────────┘   │
│                                             │
│              [ Enviar Email ]               │
└─────────────────────────────────────────────┘
```

- Texto pre-generado por `generar_texto_email_multiperiodo()`
- Envío en background thread (no bloquea UI)
- Remitente/destinatario hardcodeados en `interfaz_ctk.py:587-588`

---

## Flujos de Navegación

### Flujo 1: Comparación Exitosa

```
1. Usuario abre app (CrawlCompareGUI.__init__)
2. Se cargan hoteles desde Excel → puebla hotel_combo
3. Selecciona hotel "Alvear Palace"
   → _on_hotel_changed() detecta si tiene tipos
   → Si tiene tipos: _mostrar_edificio() + _cargar_edificios()
   → Si no tiene tipos: _ocultar_edificio() + _cargar_habitaciones()
4. (Si aplica) Selecciona edificio
   → _on_edificio_changed() → _cargar_habitaciones(hotel, edificio)
5. Selecciona habitación
   → _on_habitacion_changed() → emite 'habitacion_unificada_changed'
   → _actualizar_periodos() → CTkPeriodosPanel.actualizar_periodos()
   → EventBus emite 'precios_actualizados' → CTkPrecioPanel.mostrar_precios_multiples()
6. Ingresa fechas (DD/MM/AAAA por separado)
   → trace_add consolida en fecha_entrada_completa / fecha_salida_completa
7. Click "Ejecutar Comparacion" (o Shift+Enter)
   → _ejecutar_comparacion() → ControladorComparacion.ejecutar_comparacion_async()
   → EventBus emite 'comparison_started' → limpia área de resultados
8. Scraping completa en background thread
   → EventBus emite 'comparison_completed' con ResultadoComparacionMultiperiodo
   → VistaResultados.mostrar_resultado_multiperiodo()
9. Si hay discrepancias:
   → _mostrar_email_btn() agrega CTkButton en precio_panel.content_frame
10. Click "Enviar Email" → _abrir_ventana_email() → modal Toplevel
```

### Flujo 2: Hotel con Edificio Dinámico

```
1. Selecciona hotel con tipos (ej. "Alvear Palace")
   → edificio_combo aparece entre hotel y habitación
2. Selecciona edificio
   → habitaciones se cargan filtradas por edificio
3. Al cambiar de hotel sin tipos:
   → edificio_combo se oculta automáticamente
```

### Flujo 3: Error de Scraping

```
1. Comparación falla en background thread
   → EventBus emite 'comparison_error' con mensaje
   → _on_comparison_error() inserta "Error: ..." en área de resultados
   → (Si es "Validacion fallida", el error se silencia — lo muestra el controlador)
```

---

## Estados de la Aplicación

| Estado | hotel_combo | btn_ejecutar | vista_resultados | btn_email |
|--------|------------|--------------|-----------------|-----------|
| Inicial | vacío | habilitado | vacío | oculto |
| Hotel seleccionado | valor | habilitado | vacío | oculto |
| Comparando | valor | deshabilitado* | "Iniciando..." | oculto |
| Con resultados OK | valor | habilitado | tabla multi-período | oculto |
| Con discrepancias | valor | habilitado | tabla multi-período | visible |
| Error | valor | habilitado | "Error: ..." | oculto |

*El controlador maneja enable/disable del botón vía EventBus.

---

## Colores y Estilos (CustomTkinter)

### Paleta de Colores (`UI/styles/colors.py`)

```python
Colors.PRIMARY          = "#2563EB"   # Azul eléctrico (botones, CTAs)
Colors.PRIMARY_HOVER    = "#1D4ED8"   # Azul hover
Colors.PRIMARY_LIGHT    = "#DBEAFE"   # Azul claro (backgrounds)

Colors.SUCCESS          = "#10B981"   # Verde (botón email, coincidencias)
Colors.SUCCESS_LIGHT    = "#D1FAE5"
Colors.WARNING          = "#F59E0B"   # Naranja
Colors.ERROR            = "#EF4444"   # Rojo (discrepancias)

Colors.BACKGROUND       = "#F8FAFC"   # Fondo app (gris muy claro)
Colors.SURFACE          = "#FFFFFF"   # Cards / Panel izquierdo
Colors.BORDER           = "#E2E8F0"   # Bordes

Colors.TEXT_PRIMARY     = "#1E293B"   # Texto principal
Colors.TEXT_SECONDARY   = "#64748B"   # Texto secundario
Colors.TEXT_DISABLED    = "#94A3B8"   # Texto disabled

Colors.HEADER_BG        = "#1E293B"   # Fondo header
Colors.HEADER_TEXT      = "#FFFFFF"   # Texto header
```

### Espaciado (`UI/styles/spacing.py`)

```python
Spacing.XS = 4 / SM = 8 / MD = 16 / LG = 24 / XL = 32
Spacing.CARD_PADDING   = 24
Spacing.FORM_GAP       = 20
Spacing.RADIUS_SM/MD/LG = 6 / 8 / 12
```

### Fuentes (`UI/styles/fonts.py` + `typography.py`)

```python
Typography.FAMILY = "Inter" (o fallback del sistema)
Typography.SMALL  = 11
Typography.BODY   = 13
Typography.BOLD   = "bold"
```

---

## Dimensiones

### Ventana Principal

- **Ancho máx**: 1400px (o 92% del ancho de pantalla)
- **Alto máx**: 860px (o 88% del alto de pantalla)
- **Centrada** en pantalla (con offset -20px vertical)
- **Resizable**: Sí (min 900x600)

### Proporciones

- **Panel izquierdo**: weight=55, minsize=480px
- **Panel derecho**: weight=45, minsize=360px

### Componentes

- **Header**: 56px de altura fija
- **Botón ejecutar**: 44px de altura
- **Botón email**: 36px de altura

---

Ver también:
- [componentes.md](componentes.md) — Detalles de cada componente (legacy + CTk)
- [vistas.md](vistas.md) — VistaResultados
- [modales.md](modales.md) — Modal de email
- [controladores.md](controladores.md) — Lógica de cada controlador
