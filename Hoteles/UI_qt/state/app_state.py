"""Estado centralizado de la aplicacion (version PySide6, sin Tkinter).

Copia fiel de UI/state/app_state.py reemplazando tk.StringVar/IntVar por
ObservableVar (Signal de Qt). La API publica es identica, asi los controladores
(ControladorPrecios, ControladorComparacion, etc.) se reutilizan sin cambios.
"""

from UI_qt.state.observable import StringVar, IntVar


class AppState:
    """Estado centralizado de la aplicacion.

    Consolida todas las variables de estado (StringVar, IntVar) en un solo lugar.
    Emite eventos automaticamente cuando cambian las selecciones principales
    mediante traces de las variables observables.
    """

    def __init__(self, event_bus):
        """Inicializa el estado de la aplicacion.

        Args:
            event_bus (EventBus): Sistema de eventos para emitir cambios de estado
        """
        self._event_bus = event_bus

        # ===== Variables de seleccion =====
        self.hotel = StringVar()
        self.edificio = StringVar()
        self.habitacion = StringVar()

        # ===== Variables de fecha =====
        self.fecha_dia_entrada = StringVar()
        self.fecha_mes_entrada = StringVar()
        self.fecha_ano_entrada = StringVar()
        self.fecha_entrada_completa = StringVar()

        self.fecha_dia_salida = StringVar()
        self.fecha_mes_salida = StringVar()
        self.fecha_ano_salida = StringVar()
        self.fecha_salida_completa = StringVar()

        # ===== Variables de huespedes =====
        self.adultos = IntVar(value=1)
        self.ninos = IntVar(value=0)
        self.edades_ninos: list[int] = []

        # ===== Variables de resultado =====
        self.precio = StringVar(value="(ninguna seleccionada)")
        self.periodos_var = StringVar()

        # ===== Datos cargados =====
        self.hoteles_excel = []
        self.habitaciones_excel = []
        self.habitaciones_unificadas = []
        self.habitacion_web = None
        self.resultado_multiperiodo = None
        self.periodos_precio = []

        # ===== Habitacion seleccionada (objeto rico) =====
        self.habitacion_unificada_actual = None

        # ===== Gap analysis (cobertura de periodos) =====
        self.gap_analysis_actual = None
        self.gap_confirmado = False

        self._setup_traces()

    def _setup_traces(self):
        """Configura traces en las variables para emitir eventos cuando cambian."""
        self.hotel.trace_add('write', lambda *args:
                             self._event_bus.emit('hotel_changed', self.hotel.get()))

        self.edificio.trace_add('write', lambda *args:
                                self._event_bus.emit('edificio_changed', self.edificio.get()))

        self.habitacion.trace_add('write', lambda *args:
                                  self._event_bus.emit('habitacion_changed', self.habitacion.get()))

    def reset_edificio(self):
        """Resetea la seleccion de edificio."""
        self.edificio.set("")

    def reset_habitacion(self):
        """Resetea la seleccion de habitacion y el precio."""
        self.habitacion.set("")
        self.precio.set("(ninguna seleccionada)")

    def reset_fechas(self):
        """Resetea todas las variables de fecha."""
        self.fecha_dia_entrada.set("")
        self.fecha_mes_entrada.set("")
        self.fecha_ano_entrada.set("")
        self.fecha_entrada_completa.set("")

        self.fecha_dia_salida.set("")
        self.fecha_mes_salida.set("")
        self.fecha_ano_salida.set("")
        self.fecha_salida_completa.set("")

    def actualizar_edades_ninos(self, n: int):
        """Redimensiona edades_ninos al nuevo count. Completa con 12 por defecto."""
        while len(self.edades_ninos) < n:
            self.edades_ninos.append(12)
        self.edades_ninos = self.edades_ninos[:n]

    def reset_huespedes(self):
        """Resetea las variables de huespedes a valores por defecto."""
        self.adultos.set(1)
        self.ninos.set(0)
        self.edades_ninos = []

    def reset_all(self):
        """Resetea todo el estado de la aplicacion."""
        self.hotel.set("")
        self.reset_edificio()
        self.reset_habitacion()
        self.reset_fechas()
        self.reset_huespedes()
        self.periodos_var.set("")
        self.habitacion_web = None
        self.habitacion_unificada_actual = None
        self.periodos_precio = []
        self.gap_analysis_actual = None
        self.gap_confirmado = False
