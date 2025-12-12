"""Event bus for pub/sub communication between components."""


class EventBus:
    """Sistema de eventos pub/sub para comunicación entre componentes desacoplados.

    Permite que diferentes partes de la aplicación se comuniquen sin conocerse directamente,
    mejorando la modularidad y facilitando el testing.

    Ejemplo de uso:
        event_bus = EventBus()
        event_bus.on('hotel_changed', lambda data: print(f"Hotel: {data}"))
        event_bus.emit('hotel_changed', 'Hotel ABC')
    """

    def __init__(self):
        """Inicializa el EventBus con un diccionario vacío de listeners."""
        self._listeners = {}
        self._debug = False

    def on(self, event_name, callback):
        """Suscribe un callback a un evento específico.

        Args:
            event_name (str): Nombre del evento a escuchar
            callback (callable): Función a ejecutar cuando se emita el evento
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def off(self, event_name, callback):
        """Desuscribe un callback de un evento específico.

        Args:
            event_name (str): Nombre del evento
            callback (callable): Función a desuscribir
        """
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass  # Callback no estaba suscrito

    def emit(self, event_name, data=None):
        """Emite un evento con datos opcionales a todos los listeners suscritos.

        Args:
            event_name (str): Nombre del evento a emitir
            data: Datos opcionales a pasar a los listeners
        """
        if self._debug:
            print(f"[EventBus] Emitiendo: {event_name} con data: {data}")

        for callback in self._listeners.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                print(f"[EventBus] Error en listener de {event_name}: {e}")

    def enable_debug(self):
        """Activa el modo debug para mostrar mensajes de eventos emitidos."""
        self._debug = True

    def disable_debug(self):
        """Desactiva el modo debug."""
        self._debug = False

    def clear(self, event_name=None):
        """Limpia listeners de un evento específico o todos los eventos.

        Args:
            event_name (str, optional): Nombre del evento a limpiar.
                                       Si es None, limpia todos los eventos.
        """
        if event_name:
            self._listeners[event_name] = []
        else:
            self._listeners = {}
