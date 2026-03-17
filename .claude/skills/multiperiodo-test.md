# multiperiodo-test

Test completo del sistema multi-periodo con datos fake inventados o scraping real.

## Uso

```bash
python .claude/skills/scripts/multiperiodo_test.py [--modo fake|real] [--hotel HOTEL] [--habitacion HAB]
```

**Parámetros**:
- `--modo`: `fake` (default) o `real`
  - `fake`: UI cómoda para inventar datos web manualmente
  - `real`: Scraping de verdad con delays
- `--hotel`: Nombre del hotel (default: primer hotel del Excel)
- `--habitacion`: Nombre de habitación (default: primera habitación)

**Ejemplos**:
```bash
# Test modo fake (default) con UI para inventar datos
python .claude/skills/scripts/multiperiodo_test.py

# Test con hotel y habitación específicos
python .claude/skills/scripts/multiperiodo_test.py --modo fake --hotel "Alvear Palace" --habitacion "dbl superior"

# Test modo real (scraping de verdad)
python .claude/skills/scripts/multiperiodo_test.py --modo real
```

## Comportamiento

### Modo FAKE (default)

1. Carga hotel/habitación desde Excel
2. Detecta periodos aplicables automáticamente
3. Abre UI Tkinter con:
   - Entry para nombre de habitación web
   - Loop dinámico: Label(periodo.nombre) + Entry(precio) por cada periodo
   - Botón "Generar Comparación"
4. Usuario inventa datos web fácilmente
5. Al clickear botón:
   - Crea `HabitacionWeb` fake con `ComboPrecio` por periodo
   - Ejecuta `comparar_multiperiodo()` directamente
   - Muestra tabla comparativa en consola
   - Genera email con `generar_texto_email_multiperiodo()` (NO envía)
   - Muestra email en ventana Text editable
6. Guarda email en `tmp/multiperiodo-test-email-{timestamp}.txt`

### Modo REAL

1. Carga hotel/habitación desde Excel
2. Pide fechas de reserva al usuario
3. Infiere periodos aplicables desde fechas
4. Ejecuta scraping REAL con `force_fresh=True` por cada periodo
5. Muestra tiempos de scraping y delays aplicados
6. Ejecuta `comparar_multiperiodo()` completo
7. Muestra tabla comparativa
8. Genera y muestra email (sin enviar)

## Output esperado (modo fake)

```
🧪 Test Multi-Periodo - Modo FAKE

📊 Configuración:
   Hotel: Alvear Palace
   Habitación Excel: dbl superior w/breakfast
   Periodos aplicables: 3 (low season, high season, easter)

[Ventana Tkinter se abre con formulario]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UI - Inventar Datos Web
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Habitación Web: [ Double Superior Room with Breakfast ]

Periodo 1 - low season (01/05-31/05)
Precio: [ 140.00 ]

Periodo 2 - high season (01/06-30/06)
Precio: [ 180.00 ]

Periodo 3 - easter (02/04-05/04)
Precio: [ 165.00 ]

[ Generar Comparación ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Usuario llena datos y clickea botón]

🎯 Datos Web Inventados:
   Habitación web: "Double Superior Room with Breakfast"

   Periodo 1 (low season): $140.00
   Periodo 2 (high season): $180.00
   Periodo 3 (easter): $165.00

⚙️  Ejecutando comparación...

✅ Resultados:

┌──────────────┬─────────────┬────────────┬─────────────┬────────┐
│ Periodo      │ Precio Excel│ Precio Web │ Diferencia  │ Estado │
├──────────────┼─────────────┼────────────┼─────────────┼────────┤
│ low season   │ $150.00     │ $140.00    │ -$10.00     │ ❌ DIFF│
│ high season  │ $180.00     │ $180.00    │ $0.00       │ ✅ OK  │
│ easter       │ $170.00     │ $165.00    │ -$5.00      │ ❌ DIFF│
└──────────────┴─────────────┴────────────┴─────────────┴────────┘

📧 Email generado (NO enviado):

[Ventana Text se abre con contenido del email]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subject: Discrepancia de Precios - Alvear Palace

Se detectaron discrepancias en 2 de 3 periodos...

[contenido del email completo]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 Email guardado en: c:\Users\German\Gerssss\IA\Nueva carpeta\tmp\multiperiodo-test-email-20260131-123045.txt
```

