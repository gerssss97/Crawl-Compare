"""Entry simple con label - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent


class CTkLabeledEntry(CTkBaseComponent):
    """Entry (campo de texto) con label arriba.
    
    Proporciona un campo de entrada estilizado con label descriptivo.
    Útil para inputs simples como números, texto corto, etc.
    
    Ejemplo de uso:
        entry = CTkLabeledEntry(
            parent,
            label="Adultos",
            icon="👥",
            textvariable=adultos_var,
            placeholder="2",
            width=100
        )
        entry.pack(fill='x', pady=10)
    """
    
    def __init__(self, parent, label, icon=None, textvariable=None,
                 placeholder="", state="normal", width=None, **kwargs):
        """Inicializa el Entry con label.
        
        Args:
            parent: Widget padre
            label (str): Texto del label
            icon (str, optional): Emoji/ícono para mostrar junto al label
            textvariable (tk.StringVar, optional): Variable para almacenar el valor
            placeholder (str): Texto placeholder
            state (str): Estado inicial ('normal' o 'disabled')
            width (int, optional): Ancho del entry en pixels
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.label_text = label
        self.icon = icon
        self.textvariable = textvariable
        self.placeholder_text = placeholder
        self.state_value = state
        self.width_value = width
        
        # Frame transparente
        kwargs.setdefault('fg_color', "transparent")
        kwargs.setdefault('corner_radius', 0)
        
        super().__init__(parent, **kwargs)
    
    def _setup_ui(self):
        """Construye el label y el entry."""
        # Label
        label_text = f"{self.icon} {self.label_text}" if self.icon else self.label_text
        
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY,
            anchor='w'
        )
        self.label.pack(fill='x', pady=(0, Spacing.XS))
        
        # Entry
        entry_kwargs = {
            'textvariable': self.textvariable,
            'placeholder_text': self.placeholder_text,
            'state': self.state_value,
            'font': (Typography.FAMILY, Typography.BODY),
            'fg_color': Colors.SURFACE,
            'border_color': Colors.BORDER,
            'text_color': Colors.TEXT_PRIMARY,
            'placeholder_text_color': Colors.TEXT_DISABLED,
            'corner_radius': Spacing.RADIUS_MD,
            'border_width': 1,
            'height': 40
        }
        
        if self.width_value:
            entry_kwargs['width'] = self.width_value
        
        self.entry = ctk.CTkEntry(self, **entry_kwargs)
        self.entry.pack(fill='x')
    
    def get_value(self):
        """Obtiene el valor actual del entry.
        
        Returns:
            str: Valor del entry
        """
        if self.textvariable:
            return self.textvariable.get()
        return self.entry.get()
    
    def set_value(self, value):
        """Establece el valor del entry.
        
        Args:
            value (str): Valor a establecer
        """
        if self.textvariable:
            self.textvariable.set(value)
        else:
            self.entry.delete(0, 'end')
            self.entry.insert(0, value)
    
    def reset(self):
        """Limpia el entry."""
        self.set_value("")
    
    def set_state(self, state):
        """Habilita o deshabilita el entry.
        
        Args:
            state (str): 'normal' o 'disabled'
        """
        self.state_value = state
        self.entry.configure(state=state)
