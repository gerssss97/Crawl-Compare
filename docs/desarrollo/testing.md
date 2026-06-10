# Testing del Proyecto

Guía completa para ejecutar tests, validar componentes y mockear datos.

## Tipos de Tests

El proyecto tiene 3 tipos principales de tests:

1. **Tests de Extracción de Excel** - Validan parseo de datos
2. **Tests de Componentes UI** - Validan widgets Tkinter standalone
3. **Tests de Scraper** - Validan web scraping y matching
4. **Tests de Lógica de Negocio** - Validan comparación y periodos

---

## 1. Tests de Extracción de Excel

### Test Principal: testExtractor2.py

**Ubicación**: `Tests/testExtractor2.py`

```bash
cd Hoteles
python Tests/testExtractor2.py
```

**Qué valida:**
- ✅ Parseo de hoteles desde `Data/Extracto_prueba2.xlsx`
- ✅ Extracción de tipos de habitaciones (edificios)
- ✅ Extracción de habitaciones con precios
- ✅ Extracción de periodos con rangos de fechas
- ✅ Asignación correcta de periodos a habitaciones
- ✅ Creación de `HabitacionUnificada` (bridge pattern)

**Output esperado:**
```
=== HOTELES ENCONTRADOS ===

Hotel: Alvear Palace
  Tipos: 2
  Habitaciones directas: 0
  Periodos: 3 grupos

Tipo: Main Building
  Habitaciones: 15
  Habitación: dbl superior w/breakfast
    - Precio: $450.00
    - Periodos aplicables: 2 (low season, high season)

... (más detalles)

✅ Extracción completada exitosamente
📝 Archivo generado: habitaciones_validacion.txt
```

**Archivo de validación**: `habitaciones_validacion.txt`

Contiene lista completa de habitaciones extraídas para revisión manual.

### Validar Extracción de Periodos

```bash
cd Hoteles
python -c "
from ExtractorDatos.extractor import GestorDatos

gestor = GestorDatos()
datos = gestor.dar_datos_excel()

for hotel in datos.hoteles:
    print(f'\nHotel: {hotel.nombre}')
    print(f'Periodos: {len(hotel.periodos_group)} grupos')

    for grupo in hotel.periodos_group:
        print(f'\n  Grupo: {grupo.nombre}')
        for periodo in grupo.periodos:
            print(f'    - {periodo.fecha_inicio} a {periodo.fecha_fin}')
"
```

**Output esperado:**
```
Hotel: Alvear Palace
Periodos: 3 grupos

  Grupo: low season
    - 01-05-2025 a 30-09-2025
    - 01-11-2025 a 20-12-2025

  Grupo: high season
    - 21-12-2025 a 10-01-2026
    - 01-04-2026 a 30-04-2026

  Grupo: easter
    - 02-04-2026 a 05-04-2026
```

---

## 2. Tests de Componentes UI

### Test Standalone de Componentes

Cada componente puede ejecutarse standalone para testing visual.

#### Test DateInputWidget

```bash
cd Hoteles
python -c "
import tkinter as tk
from UI.components.date_input_widget import DateInputWidget

root = tk.Tk()
root.title('Test DateInputWidget')

widget = DateInputWidget(root, label='Fecha de Prueba')
widget.pack(padx=20, pady=20)

def on_submit():
    fecha = widget.get_value()
    print(f'Fecha ingresada: {fecha}')
    root.quit()

btn = tk.Button(root, text='Obtener Valor', command=on_submit)
btn.pack(pady=10)

root.mainloop()
"
```

**Validaciones a realizar:**
- ✅ Ingresar fecha válida (ej: 15-02-2026) → debería aceptar
- ✅ Ingresar fecha inválida (ej: 32-13-2026) → debería mostrar error
- ✅ Ingresar formato incorrecto (ej: 15/02/2026) → debería mostrar error
- ✅ Campo vacío → debería permitir (si no es requerido)

#### Test LabeledComboBox

```bash
cd Hoteles
python -c "
import tkinter as tk
from UI.components.labeled_combobox import LabeledComboBox

root = tk.Tk()
root.title('Test LabeledComboBox')

opciones = ['Alvear Palace', 'Marriott', 'Hilton']
combo = LabeledComboBox(root, label='Hotel', values=opciones)
combo.pack(padx=20, pady=20)

def on_submit():
    seleccion = combo.get_value()
    print(f'Selección: {seleccion}')
    root.quit()

btn = tk.Button(root, text='Obtener Valor', command=on_submit)
btn.pack(pady=10)

root.mainloop()
"
```

#### Test PrecioPanel

```bash
cd Hoteles
python -c "
import tkinter as tk
from UI.components.precio_panel import PrecioPanel

root = tk.Tk()
root.title('Test PrecioPanel')

panel = PrecioPanel(root)
panel.pack(padx=20, pady=20)

# Simular actualización de precio
panel.set_value('$450.00')

root.mainloop()
"
```

### Usar Skill /ui-preview

