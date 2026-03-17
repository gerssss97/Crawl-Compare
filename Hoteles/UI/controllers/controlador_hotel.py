"""Controlador de lógica de hoteles, edificios y habitaciones."""

from Core.controller import dar_hoteles_excel
from Core.servicio_habitaciones import unificar_habitaciones


class ControladorHotel:
    """Controlador de lógica de hoteles.

    Maneja la carga de hoteles, edificios y habitaciones desde Excel,
    incluyendo la lógica de agrupación por periodos.

    Ejemplo de uso:
        controlador = ControladorHotel(estado_app, event_bus)
        hoteles = controlador.cargar_hoteles()
        controlador.on_hotel_changed('Alvear Palace')
    """

    def __init__(self, estado_app, event_bus):
        """Inicializa el controlador de hoteles.

        Args:
            estado_app (AppState): Estado centralizado de la aplicación
            event_bus (EventBus): Sistema de eventos
        """
        self.estado_app = estado_app
        self.event_bus = event_bus

        # Suscribirse a eventos
        self.event_bus.on('hotel_changed', self.on_hotel_changed)
        self.event_bus.on('edificio_changed', self.on_edificio_changed)

    def cargar_hoteles(self):
        """Carga hoteles desde Excel.

        Returns:
            list: Lista de nombres de hoteles (sin sufijo '(A)')
        """
        self.estado_app.hoteles_excel = dar_hoteles_excel()
        hoteles = [h.nombre for h in self.estado_app.hoteles_excel]

        # Limpiar sufijo (A)
        hoteles = [h.replace("(A)", "").replace("(a)", "").strip() for h in hoteles]

        return hoteles

    def cargar_edificios(self, hotel_nombre):
        """Carga edificios de un hotel.

        Args:
            hotel_nombre (str): Nombre del hotel

        Returns:
            list: Lista de nombres de edificios SIN grupo de periodo
        """
        hotel = hotel_nombre.lower() + " (a)"

        for hotel_excel in self.estado_app.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                # Usar un set para evitar duplicados (mismo edificio en múltiples periodos)
                edificios_set = set()
                for tipo in hotel_excel.tipos:
                    edificios_set.add(tipo.nombre)

                # Convertir a lista ordenada
                edificios = sorted(list(edificios_set))
                return edificios

        return []

    def cargar_habitaciones(self, hotel_nombre, edificio_nombre=None):
        """Carga habitaciones de un hotel/edificio y las UNIFICA.

        Args:
            hotel_nombre (str): Nombre del hotel
            edificio_nombre (str, optional): Nombre del edificio

        Returns:
            list: Lista de nombres únicos de habitaciones (sin duplicados)
        """
        hotel = hotel_nombre.lower() + " (a)"
        hotel_excel = None

        for h in self.estado_app.hoteles_excel:
            if h.nombre.lower() == hotel:
                hotel_excel = h
                break

        if not hotel_excel:
            return []

        # Sin edificio: habitaciones directas
        if edificio_nombre is None:
            habitaciones = hotel_excel.habitaciones_directas
        else:
            # Con edificio: buscar TODOS los tipos con ese nombre
            # (un mismo edificio puede tener múltiples entradas con distintos periodos)
            nombre_tipo_base = edificio_nombre.split(' - ')[0] if ' - ' in edificio_nombre else edificio_nombre

            habitaciones = []
            for tipo in hotel_excel.tipos:
                if tipo.nombre == nombre_tipo_base:
                    # Agregar todas las habitaciones de este tipo (no hacer break)
                    habitaciones.extend(tipo.habitaciones)

        # NUEVO: Unificar habitaciones (agrupa por nombre)
        habitaciones_unificadas = unificar_habitaciones(habitaciones)

        # Guardar en estado
        self.estado_app.habitaciones_unificadas = habitaciones_unificadas
        self.estado_app.habitaciones_excel = habitaciones  # Mantener compatibilidad

        # Emitir evento
        self.event_bus.emit('habitaciones_cargadas',
                           [hab.nombre for hab in habitaciones_unificadas])

        # Retornar solo nombres únicos (sin sufijo de periodo)
        return [hab.nombre for hab in habitaciones_unificadas]

    def on_hotel_changed(self, hotel_nombre):
        """Callback cuando cambia el hotel.

        Args:
            hotel_nombre (str): Nombre del hotel seleccionado
        """
        if not hotel_nombre:
            return

        hotel = hotel_nombre.lower() + " (a)"

        for hotel_excel in self.estado_app.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                # Emitir evento con información del hotel
                tiene_tipos = bool(hotel_excel.tipos)
                self.event_bus.emit('hotel_cargado', {
                    'hotel': hotel_excel,
                    'tiene_tipos': tiene_tipos
                })
                break

    def on_edificio_changed(self, edificio_nombre):
        """Callback cuando cambia el edificio.

        Args:
            edificio_nombre (str): Nombre del edificio seleccionado
        """
        if not edificio_nombre:
            return

        hotel_nombre = self.estado_app.hotel.get()
        habitaciones = self.cargar_habitaciones(hotel_nombre, edificio_nombre)

        self.event_bus.emit('habitaciones_cargadas', habitaciones)

    def _obtener_grupo_periodo_edificio(self, hotel_excel, tipo):
        """Obtiene el nombre del grupo de periodo para un edificio.

        Args:
            hotel_excel: Objeto HotelExcel
            tipo: Objeto TipoHabitacionExcel

        Returns:
            str: Nombre del grupo de periodo o None
        """
        if not tipo.habitaciones:
            return None

        primera_habitacion = tipo.habitaciones[0]
        if not primera_habitacion.periodo_ids:
            return None

        primer_periodo_id = next(iter(primera_habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None

    def _obtener_grupo_periodo_habitacion(self, hotel_excel, habitacion):
        """Obtiene el nombre del grupo de periodo para una habitación.

        Args:
            hotel_excel: Objeto HotelExcel
            habitacion: Objeto HabitacionExcel

        Returns:
            str: Nombre del grupo de periodo o None
        """
        if not habitacion.periodo_ids:
            return None

        primer_periodo_id = next(iter(habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None
