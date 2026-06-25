"""Controlador de comparación de habitaciones."""

import asyncio
import threading
from Core.controller import (
    dar_hotel_web,
    comparar_habitaciones,
    dar_habitacion_web,
    dar_mensaje,
    normalizar_precio_str,
    imprimir_habitacion_web
)
from UI.utils import normalizar_hotel_nombre


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

    def ejecutar_comparacion_async(self, comparison_id: str):
        """Ejecuta comparación en background thread.

        Args:
            comparison_id: Identificador único de esta comparación (timestamp ISO).
        """
        threading.Thread(
            target=self._run_async,
            args=(comparison_id,),
            daemon=True,
        ).start()

    def _run_async(self, comparison_id: str):
        """Wrapper para ejecutar corrutina async."""
        asyncio.run(self._ejecutar_comparacion(comparison_id))

    async def _ejecutar_comparacion(self, comparison_id: str):
        """Ejecuta comparación multi-periodo asíncrona."""
        try:
            # Validar PRIMERO — antes de tocar la UI con comparison_started.
            # El orquestador decide CÓMO mostrar los errores: emite un evento
            # para que el handler en el main thread muestre el messagebox.
            result = self.controlador_validacion.validar_todo()
            if not result.is_valid:
                self.event_bus.emit('validation_failed', {
                    'mensajes': result.mensajes_concatenados(),
                    'errors': result.errors,
                })
                return

            # Verificar si hay gaps no confirmados
            gap_analysis = getattr(self.estado_app, 'gap_analysis_actual', None)
            gap_confirmado = getattr(self.estado_app, 'gap_confirmado', False)

            if gap_analysis and gap_analysis.tiene_gaps and not gap_confirmado:
                self.event_bus.emit('mostrar_modal_gaps', {'gap_analysis': gap_analysis})
                return
            
            self.event_bus.emit('comparison_started', {'comparison_id': comparison_id})

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
            hotel_nombre = normalizar_hotel_nombre(self.estado_app.hotel.get())
            hotel_actual = None
            for hotel in self.estado_app.hoteles_excel:
                if hotel.nombre.lower() == hotel_nombre:
                    hotel_actual = hotel
                    break

            if not hotel_actual:
                self.event_bus.emit('comparison_error', {
                    'comparison_id': comparison_id,
                    'error': "No se encontró el hotel seleccionado",
                })
                return

            # Buscar habitación unificada
            habitacion_unificada = None
            for hab_unif in self.estado_app.habitaciones_unificadas:
                if hab_unif.nombre.lower() == habitacion_nombre.lower():
                    habitacion_unificada = hab_unif
                    break

            if not habitacion_unificada:
                self.event_bus.emit('comparison_error', {
                    'comparison_id': comparison_id,
                    'error': f"No se encontró habitación '{habitacion_nombre}'",
                })
                return

            # Ejecutar comparación multi-periodo
            from Core.comparador_multiperiodo import comparar_multiperiodo

            def _on_progress(periodo_actual, total, estado):
                self.event_bus.emit('comparison_progress', {
                    'comparison_id': comparison_id,
                    'periodo_actual': periodo_actual,
                    'total': total,
                    'estado': estado,
                })

            def _on_scrape_step(step):
                self.event_bus.emit('scrape_step', {
                    'comparison_id': comparison_id,
                    'step': step,
                })

            resultado = await comparar_multiperiodo(
                habitacion_unificada=habitacion_unificada,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                adultos=adultos,
                ninos=ninos,
                hotel=hotel_actual,
                on_progress=_on_progress,
                on_scrape_step=_on_scrape_step,
            )

            # Resetear estado de gap para la próxima comparación
            self.estado_app.gap_confirmado = False
            self.estado_app.gap_analysis_actual = None

            # Emitir evento de éxito
            self.event_bus.emit('comparison_completed', {
                'comparison_id': comparison_id,
                'resultado': resultado,
            })

        except ValueError as ve:
            error_msg = f"Error de validación: {str(ve)}\n"
            self.event_bus.emit('comparison_error', {
                'comparison_id': comparison_id,
                'error': error_msg,
            })

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}\n"
            import traceback
            traceback.print_exc()
            self.event_bus.emit('comparison_error', {
                'comparison_id': comparison_id,
                'error': error_msg,
            })

    def confirmar_gap(self) -> None:
        """El usuario aceptó continuar con cobertura parcial."""
        self.estado_app.gap_confirmado = True

    def resetear_gap(self) -> None:
        """Resetea la confirmación de gap (al recalcular fechas o al completar)."""
        self.estado_app.gap_confirmado = False

    def enviar_email(self, resultado, snapshot: dict) -> str | None:
        """Genera el cuerpo del email y lo despacha con el sender configurado.

        Retorna un mensaje para mostrar al usuario si el envío requiere acción
        manual (ej. clipboard), o None si el sender abrió una app por su cuenta.
        """
        from Core.controller import generar_texto_email_multiperiodo
        from Core.services.config_service import ConfigService
        from Core.services.email_senders import ClipboardSender, get_sender
        config = ConfigService()
        hotel = snapshot.get("hotel", "")
        cuerpo = generar_texto_email_multiperiodo(
            hotel, resultado,
            template=config.get_email_template(),
            firma=config.get_email_firma(),
        )
        sender = get_sender(config.get_email_provider())
        sender.enviar(
            destinatario="",
            asunto=f"Reporte de Discrepancias - {hotel}",
            cuerpo=cuerpo,
        )
        if isinstance(sender, ClipboardSender):
            if sender.copied:
                return "Email copiado al portapapeles.\nAbrí tu cliente de email y pegá con Ctrl+V."
            return "No se pudo copiar al portapapeles (pyperclip no disponible)."
        return None
