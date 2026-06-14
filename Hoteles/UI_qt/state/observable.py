"""ObservableVar: reemplazo de tk.Variable con la misma API, respaldado por Signal de Qt.

Permite que AppState y los controladores funcionen SIN Tkinter. La API publica
(.get / .set / .trace_add) es identica a la de tk.StringVar/tk.IntVar, asi los
controladores existentes se reutilizan sin cambios.

Decision de diseno: emite en CADA .set(), aunque el valor no cambie, replicando
el comportamiento exacto de tk.Variable (que tambien re-emite siempre). No se pone
guard `if nuevo != viejo` para no alterar la semantica de la que pueda depender la
logica (ej. re-disparo de calculo de precios).
"""

from PySide6.QtCore import QObject, Signal


class ObservableVar(QObject):
    """Variable observable con API compatible con tk.Variable.

    Args:
        value: valor inicial.
    """

    changed = Signal(object)

    def __init__(self, value=None):
        super().__init__()
        self._value = self._coerce(value if value is not None else self._default())

    # --- hooks de subtipo (StringVar/IntVar los sobreescriben) ---
    def _default(self):
        return ""

    def _coerce(self, v):
        return v

    # --- API compatible con tk.Variable ---
    def get(self):
        """Devuelve el valor actual."""
        return self._value

    def set(self, value):
        """Asigna el valor y emite el cambio (siempre, como tk.Variable)."""
        self._value = self._coerce(value)
        self.changed.emit(self._value)

    def trace_add(self, mode, callback):
        """Registra un callback para cambios (firma compatible con tk.Variable).

        En Tkinter el callback recibe (name, index, mode); el codigo del proyecto
        siempre lo ignora con `*args`. Replicamos esa firma pasando placeholders.

        Args:
            mode: ignorado (en Tk seria 'write'/'read'/'unset'); aca solo 'write'.
            callback: invocable; se llama con (name, index, mode) estilo Tk.
        Returns:
            El nombre de la conexion (placeholder, por compatibilidad de firma).
        """
        self.changed.connect(lambda _value: callback("", "", "write"))
        return f"trace_{id(callback)}"


class StringVar(ObservableVar):
    """ObservableVar que coacciona a str (equivalente a tk.StringVar)."""

    def _default(self):
        return ""

    def _coerce(self, v):
        return "" if v is None else str(v)


class IntVar(ObservableVar):
    """ObservableVar que coacciona a int (equivalente a tk.IntVar)."""

    def _default(self):
        return 0

    def _coerce(self, v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0
