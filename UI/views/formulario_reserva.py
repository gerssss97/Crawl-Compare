"""Formulario de datos de reserva (fechas y huéspedes)."""

import tkinter as tk
from tkinter import ttk
from UI.components import DateInputWidget, EntradaEtiquetada


class FormularioReserva(tk.Frame):
    """Formulario de datos de reserva (fechas y huéspedes).

    Agrupa los campos de fecha de entrada/salida, adultos, niños
    y el botón de ejecutar comparación.

    Ejemplo de uso:
        form = FormularioReserva(
            parent,
            estado_app,
            fonts,
            on_submit=ejecutar_comparacion
        )
        form.pack()
    """

    def __init__(self, parent, estado_app, fonts, on_submit=None, **kwargs):
        """Inicializa el formulario de reserva.

        Args:
            parent: Widget padre de Tkinter
            estado_app (AppState): Estado centralizado de la aplicación
            fonts (FontManager): Gestor de fuentes
            on_submit (callable, optional): Callback cuando se presiona ejecutar
            **kwargs: Argumentos adicionales para el Frame
        """
        super().__init__(parent, **kwargs)
        self.estado_app = estado_app
        self.fonts = fonts
        self.on_submit = on_submit

        self._configurar_ui()

    def _configurar_ui(self):
        """Configura la interfaz del formulario."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Fecha entrada
        self.fecha_entrada = DateInputWidget(
            self,
            label_text="Fecha de entrada:",
            fonts=self.fonts
        )
        self.fecha_entrada.grid(row=0, column=0, sticky='ew', pady=(0, 0))

        # Conectar las variables internas del DateInputWidget con el estado
        # para mantener compatibilidad con el código existente
        self.estado_app.fecha_dia_entrada = self.fecha_entrada.get_dia_var()
        self.estado_app.fecha_mes_entrada = self.fecha_entrada.get_mes_var()
        self.estado_app.fecha_ano_entrada = self.fecha_entrada.get_ano_var()
        self.estado_app.fecha_entrada_completa = self.fecha_entrada.get_fecha_completa_var()

        # Fecha salida
        self.fecha_salida = DateInputWidget(
            self,
            label_text="Fecha de salida:",
            fonts=self.fonts
        )
        self.fecha_salida.grid(row=1, column=0, sticky='ew', pady=(0, 0))

        # Conectar las variables internas con el estado
        self.estado_app.fecha_dia_salida = self.fecha_salida.get_dia_var()
        self.estado_app.fecha_mes_salida = self.fecha_salida.get_mes_var()
        self.estado_app.fecha_ano_salida = self.fecha_salida.get_ano_var()
        self.estado_app.fecha_salida_completa = self.fecha_salida.get_fecha_completa_var()

        # Adultos
        self.entrada_adultos = EntradaEtiquetada(
            self,
            texto_label="Cantidad de adultos:",
            textvariable=self.estado_app.adultos,
            fonts=self.fonts,
            width=10
        )
        self.entrada_adultos.grid(row=2, column=0, sticky='ew', pady=(0, 0))

        # Niños
        self.entrada_ninos = EntradaEtiquetada(
            self,
            texto_label="Cantidad de niños:",
            textvariable=self.estado_app.ninos,
            fonts=self.fonts,
            width=10
        )
        self.entrada_ninos.grid(row=3, column=0, sticky='ew', pady=(0, 0))

        # Botón ejecutar
        style = ttk.Style()
        style.configure('Boton.TButton', font=self.fonts.boton)

        self.boton_ejecutar = ttk.Button(
            self,
            text="Ejecutar comparación",
            command=self._on_submit_clicked,
            style='Boton.TButton'
        )
        self.boton_ejecutar.grid(row=4, column=0, sticky='ew', pady=(10, 10))

        # Expandir
        self.grid_columnconfigure(0, weight=1)

    def _on_submit_clicked(self):
        """Handler interno cuando se presiona el botón."""
        if self.on_submit:
            self.on_submit()

    def obtener_fecha_entrada(self):
        """Obtiene la fecha de entrada.

        Returns:
            str: Fecha en formato DD-MM-AAAA
        """
        return self.fecha_entrada.get_value()

    def obtener_fecha_salida(self):
        """Obtiene la fecha de salida.

        Returns:
            str: Fecha en formato DD-MM-AAAA
        """
        return self.fecha_salida.get_value()

    def obtener_adultos(self):
        """Obtiene cantidad de adultos.

        Returns:
            int: Número de adultos
        """
        return self.estado_app.adultos.get()

    def obtener_ninos(self):
        """Obtiene cantidad de niños.

        Returns:
            int: Número de niños
        """
        return self.estado_app.ninos.get()

    def resetear(self):
        """Resetea todos los campos del formulario."""
        self.fecha_entrada.reset()
        self.fecha_salida.reset()
        self.entrada_adultos.set_value(1)
        self.entrada_ninos.set_value(0)
