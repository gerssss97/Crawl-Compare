import datetime

_MAX_ENTRADAS = 100


class HistorialService:
    def __init__(self, config_service):
        self._config = config_service

    def agregar(self, entrada: dict) -> None:
        historial = self._config.get_historial()
        historial.insert(0, entrada)
        self._config.set_historial(self._purgar(historial))

    def obtener_todos(self) -> list:
        return self._purgar(self._config.get_historial())

    def limpiar_todo(self) -> None:
        self._config.set_historial([])

    def _purgar(self, historial: list) -> list:
        ttl_dias = self._config.get_historial_ttl_dias()
        limite = datetime.datetime.now() - datetime.timedelta(days=ttl_dias)
        resultado = []
        for entrada in historial:
            try:
                ts = datetime.datetime.fromisoformat(entrada.get("timestamp", ""))
                if ts >= limite:
                    resultado.append(entrada)
            except (ValueError, TypeError):
                resultado.append(entrada)  # sin timestamp válido: conservar
        return resultado[:_MAX_ENTRADAS]
