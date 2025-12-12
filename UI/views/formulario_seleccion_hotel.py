"""Formulario de selección de hotel, edificio y habitación."""

import tkinter as tk
from UI.components import LabeledComboBox


class FormularioSeleccionHotel(tk.Frame):
    """Formulario de selección de hotel, edificio y habitación.

    Maneja la lógica de mostrar/ocultar el selector de edificio dinámicamente
    según si el hotel tiene tipos/edificios o habitaciones directas.

    Ejemplo de uso:
        form = FormularioSeleccionHotel(parent, estado_app, fonts)
        form.pack()
        form.on_hotel_selected(lambda hotel: print(f"Hotel: {hotel}"))
    """

    def __init__(self, parent, estado_app, fonts, **kwargs):
        """Inicializa el formulario de selección.

        Args:
            parent: Widget padre de Tkinter
            estado_app (AppState): Estado centralizado de la aplicación
            fonts (FontManager): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame
        """
        super().__init__(parent, **kwargs)
        self.estado_app = estado_app
        self.fonts = fonts

        # Componentes
        self.combo_hotel = None
        self.combo_edificio = None
        self.combo_habitacion = None

        # Callbacks externos
        self._on_hotel_selected_callback = None
        self._on_edificio_selected_callback = None
        self._on_habitacion_selected_callback = None

        self._configurar_ui()

    def _configurar_ui(self):
        """Configura la interfaz del formulario."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Hotel (siempre visible)
        self.combo_hotel = LabeledComboBox(
            self,
            label_text="Selección hotel:",
            textvariable=self.estado_app.hotel,
            fonts=self.fonts
        )
        self.combo_hotel.grid(row=0, column=0, sticky='ew')
        self.combo_hotel.on_select(self._on_hotel_selected_interno)

        # Expandir
        self.grid_columnconfigure(0, weight=1)

    def _on_hotel_selected_interno(self, hotel_nombre):
        """Handler interno cuando se selecciona un hotel."""
        if self._on_hotel_selected_callback:
            self._on_hotel_selected_callback(hotel_nombre)

    def _on_edificio_selected_interno(self, edificio_nombre):
        """Handler interno cuando se selecciona un edificio."""
        if self._on_edificio_selected_callback:
            self._on_edificio_selected_callback(edificio_nombre)

    def _on_habitacion_selected_interno(self, habitacion_nombre):
        """Handler interno cuando se selecciona una habitación."""
        if self._on_habitacion_selected_callback:
            self._on_habitacion_selected_callback(habitacion_nombre)

    def mostrar_edificio(self, valores):
        """Muestra combobox de edificio con valores.

        Args:
            valores (list): Lista de nombres de edificios
        """
        if self.combo_edificio:
            self.combo_edificio.destroy()

        self.combo_edificio = LabeledComboBox(
            self,
            label_text="Edificio:",
            textvariable=self.estado_app.edificio,
            fonts=self.fonts
        )
        self.combo_edificio.set_values(valores)
        self.combo_edificio.grid(row=1, column=0, sticky='ew')
        self.combo_edificio.on_select(self._on_edificio_selected_interno)

    def ocultar_edificio(self):
        """Oculta combobox de edificio."""
        if self.combo_edificio:
            self.combo_edificio.destroy()
            self.combo_edificio = None

    def mostrar_habitacion(self, valores):
        """Muestra combobox de habitación con valores.

        Args:
            valores (list): Lista de nombres de habitaciones
        """
        if self.combo_habitacion:
            self.combo_habitacion.destroy()

        # Calcular fila: 2 si hay edificio, 1 si no
        fila = 2 if self.combo_edificio else 1

        self.combo_habitacion = LabeledComboBox(
            self,
            label_text="Selección habitación Excel:",
            textvariable=self.estado_app.habitacion,
            fonts=self.fonts
        )
        self.combo_habitacion.set_values(valores)
        self.combo_habitacion.grid(row=fila, column=0, sticky='ew')
        self.combo_habitacion.on_select(self._on_habitacion_selected_interno)

    def ocultar_habitacion(self):
        """Oculta combobox de habitación."""
        if self.combo_habitacion:
            self.combo_habitacion.destroy()
            self.combo_habitacion = None

    def set_hoteles(self, valores):
        """Establece la lista de hoteles.

        Args:
            valores (list): Lista de nombres de hoteles
        """
        self.combo_hotel.set_values(valores)

    def seleccionar_hotel(self, hotel_nombre):
        """Selecciona un hotel por nombre.

        Args:
            hotel_nombre (str): Nombre del hotel a seleccionar
        """
        self.combo_hotel.set_value(hotel_nombre)

    def on_hotel_selected(self, callback):
        """Registra callback para cuando se selecciona un hotel.

        Args:
            callback (callable): Función a llamar con el nombre del hotel
        """
        self._on_hotel_selected_callback = callback

    def on_edificio_selected(self, callback):
        """Registra callback para cuando se selecciona un edificio.

        Args:
            callback (callable): Función a llamar con el nombre del edificio
        """
        self._on_edificio_selected_callback = callback

    def on_habitacion_selected(self, callback):
        """Registra callback para cuando se selecciona una habitación.

        Args:
            callback (callable): Función a llamar con el nombre de la habitación
        """
        self._on_habitacion_selected_callback = callback

    def obtener_indice_habitacion(self):
        """Obtiene el índice de la habitación seleccionada.

        Returns:
            int: Índice de la habitación (-1 si no hay selección)
        """
        if self.combo_habitacion:
            return self.combo_habitacion.current()
        return -1