Alternativamente, usar el skill personalizado:

```bash
python .claude/skills/scripts/ui_preview.py DateInputWidget
python .claude/skills/scripts/ui_preview.py LabeledComboBox
python .claude/skills/scripts/ui_preview.py PrecioPanel
```

---

## 3. Tests de Scraper

### Test Básico con Skill

```bash
python .claude/skills/scripts/test_scraper.py
```

**Output esperado:**
```
🔍 Testeando Scraper de Hoteles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hotel: alvear
Fechas: 2026-02-01 → 2026-02-02
Huéspedes: 2 adultos, 0 niños

⏱️  Scraping completado en 5.23s

📊 Resumen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Habitaciones encontradas: 15

Primeras 3 habitaciones:
  1. Double Superior Room - $450.00
  2. Junior Suite - $680.00
  3. Deluxe Suite - $920.00

💾 Datos guardados en: /tmp/test-scraper-20260131-143022.json
```

### Test con Parámetros Custom

```bash
# Scraping para fechas específicas
python .claude/skills/scripts/test_scraper.py alvear 15-02-2026 16-02-2026 2 1

# Scraping con 3 adultos
python .claude/skills/scripts/test_scraper.py alvear 01-03-2026 05-03-2026 3 0
```

### Test de Matching Manual

```bash
cd Hoteles
python -c "
from Core.comparador import encontrar_mejor_match, limpiar_nombre_excel

# Simular habitación de Excel
nombre_excel = 'dbl superior w/breakfast'
nombre_limpio = limpiar_nombre_excel(nombre_excel)
print(f'Nombre limpio: {nombre_limpio}')

# Simular habitaciones web (mock)
habitaciones_web = [
    type('obj', (object,), {'nombre': 'Double Superior Room'}),
    type('obj', (object,), {'nombre': 'Superior Double with Breakfast'}),
    type('obj', (object,), {'nombre': 'Deluxe Double'}),
]

mejor_match, score = encontrar_mejor_match(nombre_limpio, habitaciones_web)
print(f'\nMejor match: {mejor_match.nombre}')
print(f'Score: {score:.2f}')
"
```

### Test de Matching con Skill /compare-debug

```bash
python .claude/skills/scripts/compare_debug.py \
  "dbl superior w/breakfast" \
  "Double Superior Room" \
  "Superior Double with Breakfast" \
  "Deluxe Double"
```

**Output esperado:**
```
🔍 Fuzzy Matching Debug
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Habitación Excel (limpia): "dbl superior breakfast"
Habitación Excel (original): "dbl superior w/breakfast"
Incluye breakfast: ✅

Habitación Web                      Ratio  Partial  Sort   Set    Final  BF
────────────────────────────────────────────────────────────────────────────
Superior Double with Breakfast      72.00  85.00    78.00  80.00  79.25  ✅  ← MEJOR MATCH
Double Superior Room                65.00  78.00    70.00  72.00  71.50  ❌
Deluxe Double                       45.00  52.00    48.00  50.00  49.25  ❌
```

---

## 4. Tests de Lógica Multi-Periodo

### Test con Skill /multiperiodo-test (Modo Fake)

```bash
python .claude/skills/scripts/multiperiodo_test.py --modo fake
```

**Qué hace:**
1. Abre UI Tkinter
2. Seleccionar hotel, edificio, habitación
3. Ingresar fechas de reserva
4. UI muestra periodos aplicables con inputs de precio
5. Ingresar precios web fake manualmente
6. Click "Generar Comparación"
7. Ver tabla comparativa
8. Ver preview de email (sin enviar)

**Ideal para:**
- ✅ Validar lógica de inferencia de periodos
- ✅ Validar cálculo de diferencias
- ✅ Validar generación de email
- ✅ Testing sin consumir API calls

### Test con Modo Real

```bash
python .claude/skills/scripts/multiperiodo_test.py --modo real
```

**Advertencia**: Consume API calls de Groq (scraping real).

---

## 5. Mocking de Datos

### Mock de HotelExcel

```python
from Models.hotelExcel import HotelExcel, HabitacionExcel, Periodo

# Crear periodo mock
periodo = Periodo(
    fecha_inicio="01-05-2025",
    fecha_fin="30-09-2025",
    nombre="low season"
)

# Crear habitación mock
habitacion = HabitacionExcel(
    nombre="dbl superior w/breakfast",
    precio=450.0,
    row_idx=10,
    periodo_ids={periodo.id}
)

# Crear hotel mock
hotel = HotelExcel(
    nombre="Hotel Test",
    tipos=[],
    habitaciones_directas=[habitacion],
    periodos_group=[]
)

print(f"Hotel mock creado: {hotel.nombre}")
print(f"Habitaciones: {len(hotel.habitaciones_directas)}")
```

### Mock de HotelWeb

