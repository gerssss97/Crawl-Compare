"""Input de fecha DD-MM-AAAA - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent


class CTkDateInput(CTkBaseComponent):
    """Componente de entrada de fecha con 3 campos separados (DD/MM/AAAA).
    
    Proporciona 3 campos de entrada independientes para día, mes y año.
    Cada campo tiene su propia variable de Tkinter y placeholder.
    
    Ejemplo de uso:
        date_input = CTkDateInput(
            parent,
            label="Fecha de entrada",
            icon="📅",
            day_var=dia_var,
            month_var=mes_var,
            year_var=ano_var
        )
        date_input.pack(fill='x', pady=10)
    """
    
    def __init__(self, parent, label, icon=None,
                 day_var=None, month_var=None, year_var=None, **kwargs):
        """Inicializa el componente de fecha.
        
        Args:
            parent: Widget padre
            label (str): Texto del label
            icon (str, optional): Emoji/ícono para mostrar junto al label
            day_var (tk.StringVar, optional): Variable para el día
            month_var (tk.StringVar, optional): Variable para el mes
            year_var (tk.StringVar, optional): Variable para el año
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.label_text = label
        self.icon = icon
        self.day_var = day_var
        self.month_var = month_var
        self.year_var = year_var
        
        # Frame transparente
        kwargs.setdefault('fg_color', "transparent")
        kwargs.setdefault('corner_radius', 0)
        
        super().__init__(parent, **kwargs)
    
    def _setup_ui(self):
        """Construye el label y los 3 campos de entrada."""
        # Label
        label_text = f"{self.icon} {self.label_text}" if self.icon else self.label_text
        
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        )
        self.label.pack(fill='x', pady=(0, Spacing.SM))
        
        # Frame para los 3 inputs
        inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        inputs_frame.pack(fill='x')
        
        # Estilo común para los entries
        entry_style = {
            'font': (Typography.FAMILY, Typography.BODY),
            'fg_color': Colors.SURFACE,
            'border_color': Colors.BORDER,
            'text_color': Colors.TEXT_PRIMARY,
            'placeholder_text_color': Colors.TEXT_DISABLED,
            'corner_radius': Spacing.RADIUS_MD,
            'border_width': 1,
            'height': 40
        }
        
        # DD (día)
        self.day_entry = ctk.CTkEntry(
            inputs_frame,
            width=70,
            placeholder_text="DD",
            textvariable=self.day_var,
            **entry_style
        )
        self.day_entry.pack(side='left', padx=(0, Spacing.SM))
        
        # MM (mes)
        self.month_entry = ctk.CTkEntry(
            inputs_frame,
            width=90,
            placeholder_text="MM",
            textvariable=self.month_var,
            **entry_style
        )
        self.month_entry.pack(side='left', padx=(0, Spacing.SM))
        
        # AAAA (año)
        self.year_entry = ctk.CTkEntry(
            inputs_frame,
            width=100,
            placeholder_text="AAAA",
            textvariable=self.year_var,
            **entry_style
        )
        self.year_entry.pack(side='left')
        
        # Limitar caracteres con validación
        self._setup_validation()
    
    def _setup_validation(self):
        """Configura validación básica de caracteres."""
        # Limitar día a 2 dígitos
        if self.day_var:
            self.day_var.trace_add('write', lambda *args: self._limit_length(self.day_var, 2))
        
        # Limitar mes a 2 dígitos
        if self.month_var:
            self.month_var.trace_add('write', lambda *args: self._limit_length(self.month_var, 2))
        
        # Limitar año a 4 dígitos
        if self.year_var:
            self.year_var.trace_add('write', lambda *args: self._limit_length(self.year_var, 4))
    
    def _limit_length(self, var, max_length):
        """Limita la longitud de una variable de texto.
        
        Args:
            var (tk.StringVar): Variable a limitar
            max_length (int): Longitud máxima
        """
        value = var.get()
        if len(value) > max_length:
            var.set(value[:max_length])
    
    def get_value(self):
        """Obtiene la fecha como tupla (día, mes, año).
        
        Returns:
            tuple: (día, mes, año) como strings
        """
        day = self.day_var.get() if self.day_var else self.day_entry.get()
        month = self.month_var.get() if self.month_var else self.month_entry.get()
        year = self.year_var.get() if self.year_var else self.year_entry.get()
        return (day, month, year)
    
    def set_value(self, day, month, year):
        """Establece los valores de fecha.
        
        Args:
            day (str): Día (DD)
            month (str): Mes (MM)
            year (str): Año (AAAA)
        """
        if self.day_var:
            self.day_var.set(day)
        else:
            self.day_entry.delete(0, 'end')
            self.day_entry.insert(0, day)
        
        if self.month_var:
            self.month_var.set(month)
        else:
            self.month_entry.delete(0, 'end')
            self.month_entry.insert(0, month)
        
        if self.year_var:
            self.year_var.set(year)
        else:
            self.year_entry.delete(0, 'end')
            self.year_entry.insert(0, year)
    
    def reset(self):
        """Limpia todos los campos de fecha."""
        self.set_value("", "", "")
    
    def set_state(self, state):
        """Habilita o deshabilita los campos.
        
        Args:
            state (str): 'normal' o 'disabled'
        """
        self.day_entry.configure(state=state)
        self.month_entry.configure(state=state)
        self.year_entry.configure(state=state)
