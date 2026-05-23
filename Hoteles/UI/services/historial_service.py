MAX_ENTRADAS = 50


class HistorialService:
    def __init__(self, config_service):
        self._config = config_service

    def agregar(self, entrada: dict) -> None:
        historial = self._config.get_historial()
        historial.insert(0, entrada)
        if len(historial) > MAX_ENTRADAS:
            historial = historial[:MAX_ENTRADAS]
        self._config.set_historial(historial)

    def obtener_todos(self) -> list:
        return self._config.get_historial()

    def limpiar_todo(self) -> None:
        self._config.set_historial([])