```python
from Models.hotelWeb import HotelWeb, HabitacionWeb, ComboPrecio

# Crear combo de precio mock
combo = ComboPrecio(
    titulo="Standard Rate",
    descripcion="Room only",
    precio=450.0
)

# Crear habitación web mock
habitacion_web = HabitacionWeb(
    nombre="Double Superior Room",
    combos_precios=[combo]
)

# Crear hotel web mock
hotel_web = HotelWeb(habitaciones=[habitacion_web])

print(f"Hotel web mock creado")
print(f"Habitaciones: {len(hotel_web.habitaciones)}")
```

### Mock de Resultado Multi-Periodo

```python
from Models.hotelExcel import Periodo
from Core.comparador_multiperiodo import ResultadoPeriodo, ResultadoComparacionMultiperiodo

# Crear periodos mock
periodo1 = Periodo(fecha_inicio="01-05-2025", fecha_fin="30-09-2025", nombre="low season")
periodo2 = Periodo(fecha_inicio="21-12-2025", fecha_fin="10-01-2026", nombre="high season")

# Crear resultados por periodo
resultado_p1 = ResultadoPeriodo(
    periodo=periodo1,
    precio_excel=450.0,
    precio_web=455.0,
    diferencia=5.0,
    coincide=False
)

resultado_p2 = ResultadoPeriodo(
    periodo=periodo2,
    precio_excel=680.0,
    precio_web=680.0,
    diferencia=0.0,
    coincide=True
)

# Crear resultado completo mock
resultado = ResultadoComparacionMultiperiodo(
    habitacion_excel_nombre="dbl superior w/breakfast",
    habitacion_web_matcheada=habitacion_web,  # Del mock anterior
    periodos=[resultado_p1, resultado_p2],
    mensaje_match="Match encontrado: Double Superior Room (score: 79.25)"
)

print(f"Tiene discrepancias: {resultado.tiene_discrepancias}")
print(f"Periodos evaluados: {len(resultado.periodos)}")
```

---

## 6. Validación de Convenciones

```bash
# Validar convenciones de código
python .claude/skills/scripts/check_conventions.py UI/components/
python .claude/skills/scripts/check_conventions.py UI/controllers/
python .claude/skills/scripts/check_conventions.py Core/
```

**Output esperado:**
```
🔍 Validando Convenciones del Proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ base_component.py
   ✓ Nombre en español
   ✓ Docstrings presentes

✅ date_input_widget.py
   ✓ Nombre en español
   ✓ BaseComponent pattern correcto
   ✓ Métodos requeridos: _setup_ui, get_value, set_value, reset

📊 Resumen: 5 archivos, 5 ✅, 0 ⚠️, 0 ❌
```

---

## 7. Pytest (Futuro)

El proyecto está preparado para usar pytest en el futuro:

```bash
# Crear directorio de tests pytest
mkdir -p Tests/pytest

# Ejemplo de test pytest
cat > Tests/pytest/test_comparador.py << 'EOF'
import pytest
from Core.comparador import limpiar_nombre_excel

def test_limpiar_nombre_excel():
    assert limpiar_nombre_excel("dbl superior w/breakfast") == "dbl superior breakfast"
    assert limpiar_nombre_excel("jr suite (w/balcony)") == "jr suite balcony"

def test_limpiar_nombre_excel_vacio():
    assert limpiar_nombre_excel("") == ""
EOF

# Ejecutar pytest
python -m pytest Tests/pytest/ -v
```

**Output esperado:**
```
======================== test session starts ========================
Tests/pytest/test_comparador.py::test_limpiar_nombre_excel PASSED
Tests/pytest/test_comparador.py::test_limpiar_nombre_excel_vacio PASSED

======================== 2 passed in 0.05s ========================
```

---

## Checklist de Testing Pre-Commit

Antes de hacer commit de cambios importantes:

- [ ] ✅ Ejecutar `python Tests/testExtractor2.py`
- [ ] ✅ Ejecutar `python .claude/skills/scripts/test_scraper.py`
- [ ] ✅ Ejecutar `python .claude/skills/scripts/check_conventions.py UI/`
- [ ] ✅ Validar componentes UI modificados standalone
- [ ] ✅ Testing manual de flujo completo en interfaz
- [ ] ✅ Verificar que `.env` no esté en commit (`git status`)

---

## Troubleshooting de Tests

### "ModuleNotFoundError" en tests

```bash
# Asegurar que estás en el directorio correcto
cd Hoteles

# Verificar que el entorno esté activado
conda activate crawler
```

### Tests de scraper fallan con timeout

- Aumentar `SCRAPING_DELAY_SECONDS` en `.env`
- Verificar API key de Groq
- Verificar conexión a internet

### Tests de UI no abren ventana

- Verificar que tkinter esté instalado (ver [setup.md](setup.md))
- En sistemas headless (sin GUI), los tests de UI no funcionarán

---

Ver también:
- [debugging.md](debugging.md) - Debugging avanzado
- [convenciones.md](convenciones.md) - Patrones de código
- [../scraper/troubleshooting.md](../scraper/troubleshooting.md) - Problemas de scraping