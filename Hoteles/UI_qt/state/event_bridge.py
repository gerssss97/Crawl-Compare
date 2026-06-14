"""Puente EventBus -> Qt Signals (thread-safe). Fase 6 del plan de migracion.

El scraping corre en un threading.Thread y emite eventos al EventBus DESDE ese hilo
(comparison_started/progress/scrape_step/completed/error). En Qt, tocar widgets desde
un hilo que no es el de la GUI crashea. Tkinter lo resolvia con self.after(0, ...).

Solucion Qt: este QObject se suscribe al EventBus y RE-EMITE cada evento como un
Signal de Qt. Cuando un signal cruza de un hilo a otro, Qt usa QueuedConnection
automaticamente: el slot se ejecuta en el hilo donde vive el QObject (el de la GUI,
porque se crea ahi). Asi los modales pueden conectar a estos signals con la garantia
de correr en el hilo de UI. El EventBus y los controladores quedan agnosticos a Qt.
"""

from PySide6.QtCore import QObject, Signal


class EventBridge(QObject):
    """Re-emite los eventos de comparacion del EventBus como Qt Signals."""

    started = Signal(dict)
    progress = Signal(dict)
    scrape_step = Signal(dict)
    completed = Signal(dict)
    error = Signal(dict)
    validation_failed = Signal(dict)
    mostrar_modal_gaps = Signal(dict)
    precios_actualizados = Signal(dict)
    habitacion_unificada_changed = Signal(object)  # HabitacionUnificada

    # Mapa evento del EventBus -> nombre del signal
    _MAP = {
        "comparison_started": "started",
        "comparison_progress": "progress",
        "scrape_step": "scrape_step",
        "comparison_completed": "completed",
        "comparison_error": "error",
        "validation_failed": "validation_failed",
        "mostrar_modal_gaps": "mostrar_modal_gaps",
        "precios_actualizados": "precios_actualizados",
        "habitacion_unificada_changed": "habitacion_unificada_changed",
    }

    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self._event_bus = event_bus
        # Suscribir un re-emisor por cada evento mapeado
        for evento, signal_name in self._MAP.items():
            sig = getattr(self, signal_name)
            event_bus.on(evento, self._make_reemit(sig))

    @staticmethod
    def _make_reemit(signal):
        def _reemit(data):
            # data puede no ser dict (algunos eventos mandan otra cosa); normalizamos
            payload = data if isinstance(data, dict) else {"value": data}
            signal.emit(payload)
        return _reemit
