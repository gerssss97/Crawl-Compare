"""Centralized application state management."""

import tkinter as tk


class AppState:
    """Estado centralizado de la aplicación.

    Consolida todas las variables de estado (StringVar, IntVar) en un solo lugar,
    facilitando el acceso y la sincronización de datos entre componentes.

    Emite eventos automáticamente cuando cambian las selecciones principales mediante
    traces de las variables de Tkinter.
    """

    def __init__(self, event_bus):
        """Inicializa el estado de la aplicación.

        Args:
            event_bus (EventBus): Sistema de eventos para emitir cambios de estado
        """
        self._event_bus = event_bus

        # ===== Variables de selección =====
        self.hotel = tk.StringVar()
        self.edificio = tk.StringVar()
        self.habitacion = tk.StringVar()

        # ===== Variables de fecha =====
        # Componentes individuales de fecha de entrada
        self.fecha_dia_entrada = tk.StringVar()
        self.fecha_mes_entrada = tk.StringVar()
        self.fecha_ano_entrada = tk.StringVar()
        self.fecha_entrada_completa = tk.StringVar()

        # Componentes individuales de fecha de salida
        self.fecha_dia_salida = tk.StringVar()
        self.fecha_mes_salida = tk.StringVar()
        self.fecha_ano_salida = tk.StringVar()
        self.fecha_salida_completa = tk.StringVar()

        # ===== Variables de huéspedes =====
        self.adultos = tk.IntVar(value=1)
        self.ninos = tk.IntVar(value=0)

        # ===== Variables de resultado =====
        self.precio = tk.StringVar(value="(ninguna seleccionada)")
        self.periodos_var = tk.StringVar()  # Variable auxiliar para periodos

        # ===== Datos cargados =====
        self.hoteles_excel = []  # Lista de HotelExcel
        self.habitaciones_excel = []  # Lista de HabitacionExcel del hotel/edificio actual
        self.habitaciones_unificadas = []  # Lista de HabitacionUnificada (sin duplicados)
        self.habitacion_web = None  # HabitacionWeb de la última comparación

        # Configurar traces para emitir eventos
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
        """Resetea la selección de edificio."""
        self.edificio.set("")

    def reset_habitacion(self):
        """Resetea la selección de habitación y el precio."""
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

    def reset_huespedes(self):
        """Resetea las variables de huéspedes a valores por defecto."""
        self.adultos.set(1)
        self.ninos.set(0)

    def reset_all(self):
        """Resetea todo el estado de la aplicación."""
        self.hotel.set("")
        self.reset_edificio()
        self.reset_habitacion()
        self.reset_fechas()
        self.reset_huespedes()
        self.periodos_var.set("")
        self.habitacion_web = None
