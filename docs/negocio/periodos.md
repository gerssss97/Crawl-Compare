# Sistema de Periodos

Explicación completa del manejo de periodos estacionales en el proyecto.

## Concepto

Los hoteles tienen **periodos estacionales** con precios diferentes:
- Low season (temporada baja)
- High season (temporada alta)
- Easter (pascua)
- Special events (eventos especiales)

Cada habitación puede tener múltiples precios dependiendo del periodo aplicable.

---

## Extracción desde Excel

**Archivo**: `ExtractorDatos/utils.py`

### Formato en Excel

```
Low Season: 1May25 - 30Sep25
dbl superior w/breakfast | $450
jr suite                 | $680

High Season: 21Dec25 - 10Jan26
dbl superior w/breakfast | $680
jr suite                 | $950

Easter: 2-5Apr26
dbl superior w/breakfast | $720
jr suite                 | $1020
```

### Regex Patterns de Extracción

**Patrón 1**: `(1May25 - 30Sep25)`

```python
patron = r'\((\d{1,2}[A-Za-z]{3}\d{2})\s*-\s*(\d{1,2}[A-Za-z]{3}\d{2})\)'

# Match: (1May25 - 30Sep25)
# Grupo 1: 1May25
# Grupo 2: 30Sep25
```

**Patrón 2**: `2-5Apr26`

```python
patron = r'(\d{1,2})-(\d{1,2})([A-Za-z]{3})(\d{2})'

# Match: 2-5Apr26
# Grupo 1: 2 (día inicio)
# Grupo 2: 5 (día fin)
# Grupo 3: Apr (mes)
# Grupo 4: 26 (año)
```

### Conversión a Formato DD-MM-YYYY

```python
from datetime import datetime

def parsear_fecha(fecha_str):
    """
    Convierte "1May25" → "01-05-2025"
    """
    # Parsear
    fecha_obj = datetime.strptime(fecha_str, "%d%b%y")

    # Formatear
    return fecha_obj.strftime("%d-%m-%Y")

# Ejemplo
parsear_fecha("1May25")   # → "01-05-2025"
parsear_fecha("30Sep25")  # → "30-09-2025"
```

### Asignación a Habitaciones

**Lógica**: Periodos se asignan por **proximidad de filas** en Excel.

```python
# Al encontrar nombre de periodo en fila 10
periodo = Periodo(
    nombre="low season",
    fecha_inicio="01-05-2025",
    fecha_fin="30-09-2025",
    row_idx=10  # Guardar índice de fila
)

# Habitaciones en filas 11, 12, 13 (dentro de 3 filas)
# → Se les asigna periodo.id

UMBRAL_PROXIMIDAD = 3  # Máximo 3 filas de distancia
```

**Implementación** (`ExtractorDatos/extractor.py:180-220`):

```python
def agregar_periodos_a_habitaciones(hotel, periodos_detectados):
    """
    Asigna periodos a habitaciones por proximidad de filas.
    """
    for habitacion in hotel.habitaciones_todas():
        hab_row = habitacion.row_idx

        for periodo in periodos_detectados:
            periodo_row = periodo.row_idx

            # Si habitación está cerca del periodo
            if abs(hab_row - periodo_row) <= UMBRAL_PROXIMIDAD:
                habitacion.periodo_ids.add(periodo.id)
```

---

## Modelo de Datos

### Clase Periodo

**Archivo**: `Models/periodo.py`

```python
class Periodo(BaseModel):
    id: int                  # Auto-incremental (1, 2, 3, ...)
    fecha_inicio: str        # Formato DD-MM-YYYY
    fecha_fin: str           # Formato DD-MM-YYYY
    nombre: str              # "low season", "high season", etc.
    row_idx: int = 0         # Índice de fila en Excel

    @staticmethod
    def _get_next_id():
        """Auto-incrementing ID global."""
        if not hasattr(Periodo, '_counter'):
            Periodo._counter = 0
        Periodo._counter += 1
        return Periodo._counter
```

### Clase PeriodoGroup

**Archivo**: `Models/hotelExcel.py`

```python
class PeriodoGroup(BaseModel):
    nombre: str              # "low season"
    periodos: List[Periodo]  # Lista de periodos con ese nombre

# Ejemplo: Low season puede tener 2 rangos de fechas
group = PeriodoGroup(
    nombre="low season",
    periodos=[
        Periodo(nombre="low season", fecha_inicio="01-05-2025", fecha_fin="30-09-2025"),
        Periodo(nombre="low season", fecha_inicio="01-11-2025", fecha_fin="20-12-2025"),
    ]
)
```

### HabitacionExcel con Periodos

```python
class HabitacionExcel(BaseModel):
    nombre: str
    precio: float
    row_idx: int
    periodo_ids: Set[int] = set()  # IDs de periodos aplicables

# Ejemplo
habitacion = HabitacionExcel(
    nombre="dbl superior w/breakfast",
    precio=450.0,
    row_idx=12,
    periodo_ids={1, 2, 3}  # 3 periodos aplicables
)
```

---

## Inferencia de Periodos Aplicables

