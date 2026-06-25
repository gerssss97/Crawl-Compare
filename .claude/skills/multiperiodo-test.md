# multiperiodo-test

Test completo del sistema multi-periodo con datos fake inventados o scraping real.

## Uso

```bash
python .claude/skills/scripts/multiperiodo_test.py [--modo fake|real] [--hotel HOTEL] [--habitacion HAB]
```

**Parámetros**:
- `--modo`: `fake` (default) o `real`
  - `fake`: Formulario PySide6 para inventar datos web manualmente
  - `real`: No implementado todavía
- `--hotel`: Nombre del hotel (default: primer hotel del Excel)
- `--habitacion`: Nombre de habitación (default: primera habitación)

**Ejemplos**:
```bash
# Test modo fake (default) con UI Qt para inventar datos
python .claude/skills/scripts/multiperiodo_test.py

# Test con hotel y habitación específicos
python .claude/skills/scripts/multiperiodo_test.py --modo fake --hotel "Alvear Palace" --habitacion "dbl superior"
```

## Comportamiento

### Modo FAKE (default)

1. Carga hotel/habitación desde Excel
2. Detecta periodos aplicables automáticamente
3. Abre `MultiperiodoTestDialog` (PySide6 QDialog) con:
   - QLineEdit para nombre de habitación web
   - Un QDoubleSpinBox por cada periodo aplicable
   - Botón "Generar Comparación"
4. Al confirmar:
   - Crea `HabitacionWeb` fake con `ComboPrecio` por periodo
   - Construye `ResultadoComparacionMultiperiodo` directamente (sin scraping)
   - Abre `ResultadosWindow` con `QtVistaResultados` renderizando el resultado en HTML
   - Genera email con `generar_texto_email_multiperiodo()` (NO envía)
   - Guarda email en `tmp/multiperiodo-test-email-{timestamp}.txt`
   - Botón "Mostrar email generado" abre el texto en un QDialog

### Modo REAL

No implementado todavía.

## Output esperado (modo fake)

```
🧪 Test Multi-Periodo — Modo FAKE

📂 Cargando datos de Excel...
✅ Hotel: Alvear Palace
✅ Habitación: dbl superior w/breakfast
✅ Periodos: 3

[QDialog se abre con spinboxes por periodo]

[Usuario llena datos y confirma]

💾 Email guardado en: .claude/skills/tmp/multiperiodo-test-email-20260625-120530.txt

[ResultadosWindow se abre con QtVistaResultados mostrando tabla HTML]
```

## Dependencias

- `PySide6.QtWidgets` — UI (QDialog, QDoubleSpinBox, QScrollArea, QTextEdit)
- Módulos del proyecto:
  - `Core.controller` — `dar_hoteles_excel()`, `generar_texto_email_multiperiodo()`
  - `Core.comparador_multiperiodo` — `ResultadoComparacionMultiperiodo`, `ResultadoPeriodo`
  - `Core.servicio_habitaciones` — `unificar_habitaciones()`
  - `Models.hotelWeb` — `HabitacionWeb`, `ComboPrecio`
  - `UI_qt.widgets.qt_vista_resultados` — `QtVistaResultados`

## Errores Comunes

### Error: "No se encontró hotel 'X'"
**Solución**: Verificar que el hotel existe en `Data/Extracto.xls`

### Error: "No hay periodos aplicables"
**Solución**: Verificar que la habitación tiene `periodo_ids` asignados

---

Ver también:
- [docs/negocio/multiperiodo.md](../../docs/negocio/multiperiodo.md) - Sistema multi-periodo completo
