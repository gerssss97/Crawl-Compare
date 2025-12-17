"""Controlador para gestión dinámica de precios basados en fechas y periodos."""

from datetime import datetime
from typing import Optional
from Models.habitacion_unificada import HabitacionUnificada
from Core.servicio_habitaciones import inferir_periodos_desde_fechas


class ControladorPrecios:
    """Gestiona visualización dinámica de precios basada en fechas.

    Este controlador se encarga de:
    - Escuchar cambios en la habitación seleccionada
    - Escuchar cambios en las fechas de entrada/salida
    - Inferir qué periodos aplican según las fechas
    - Calcular y emitir los precios correspondientes

    Flujo:
    1. Usuario selecciona habitación -> NO muestra precio aún
    2. Usuario ingresa fechas -> Infiere periodos -> Muestra precios
    3. Usuario cambia fechas -> Recalcula periodos -> Actualiza precios
    """

    def __init__(self, estado_app, event_bus):
        """Inicializa el controlador de precios.

        Args:
            estado_app: AppState con variables de estado de la aplicación
            event_bus: EventBus para comunicación entre componentes
        """
        self.estado_app = estado_app
        self.event_bus = event_bus
        self.habitacion_actual: Optional[HabitacionUnificada] = None

        # Suscribirse a cambios de fechas
        self.estado_app.fecha_entrada_completa.trace_add(
            'write',
            lambda *args: self._on_fechas_changed()
        )
        self.estado_app.fecha_salida_completa.trace_add(
            'write',
            lambda *args: self._on_fechas_changed()
        )

        # Suscribirse a cambio de habitación
        self.event_bus.on('habitacion_unificada_changed', self._on_habitacion_changed)

    def _on_habitacion_changed(self, habitacion_unificada: HabitacionUnificada):
        """Handler cuando cambia la habitación seleccionada.

        Args:
            habitacion_unificada: Nueva habitación seleccionada
        """
        self.habitacion_actual = habitacion_unificada

        # Si ya hay fechas válidas, calcular precios inmediatamente
        if self._fechas_son_validas():
            self._calcular_y_mostrar_precios()
        else:
            # Mostrar mensaje "Ingrese fechas" y resetear precio
            self.estado_app.precio.set("(ninguna seleccionada)")
            self.event_bus.emit('precios_actualizados', {
                'tipo': 'sin_fechas',
                'mensaje': '(Ingrese fechas para ver precios)'
            })

    def _on_fechas_changed(self):
        """Handler cuando cambian las fechas de entrada o salida."""
        # Recalcular precios si hay habitación seleccionada y fechas válidas
        if self.habitacion_actual and self._fechas_son_validas():
            self._calcular_y_mostrar_precios()

    def _fechas_son_validas(self) -> bool:
        """Verifica si las fechas están completas y son válidas.

        Returns:
            True si ambas fechas están completas y tienen formato válido DD-MM-AAAA
        """
        fecha_entrada_str = self.estado_app.fecha_entrada_completa.get()
        fecha_salida_str = self.estado_app.fecha_salida_completa.get()

        # Verificar que ambas fechas existan
        if not fecha_entrada_str or not fecha_salida_str:
            return False

        # Verificar formato válido
        try:
            datetime.strptime(fecha_entrada_str, "%d-%m-%Y")
            datetime.strptime(fecha_salida_str, "%d-%m-%Y")
            return True
        except ValueError:
            return False

    def _calcular_y_mostrar_precios(self):
        """Calcula precios para los periodos inferidos y emite evento con los resultados."""
        fecha_entrada_str = self.estado_app.fecha_entrada_completa.get()
        fecha_salida_str = self.estado_app.fecha_salida_completa.get()

        # Parsear fechas
        fecha_entrada = datetime.strptime(fecha_entrada_str, "%d-%m-%Y").date()
        fecha_salida = datetime.strptime(fecha_salida_str, "%d-%m-%Y").date()

        # Obtener hotel actual (agregar sufijo "(A)" para búsqueda)
        hotel_nombre = self.estado_app.hotel.get().lower() + " (a)"
        hotel_actual = None
        for hotel in self.estado_app.hoteles_excel:
            if hotel.nombre.lower() == hotel_nombre:
                hotel_actual = hotel
                break

        if not hotel_actual:
            return

        # Inferir periodos aplicables para el rango de fechas
        periodos_aplicables = inferir_periodos_desde_fechas(
            fecha_entrada,
            fecha_salida,
            hotel_actual
        )

        # Si no hay periodos aplicables, mostrar advertencia y resetear precio
        if not periodos_aplicables:
            self.estado_app.precio.set("(ninguna seleccionada)")
            self.event_bus.emit('precios_actualizados', {
                'tipo': 'sin_periodos',
                'mensaje': 'No hay periodos definidos para estas fechas'
            })
            return

        # Obtener precios para cada periodo
        precios_data = []
        for periodo in periodos_aplicables:
            precio = self.habitacion_actual.precio_para_periodo(periodo.id)

            # Buscar nombre del grupo al que pertenece el periodo
            nombre_grupo = None
            for grupo in hotel_actual.periodos_group:
                if periodo in grupo.periodos:
                    nombre_grupo = grupo.nombre
                    break

            precios_data.append({
                'periodo': periodo,
                'precio': precio,
                'nombre_grupo': nombre_grupo
            })

        # Actualizar AppState.precio para validación
        if precios_data:
            if len(precios_data) == 1:
                # Un solo periodo - mostrar precio exacto
                precio = precios_data[0]['precio']
                if isinstance(precio, (int, float)):
                    self.estado_app.precio.set(f"${precio:.2f}")
                else:
                    self.estado_app.precio.set(str(precio))
            else:
                # Múltiples periodos - mostrar rango
                precios_num = [p['precio'] for p in precios_data if isinstance(p['precio'], (int, float))]
                if precios_num:
                    min_precio = min(precios_num)
                    max_precio = max(precios_num)
                    if min_precio == max_precio:
                        self.estado_app.precio.set(f"${min_precio:.2f}")
                    else:
                        self.estado_app.precio.set(f"${min_precio:.2f} - ${max_precio:.2f}")
                else:
                    # Todos son leyendas
                    self.estado_app.precio.set(precios_data[0]['precio'])

        # Emitir evento con los precios calculados
        self.event_bus.emit('precios_actualizados', {
            'tipo': 'precios_calculados',
            'precios': precios_data
        })
