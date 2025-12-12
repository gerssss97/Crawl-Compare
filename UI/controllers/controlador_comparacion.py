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
        """Ejecuta comparación asíncrona (método privado)."""
        try:
            # Emitir evento de inicio
            self.event_bus.emit('comparison_started')

            # Validar todo primero
            if not self.controlador_validacion.validar_todo():
                self.event_bus.emit('comparison_error', "Validación fallida")
                return

            # Obtener datos del estado
            fecha_entrada = self.estado_app.fecha_entrada_completa.get()
            fecha_salida = self.estado_app.fecha_salida_completa.get()
            adultos = self.estado_app.adultos.get()
            ninos = self.estado_app.ninos.get()
            habitacion_excel = self.estado_app.habitacion.get()
            precio = self.estado_app.precio.get()

            # Construir mensaje inicial
            mensaje_inicial = "Ejecutando scraping con:\n"
            mensaje_inicial += f"  - Fecha de entrada: {fecha_entrada}\n"
            mensaje_inicial += f"  - Fecha de salida: {fecha_salida}\n"
            mensaje_inicial += f"  - Número de adultos: {adultos}\n"
            mensaje_inicial += f"  - Número de niños: {ninos}\n"
            mensaje_inicial += f"  - Habitación Excel: {habitacion_excel}\n"
            mensaje_inicial += f"  - Precio: {precio}\n"

            # Obtener datos web
            hotel_web = await dar_hotel_web(fecha_entrada, fecha_salida, adultos, ninos)

            if not hotel_web or not hotel_web.habitacion:
                error_msg = "Error: No se pudieron obtener datos del hotel web\n"
                self.event_bus.emit('comparison_error', error_msg)
                return

            # Comparar habitaciones
            precio_normalizado = normalizar_precio_str(precio)
            coincide = await comparar_habitaciones(habitacion_excel, precio_normalizado)

            # Obtener resultados
            habitacion_web = dar_habitacion_web()
            mensaje_match = dar_mensaje()

            # Guardar habitación web en estado
            self.estado_app.habitacion_web = habitacion_web

            # Construir mensaje de resultado
            texto_habitacion = imprimir_habitacion_web(habitacion_web)
            mensaje_resultado = mensaje_inicial
            mensaje_resultado += f"\nHabitación web de mayor coincidencia:\n{texto_habitacion}\n"

            if mensaje_match:
                mensaje_resultado += f"{mensaje_match}\n"

            if coincide:
                mensaje_resultado += "Se encontró diferencia de precio.\n"
                resultado_data = {
                    'mensaje': mensaje_resultado,
                    'coincide': True,
                    'habitacion_web': habitacion_web
                }
            else:
                mensaje_resultado += "Las habitaciones coinciden en precio y nombre.\n"
                resultado_data = {
                    'mensaje': mensaje_resultado,
                    'coincide': False,
                    'habitacion_web': habitacion_web
                }

            # Emitir evento de éxito
            self.event_bus.emit('comparison_completed', resultado_data)

        except ValueError as ve:
            error_msg = f"Error de validación: {str(ve)}\n"
            self.event_bus.emit('comparison_error', error_msg)

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}\n"
            self.event_bus.emit('comparison_error', error_msg)
