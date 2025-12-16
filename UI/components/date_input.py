"""Date input widget with validation (DD-MM-AAAA format)."""

import tkinter as tk
from tkinter import ttk
from .base_component import BaseComponent
from UI.utils.validadores_fecha import validar_dia, validar_mes, validar_ano


class DateInputWidget(BaseComponent):
    """Widget de entrada de fecha con validación (DD-MM-AAAA).

    Componente reutilizable que permite ingresar una fecha mediante tres campos
    separados (día, mes, año) con validación en tiempo real. Muestra la fecha
    completa en un campo de solo lectura.

    Ejemplo de uso:
        date_widget = DateInputWidget(parent, label_text="Fecha de entrada", fonts=fonts)
        date_widget.pack()
        fecha = date_widget.get_value()  # "15-03-2024"
    """

    def __init__(self, parent, label_text="Fecha", fonts=None, **kwargs):
        """Inicializa el widget de fecha.

        Args:
            parent: Widget padre de Tkinter
            label_text (str): Texto del label superior
            fonts (FontManager, optional): Gestor de fuentes
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.label_text = label_text
        self.fonts = fonts

        # Variables internas
        self._dia = tk.StringVar()
        self._mes = tk.StringVar()
        self._ano = tk.StringVar()
        self._fecha_completa = tk.StringVar()

        # Callback externo
        self._on_change_callback = None

        super().__init__(parent, **kwargs)

    def _setup_ui(self):
        """Construye la interfaz del componente."""
        bg_color = '#F5F5F5'
        self.configure(bg=bg_color)

        # Label principal
        font_label = self.fonts.normal if self.fonts else None
        label = tk.Label(self, text=self.label_text, bg=bg_color, font=font_label)
        label.grid(row=0, column=0, sticky='w', pady=(4, 4))

        # Frame de inputs
        input_frame = tk.Frame(self, bg=bg_color)
        input_frame.grid(row=1, column=0, sticky='ew', pady=(0, 8))

        # DD
        tk.Label(input_frame, text="DD", bg=bg_color, font=font_label).grid(
            row=0, column=0, padx=(0, 2))
        self._entry_dia = ttk.Entry(
            input_frame, width=3, textvariable=self._dia,
            validate='key', validatecommand=self._get_dia_validation())
        self._entry_dia.grid(row=0, column=1, padx=2)

        tk.Label(input_frame, text="-", bg=bg_color).grid(row=0, column=2, padx=2)

        # MM
        tk.Label(input_frame, text="MM", bg=bg_color, font=font_label).grid(
            row=0, column=3, padx=2)
        self._entry_mes = ttk.Entry(
            input_frame, width=3, textvariable=self._mes,
            validate='key', validatecommand=self._get_mes_validation())
        self._entry_mes.grid(row=0, column=4, padx=2)

        tk.Label(input_frame, text="-", bg=bg_color).grid(row=0, column=5, padx=2)

        # AAAA
        tk.Label(input_frame, text="AAAA", bg=bg_color, font=font_label).grid(
            row=0, column=6, padx=2)
        self._entry_ano = ttk.Entry(
            input_frame, width=5, textvariable=self._ano,
            validate='key', validatecommand=self._get_ano_validation())
        self._entry_ano.grid(row=0, column=7, padx=2)


    def _get_dia_validation(self):
        """Comando de validación para día."""
        return (self.register(self._validar_dia), "%P")

    def _get_mes_validation(self):
        """Comando de validación para mes."""
        return (self.register(self._validar_mes), "%P")

    def _get_ano_validation(self):
        """Comando de validación para año."""
        return (self.register(self._validar_ano), "%P")

    def _validar_dia(self, valor):
        """Valida el día (1-31)."""
        return validar_dia(valor)

    def _validar_mes(self, valor):
        """Valida el mes (1-12)."""
        return validar_mes(valor)

    def _validar_ano(self, valor):
        """Valida el año (1-4 dígitos)."""
        return validar_ano(valor)



    def set_value(self, fecha_str):
        """Establece fecha desde string DD-MM-AAAA.

        Args:
            fecha_str (str): Fecha en formato "DD-MM-AAAA"
        """
        if not fecha_str:
            self.reset()
            return

        try:
            partes = fecha_str.split('-')
            if len(partes) == 3:
                self._dia.set(partes[0])
                self._mes.set(partes[1])
                self._ano.set(partes[2])
        except:
            pass

    def reset(self):
        """Resetea a vacío."""
        self._dia.set("")
        self._mes.set("")
        self._ano.set("")

    def on_change(self, callback):
        """Registra callback para cuando cambia la fecha.

        Args:
            callback (callable): Función a llamar con la fecha completa
        """
        self._on_change_callback = callback

    def get_dia_var(self):
        """Obtiene StringVar del día."""
        return self._dia

    def get_mes_var(self):
        """Obtiene StringVar del mes."""
        return self._mes

    def get_ano_var(self):
        """Obtiene StringVar del año."""
        return self._ano
