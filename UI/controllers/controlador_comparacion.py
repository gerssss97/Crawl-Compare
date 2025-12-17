"""Controlador de comparación de habitaciones."""

import asyncio
import threading
import tkinter as tk
from Core.controller import (
    dar_hotel_web,
    comparar_habitaciones,
    dar_habitacion_web,
    dar_mensaje,
    normalizar_precio_str,
    imprimir_habitacion_web
)


class ControladorComparacion:
    """Controlador de comparación de habitaciones.

    Maneja la ejecución asíncrona de la comparación entre
    habitación Excel y habitación web.

    Emite eventos:
    - comparison_started: Al iniciar comparación
    - comparison_completed: Al completar comparación exitosamente
    - comparison_error: Si ocurre un error

    Ejemplo de uso:
        controlador = ControladorComparacion(
            estado_app,
            event_bus,
            controlador_validacion
        )
        controlador.ejecutar_comparacion_async()
    """

    def __init__(self, estado_app, event_bus, controlador_validacion):
        """Inicializa el controlador de comparación.

        Args:
            estado_app (AppState): Estado centralizado
            event_bus (EventBus): Sistema de eventos
            controlador_validacion (ControladorValidacion): Controlador de validación
        """
        self.estado_app = estado_app
        self.event_bus = event_bus
        self.controlador_validacion = controlador_validacion

    def ejecutar_comparacion_async(self):
        """Ejecuta comparación en background thread."""
        threading.Thread(target=self._run_async, daemon=True).start()

    def _run_async(self):
        """Wrapper para ejecutar corrutina async."""
        asyncio.run(self._ejecutar_comparacion())

    async def _ejecutar_comparacion(self):
        """Ejecuta comparación multi-periodo asíncrona."""
        try:
            self.event_bus.emit('comparison_started')

            # Validar
            if not self.controlador_validacion.validar_todo():
                self.event_bus.emit('comparison_error', "Validación fallida")
                return

            # Obtener datos del estado
            fecha_entrada_str = self.estado_app.fecha_entrada_completa.get()
            fecha_salida_str = self.estado_app.fecha_salida_completa.get()
            adultos = self.estado_app.adultos.get()
            ninos = self.estado_app.ninos.get()
            habitacion_nombre = self.estado_app.habitacion.get()

            # Parsear fechas
            from datetime import datetime
            fecha_entrada = datetime.strptime(fecha_entrada_str, "%d-%m-%Y").date()
            fecha_salida = datetime.strptime(fecha_salida_str, "%d-%m-%Y").date()

            # Obtener hotel actual
            hotel_nombre = self.estado_app.hotel.get().lower() + " (a)"
            hotel_actual = None
            for hotel in self.estado_app.hoteles_excel:
                if hotel.nombre.lower() == hotel_nombre:
                    hotel_actual = hotel
                    break

            if not hotel_actual:
                self.event_bus.emit('comparison_error', "No se encontró el hotel seleccionado")
                return

            # Buscar habitación unificada
            habitacion_unificada = None
            for hab_unif in self.estado_app.habitaciones_unificadas:
                if hab_unif.nombre.lower() == habitacion_nombre.lower():
                    habitacion_unificada = hab_unif
                    break

            if not habitacion_unificada:
                self.event_bus.emit('comparison_error', f"No se encontró habitación '{habitacion_nombre}'")
                return

            # Ejecutar comparación multi-periodo
            from Core.comparador_multiperiodo import comparar_multiperiodo

            resultado = await comparar_multiperiodo(
                habitacion_unificada=habitacion_unificada,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                adultos=adultos,
                ninos=ninos,
                hotel=hotel_actual
            )

            # Emitir evento de éxito
            self.event_bus.emit('comparison_completed', resultado)

        except ValueError as ve:
            error_msg = f"Error de validación: {str(ve)}\n"
            self.event_bus.emit('comparison_error', error_msg)

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}\n"
            import traceback
            traceback.print_exc()
            self.event_bus.emit('comparison_error', error_msg)