**Función**: `inferir_periodos_desde_fechas()`
**Archivo**: `Core/servicio_habitaciones.py`

### Lógica de Overlap

Dado un rango de reserva (entrada → salida), determinar qué periodos se superponen:

```python
def inferir_periodos_desde_fechas(
    habitacion_unificada,
    fecha_entrada_str,
    fecha_salida_str
):
    """
    Determina qué periodos de la habitación se superponen con el rango de reserva.

    Args:
        habitacion_unificada: HabitacionUnificada
        fecha_entrada_str: str DD-MM-YYYY
        fecha_salida_str: str DD-MM-YYYY

    Returns:
        List[Periodo] - Periodos aplicables ordenados por fecha
    """
    from datetime import datetime

    # Parsear fechas de reserva
    reserva_inicio = datetime.strptime(fecha_entrada_str, "%d-%m-%Y")
    reserva_fin = datetime.strptime(fecha_salida_str, "%d-%m-%Y")

    periodos_aplicables = []

    for periodo in habitacion_unificada.periodos:
        # Parsear fechas del periodo
        periodo_inicio = datetime.strptime(periodo.fecha_inicio, "%d-%m-%Y")
        periodo_fin = datetime.strptime(periodo.fecha_fin, "%d-%m-%Y")

        # Verificar overlap
        if ranges_overlap(
            reserva_inicio, reserva_fin,
            periodo_inicio, periodo_fin
        ):
            periodos_aplicables.append(periodo)

    # Ordenar por fecha de inicio
    periodos_aplicables.sort(key=lambda p: datetime.strptime(p.fecha_inicio, "%d-%m-%Y"))

    return periodos_aplicables


def ranges_overlap(start1, end1, start2, end2):
    """
    Verifica si dos rangos de fechas se superponen.

    Returns:
        bool - True si hay overlap
    """
    return start1 <= end2 and start2 <= end1
```

### Ejemplo de Inferencia

```python
# Habitación con 3 periodos
habitacion = HabitacionUnificada(
    nombre="dbl superior w/breakfast",
    periodos=[
        Periodo(nombre="low season", fecha_inicio="01-05-2025", fecha_fin="30-09-2025"),
        Periodo(nombre="high season", fecha_inicio="21-12-2025", fecha_fin="10-01-2026"),
        Periodo(nombre="easter", fecha_inicio="02-04-2026", fecha_fin="05-04-2026"),
    ]
)

# Reserva del 15 al 20 de mayo de 2025
periodos_aplicables = inferir_periodos_desde_fechas(
    habitacion,
    "15-05-2025",
    "20-05-2025"
)

# Resultado: [Periodo("low season", "01-05-2025", "30-09-2025")]
# Solo low season se superpone con la reserva
```

### Caso Multi-Periodo

```python
# Reserva del 25 de diciembre de 2025 al 8 de enero de 2026
periodos_aplicables = inferir_periodos_desde_fechas(
    habitacion,
    "25-12-2025",
    "08-01-2026"
)

# Resultado: [Periodo("high season", "21-12-2025", "10-01-2026")]
# La reserva cae completamente dentro de high season
```

```python
# Reserva que cruza periodos: 20 diciembre 2025 - 15 enero 2026
periodos_aplicables = inferir_periodos_desde_fechas(
    habitacion,
    "20-12-2025",
    "15-01-2026"
)

# Resultado:
# [
#   Periodo("low season", "01-11-2025", "20-12-2025"),  # Overlap 1 día
#   Periodo("high season", "21-12-2025", "10-01-2026")  # Overlap 21 días
# ]
```

---

## Agrupación de Periodos

**Función**: `agrupar_periodos_por_nombre()`
**Archivo**: `Core/controller.py`

### Por qué Agrupar

Un mismo periodo puede tener **múltiples rangos de fechas**:

```
Low Season:
  - 1May25 - 30Sep25
  - 1Nov25 - 20Dec25

High Season:
  - 21Dec25 - 10Jan26
  - 1Apr26 - 30Apr26
```

### Implementación

```python
from collections import defaultdict
from Models.hotelExcel import PeriodoGroup

def agrupar_periodos_por_nombre(periodos: List[Periodo]) -> List[PeriodoGroup]:
    """
    Agrupa periodos por nombre.

    Args:
        periodos: List[Periodo] - Todos los periodos

    Returns:
        List[PeriodoGroup] - Periodos agrupados
    """
    grupos = defaultdict(list)

    for periodo in periodos:
        grupos[periodo.nombre].append(periodo)

    # Convertir a PeriodoGroup
    periodo_groups = [
        PeriodoGroup(nombre=nombre, periodos=periodos_lista)
        for nombre, periodos_lista in grupos.items()
    ]

    return periodo_groups
```

### Ejemplo