## Notas de Implementación

### Modo FAKE

**UI Tkinter**:
```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Test Multi-Periodo - Inventar Datos Web")

# Entry para nombre habitación web
nombre_var = tk.StringVar()
ttk.Label(root, text="Habitación Web:").grid(row=0, column=0)
ttk.Entry(root, textvariable=nombre_var, width=40).grid(row=0, column=1)

# Loop dinámico por cada periodo
precio_vars = {}
for i, periodo in enumerate(periodos_aplicables, start=1):
    ttk.Label(root, text=f"{periodo.nombre} ({periodo.fecha_inicio.strftime('%d/%m')}-{periodo.fecha_fin.strftime('%d/%m')})").grid(row=i, column=0)
    var = tk.DoubleVar(value=0.0)
    precio_vars[periodo.id] = var
    ttk.Entry(root, textvariable=var, width=15).grid(row=i, column=1)

# Botón generar
ttk.Button(root, text="Generar Comparación", command=generar).grid(row=len(periodos)+1, column=0, columnspan=2)

root.mainloop()
```

**Crear HabitacionWeb fake**:
```python
def generar():
    nombre = nombre_var.get()

    # Crear ComboPrecio por cada periodo con el precio inventado
    combos = []
    for periodo in periodos_aplicables:
        precio = precio_vars[periodo.id].get()
        combos.append(ComboPrecio(
            titulo=nombre,
            descripcion=f"Inventado para {periodo.nombre}",
            precio=precio
        ))

    habitacion_web = HabitacionWeb(
        nombre=nombre,
        detalles="Habitación inventada para testing",
        combos=combos
    )

    # Llamar a comparar_multiperiodo()
    resultado = comparar_multiperiodo(...)
```

### Modo REAL

**Flujo**:
1. Pedir fechas con `input()` o Tkinter DateInputWidget
2. Inferir periodos con `inferir_periodos_desde_fechas()`
3. Ejecutar scraping con `dar_hotel_web(force_fresh=True)`
4. Comparar con `comparar_multiperiodo()`

**Diferencias con fake**:
- NO crear HabitacionWeb manualmente
- Scraping real tarda 2-3s por periodo + delay 2s
- Puede fallar si sitio está caído

## Dependencias

- `sys`, `os` - Argumentos y paths
- `argparse` - Parsing de argumentos
- `tkinter` - UI para modo fake
- `datetime` - Manejo de fechas
- Módulos del proyecto:
  - `Core.controller` - `dar_hoteles_excel()`, `generar_texto_email_multiperiodo()`
  - `Core.comparador_multiperiodo` - `comparar_multiperiodo()`, `ResultadoComparacionMultiperiodo`
  - `Core.servicio_habitaciones` - `inferir_periodos_desde_fechas()`, `unificar_habitaciones()`
  - `Models.hotelWeb` - `HabitacionWeb`, `ComboPrecio`
  - `Models.habitacion_unificada` - `HabitacionUnificada`
  - `UI.views.vista_resultados` - `VistaResultados`
  - `UI.styles.fonts` - `FontManager`

## Errores Comunes

### Error: "No se encontró hotel 'X'"
**Solución**: Verificar que el hotel existe en `Data/Extracto_prueba2.xlsx`

### Error: "No hay periodos aplicables"
**Solución**: Verificar que la habitación tiene `periodo_ids` asignados

### Modo real: Scraping falla
**Solución**: Ver [docs/scraper/troubleshooting.md](../../docs/scraper/troubleshooting.md)

---

Ver también:
- [docs/negocio/multiperiodo.md](../../docs/negocio/multiperiodo.md) - Sistema multi-periodo completo
- [Hoteles/CHECKPOINT_MULTIPERIODO.md](../../Hoteles/CHECKPOINT_MULTIPERIODO.md) - Detalles técnicos
