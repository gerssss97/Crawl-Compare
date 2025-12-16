"""Contexto de extracción para procesar datos del Excel de hoteles.

Este módulo encapsula el estado mutable durante la extracción del Excel,
separando las responsabilidades de procesamiento en métodos especializados.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from openpyxl.worksheet.worksheet import Worksheet

from Models.hotelExcel import HotelExcel, HabitacionExcel, TipoHabitacionExcel, Extra


@dataclass
class ContextoExtraccion:
    """Encapsula el estado mutable durante la extracción del Excel.

    Responsabilidades:
    - Mantener referencias a entidades actuales (hotel, tipo, periodos)
    - Gestionar buffers temporales (habitaciones_sin_periodos)
    - Coordinar la asignación de periodos a habitaciones
    - Procesar cada fila del Excel delegando a métodos especializados

    Atributos:
        hoteles: Lista acumulada de hoteles extraídos
        hotel_actual: Hotel siendo procesado actualmente
        tipo_actual: Tipo de habitación (edificio) siendo procesado
        fila_nombre_seasson: Número de fila donde se detectó nombre de periodo
        nombre_periodo: Nombre del periodo actual ("Low Season", etc.)
        precio_str: Precio heredado entre filas (leyenda agreement)
        habitaciones_sin_periodos: Buffer de habitaciones pendientes de asignación
        ws: Worksheet de openpyxl para acceder a celdas fusionadas
    """

    # Estado principal
    hoteles: List[HotelExcel] = field(default_factory=list)
    hotel_actual: Optional[HotelExcel] = None
    tipo_actual: Optional[TipoHabitacionExcel] = None

    # Estado de periodos
    nombre_periodo: Optional[str] = None
    hubo_nombre_periodo: bool = False

    # Herencia de precios entre filas
    precio_str: Optional[str] = None

    # Buffer temporal
    habitaciones_sin_periodos: List[HabitacionExcel] = field(default_factory=list)

    # Worksheet para acceso a celdas merged
    ws: Optional[Worksheet] = None

    def procesar_fila(self, row, i: int) -> None:
        """Procesa una fila del Excel aplicando los procesadores en orden.

        Args:
            row: Tupla con valores de la fila
            i: Índice de fila (0-based)

        Flujo de procesamiento:
        1. Fila vacía → asignar periodos y limpiar buffer
        2. Periodo → intentar extraer periodo
        3. Sin nombre (columna A vacía) → saltar
        4. Exclusiones → saltar
        5. Hotel → crear hotel y saltar
        6. Tipo habitación → crear tipo y saltar
        7. Precio → extraer y validar precio
        8. Habitación → crear habitación
        9. Extra → crear extra
        """
        # Constantes (importadas del módulo extractor)
        EXCLUSIONES = [
            "season rates", "(per room)", "closing agreement",
            "rates includes", "promotion", "not included", "high speed", "minimum stay",
            "other benefits"
        ]

        # 1. Fila vacía
        if not any(row):
            self._procesar_fila_vacia()
            return

        # 2. Periodo
        periodo_raw = row[1]
        if self._procesar_periodo(periodo_raw, i):
            return  

        # 3. Sin nombre
        if row[0] is None:
            return

        nombre_raw = str(row[0]).strip()
        nombre_norm = nombre_raw.lower()

        # 4. Exclusiones
        if any(nombre_norm.startswith(excl) for excl in EXCLUSIONES):
            return

        # 5. Hotel
        if self._procesar_hotel(nombre_raw):
            return

        # 6. Tipo habitación
        if self._procesar_tipo_habitacion(nombre_raw, row):
            return

        # 7. Precio
        precio, debe_omitir = self._procesar_precio(row, i)
        if debe_omitir:
            return

        # 8. Habitación
        if self._procesar_habitacion(nombre_raw, nombre_norm, precio, row, i):
            return

        # 9. Extra
        self._procesar_extra(nombre_raw, precio)

    def _procesar_fila_vacia(self) -> None:
        """Procesa una fila vacía asignando periodos y limpiando el buffer.

        Casos especiales:
        - Asigna último grupo de periodos a habitaciones pendientes
        - Agrega habitaciones al tipo actual o directamente al hotel
        - Limpia el buffer habitaciones_sin_periodos

        Ejemplo:
            Hotel con periodos_group = [
                PeriodoGroup("Low", [Periodo(id=1), Periodo(id=2)]),
                PeriodoGroup("High", [Periodo(id=3), Periodo(id=4)])
            ]
            Buffer: [Hab1, Hab2, Hab3]
            → Fila vacía asigna SOLO periodos del último grupo: {3, 4}
        """
        # Asignar periodos a las habitaciones SIN periodos
        if self.hotel_actual and self.hotel_actual.periodos_group:
            # Siempre asignar el último grupo de periodos disponible
            ultimo_grupo = self.hotel_actual.periodos_group[-1]
            for habitacion in self.habitaciones_sin_periodos:
                for periodo in ultimo_grupo.periodos:
                    habitacion.periodo_ids.add(periodo.id)

        # Agregar habitaciones al tipo o directamente al hotel
        if self.hotel_actual:
            if self.tipo_actual:
                self.tipo_actual.habitaciones.extend(self.habitaciones_sin_periodos)
            else:
                self.hotel_actual.habitaciones_directas.extend(self.habitaciones_sin_periodos)

        # Limpiar buffer
        self.habitaciones_sin_periodos = []

        self.hubo_nombre_periodo = False

    def _procesar_periodo(self, periodo_raw, i) -> bool:
        """Procesa una celda que podría contener información de periodo.

        Args:
            periodo_raw: Valor de la celda B (row[1])
            i: Índice de fila actual

        Returns:
            True si se procesó un periodo (saltar resto de fila)
            False si no es un periodo (continuar procesando fila)

        Casos especiales:
        - Detecta nombres de periodos ("season", "special dates")
        - Extrae fechas con paréntesis: (1May25 - 30Sep25)
        - Extrae fechas sin paréntesis: New Year: 26Dec25 - 3Jan26
        - Maneja proximidad de periodos (fila_nombre_seasson ≤3 filas)

        Ejemplo:
            Fila 10: "Low Season" → nombre_periodo = "Low Season", fila = 10
            Fila 12: "(1May25 - 30Sep25)" → i=12, 12-10=2 ≤ 3
                     → Agregar a grupo "Low Season"
        """
        from ExtractorDatos.utils import parece_periodo
        from ExtractorDatos.extractor import detectar_y_agregar_periodo

        if periodo_raw is None or not parece_periodo(periodo_raw):
            return False

        continuar, nuevo_nombre = detectar_y_agregar_periodo(
            self.hotel_actual,
            periodo_raw,
            self.hubo_nombre_periodo,
            i
        )

        # Actualizar estado de periodo si se detectó nombre
        if nuevo_nombre is not None:
            self.hubo_nombre_periodo = True

        return continuar

    def _procesar_hotel(self, nombre_raw: str) -> bool:
        """Detecta y crea un nuevo hotel.

        Args:
            nombre_raw: Valor crudo de la celda A (row[0])

        Returns:
            True si se procesó un hotel (saltar resto de fila)
            False si no es un hotel (continuar procesando)

        Casos especiales:
        - Detecta hoteles por sufijo "(A)"
        - Resetea variables de periodo para el nuevo hotel
        - Resetea tipo_actual a None

        Ejemplo:
            "Hotel Paradise (A)" → Crea HotelExcel, resetea contexto
        """
        if not nombre_raw.endswith("(A)"):
            return False

        # Resetear contexto de periodos
        self.fila_nombre_seasson = -1
        self.nombre_periodo = None

        # Crear nuevo hotel
        self.hotel_actual = HotelExcel(
            nombre=nombre_raw,
            tipos=[],
            habitaciones_directas=[],
            periodos=[]
        )
        self.hoteles.append(self.hotel_actual)
        self.tipo_actual = None

        return True

    def _procesar_tipo_habitacion(self, nombre_raw: str, row) -> bool:
        """Detecta y crea un tipo de habitación (edificio).

        Args:
            nombre_raw: Valor crudo de la celda A
            row: Fila completa del Excel

        Returns:
            True si se procesó un tipo (saltar resto de fila)
            False si no es un tipo (continuar procesando)

        Casos especiales:
        - Detecta por: nombre en MAYÚSCULAS Y sin precio en columna C
        - Limpia caracteres ":" del nombre

        Ejemplo:
            "SUITE:" (en mayúsculas) + col C vacía → TipoHabitacionExcel("SUITE")
        """
        if not (nombre_raw.isupper() and row[2] is None):
            return False

        nombre_limpio = nombre_raw.replace(":", "").strip()
        self.tipo_actual = TipoHabitacionExcel(
            nombre=nombre_limpio,
            habitaciones=[]
        )

        if self.hotel_actual:
            self.hotel_actual.tipos.append(self.tipo_actual)

        return True

    def _procesar_precio(self, row, i: int) -> tuple[Optional[str], bool]:
        """Extrae y valida el precio de una fila.

        Args:
            row: Fila completa del Excel
            i: Índice de fila (para obtener_valor_real)

        Returns:
            tuple: (precio: str | None, debe_omitir: bool)
            - precio: Precio validado o None
            - debe_omitir: True si la fila debe omitirse (leyenda no permitida)

        Casos especiales:
        - Columna C vacía → intenta columna D (precio BAR)
        - Leyendas permitidas: solo LEYENDAS_AGREEMENT
        - Herencia de precio: si precio_str existe y fila actual vacía
        - Omite filas con texto no numérico no permitido

        Ejemplo de herencia:
            Fila 10: precio "closing agreement" → precio_str = "closing agreement"
            Fila 11: precio vacío → hereda "closing agreement"
            Fila 12: precio "100.5" → precio_str = None (resetear herencia)
            Fila 13: precio vacío → NO hereda (precio_str es None)
        """
        from ExtractorDatos.utils import obtener_valor_real

        # Constantes (importadas del módulo extractor)
        LEYENDAS_AGREEMENT = ["closing agreement"]

        # Obtener valor de columna C (considerando celdas fusionadas)
        col_precio = obtener_valor_real(self.ws, i, 2)  # columna 2 = índice C
        valor_str = str(col_precio).strip().lower() if col_precio is not None else ""

        # Clasificar tipo de precio
        es_leyenda_agreement = valor_str in LEYENDAS_AGREEMENT
        es_numerico = valor_str.replace(".", "").replace(",", "").isdigit()
        es_texto_no_leyenda = valor_str and not es_numerico and not es_leyenda_agreement

        # Omitir leyendas no permitidas
        if es_texto_no_leyenda:
            return (None, True)  # Debe omitir la fila

        # Procesar precio
        precio = None
        if es_leyenda_agreement:
            self.precio_str = valor_str
            precio = valor_str
        elif es_numerico:
            self.precio_str = None  # Resetear herencia
            precio = valor_str
        elif self.precio_str:
            precio = self.precio_str  # Heredar precio anterior

        return (precio, False)

    def _procesar_habitacion(
        self,
        nombre_raw: str,
        nombre_norm: str,
        precio: Optional[str],
        row,
        i: int
    ) -> bool:
        """Detecta y crea una habitación.

        Args:
            nombre_raw: Nombre original (sin procesar)
            nombre_norm: Nombre normalizado (lowercase)
            precio: Precio ya procesado
            row: Fila completa
            i: Índice de fila

        Returns:
            True si se procesó una habitación
            False si no es una habitación

        Casos especiales:
        - Detecta por prefijo: dbl, sgl, tpl
        - Fallback a columna D (precio BAR) si columna C vacía
        - Omite si no tiene precio después del fallback
        - Agrega a buffer (periodo asignado en fila vacía)

        Ejemplo:
            "DBL STANDARD" → nombre_norm="dbl standard" → HabitacionExcel
        """
        es_habitacion = nombre_norm.startswith(("dbl", "sgl", "tpl"))

        if not es_habitacion:
            return False

        # Intentar precio BAR si no hay precio
        precio_final = precio
        if not precio_final and row[3] is not None:
            precio_final = str(row[3]).strip()

        # Omitir si sigue sin precio
        if not precio_final:
            return True  # Es habitación pero se omite

        habitacion = HabitacionExcel(
            nombre=nombre_raw,
            precio=precio_final,
            row_idx=i,
            periodo_ids=[]  # Se asignan en fila vacía
        )

        # Agregar a buffer (periodos se asignan en fila vacía)
        self.habitaciones_sin_periodos.append(habitacion)

        return True

    def _procesar_extra(self, nombre_raw: str, precio: Optional[str]) -> bool:
        """Detecta y crea un extra (no es habitación, tiene precio).

        Args:
            nombre_raw: Nombre original
            precio: Precio ya procesado

        Returns:
            True si se procesó un extra
            False si no tiene precio (omitir)

        Casos especiales:
        - Solo se crea si tiene precio
        - Se agrega directamente al hotel_actual

        Ejemplo:
            "BREAKFAST" con precio → Extra
            "WiFi Premium" con precio → Extra
        """
        if not precio:
            return False

        extra = Extra(nombre=nombre_raw, precio=precio)

        if self.hotel_actual:
            self.hotel_actual.extras.append(extra)

        return True