```python
periodos = [
    Periodo(id=1, nombre="low season", fecha_inicio="01-05-2025", fecha_fin="30-09-2025"),
    Periodo(id=2, nombre="low season", fecha_inicio="01-11-2025", fecha_fin="20-12-2025"),
    Periodo(id=3, nombre="high season", fecha_inicio="21-12-2025", fecha_fin="10-01-2026"),
]

grupos = agrupar_periodos_por_nombre(periodos)

# Resultado:
# [
#   PeriodoGroup(nombre="low season", periodos=[Periodo(id=1), Periodo(id=2)]),
#   PeriodoGroup(nombre="high season", periodos=[Periodo(id=3)])
# ]
```

---

## Visualización en UI

**Componente**: `PeriodosPanel`
**Archivo**: `UI/components/periodos_panel.py`

### Formato de Display

```
╔═══════════════════════════════════════╗
║ Periodos de la Habitación            ║
╠═══════════════════════════════════════╣
║                                       ║
║ Low Season (2 rangos)                 ║
║   • 01-05-2025 → 30-09-2025          ║
║   • 01-11-2025 → 20-12-2025          ║
║                                       ║
║ High Season (1 rango)                 ║
║   • 21-12-2025 → 10-01-2026          ║
║                                       ║
║ Easter (1 rango)                      ║
║   • 02-04-2026 → 05-04-2026          ║
║                                       ║
╚═══════════════════════════════════════╝
```

### Código de Visualización

```python
def mostrar_periodos(self, periodos_groups):
    """
    Muestra periodos agrupados en el panel.
    """
    self.text_widget.delete('1.0', tk.END)

    for group in periodos_groups:
        # Nombre del grupo
        self.text_widget.insert(tk.END, f"\n{group.nombre.upper()} ({len(group.periodos)} rango{'s' if len(group.periodos) > 1 else ''})\n", "bold")

        # Rangos de fechas
        for periodo in group.periodos:
            linea = f"  • {periodo.fecha_inicio} → {periodo.fecha_fin}\n"
            self.text_widget.insert(tk.END, linea)

    self.text_widget.insert(tk.END, "\n")
```

---

## Obtener Precio de Periodo

**Función**: `obtener_precio_periodo()`
**Archivo**: `Core/controller.py`

### Lógica

Cada habitación tiene un precio por periodo:

```python
def obtener_precio_periodo(habitacion_excel, periodo):
    """
    Obtiene el precio de la habitación para un periodo específico.

    Args:
        habitacion_excel: HabitacionExcel
        periodo: Periodo

    Returns:
        float o str - Precio numérico o "closing agreement"
    """
    # Si la habitación tiene ese periodo asignado
    if periodo.id in habitacion_excel.periodo_ids:
        return habitacion_excel.precio

    # Si no tiene el periodo, puede ser "closing agreement" u otro especial
    return "closing agreement"
```

### Precios Especiales

Algunos periodos pueden tener texto en vez de precio:

```
Easter: 2-5Apr26
dbl superior w/breakfast | closing agreement
jr suite                 | on request
```

**Manejo**:

```python
class HabitacionExcel(BaseModel):
    precio: float | str  # Puede ser número o string especial

    @field_validator('precio', mode='before')
    @classmethod
    def parse_precio(cls, v):
        if isinstance(v, str):
            # Intentar convertir a float
            try:
                return float(v.replace('$', '').replace(',', ''))
            except ValueError:
                # Es texto especial como "closing agreement"
                return v
        return v
```

---

## Casos Edge

### Periodo Sin Habitaciones

```python
# Periodo detectado pero ninguna habitación cercana
periodo = Periodo(
    nombre="special event",
    fecha_inicio="01-12-2025",
    fecha_fin="05-12-2025",
    row_idx=50
)

# Habitaciones más cercanas en fila 45 (distancia 5 > umbral 3)
# → Periodo NO se asigna a ninguna habitación
```

### Habitación Sin Periodos

```python
# Habitación sin periodo_ids
habitacion = HabitacionExcel(
    nombre="dbl superior",
    precio=400.0,
    row_idx=100,
    periodo_ids=set()  # Vacío
)

# Interpretación: Precio fijo todo el año (no estacional)
```

### Reserva Fuera de Periodos

```python
# Reserva del 1 al 5 de marzo de 2026
# Ningún periodo cubre esas fechas

periodos_aplicables = inferir_periodos_desde_fechas(...)
# → []

# Acción: Mostrar error al usuario
# "No hay periodos aplicables para las fechas seleccionadas"
```

---

## Performance

### Extracción de Periodos

- Regex matching: ~0.001s por fila
- Excel con 100 filas: ~0.1s total

### Asignación a Habitaciones

- Comparación de distancias: O(n*m) donde n=habitaciones, m=periodos
- Típico: 50 habitaciones × 5 periodos = 250 comparaciones
- Tiempo: ~0.005s

### Inferencia de Periodos

- Overlap checking: O(n) donde n=periodos de la habitación
- Típico: 3-5 periodos por habitación
- Tiempo: <0.001s

---

Ver también:
- [multiperiodo.md](multiperiodo.md) - Comparación multi-periodo completa
- [comparacion.md](comparacion.md) - Fuzzy matching de habitaciones
- [../arquitectura/modelo-datos.md](../arquitectura/modelo-datos.md) - Modelos Pydantic