"""ComboBox con label - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent
from .ctk_custom_dropdown import CTkCustomDropdown


class CTkLabeledComboBox(CTkBaseComponent):
    """ComboBox (dropdown) con label arriba.
    
    Proporciona un dropdown estilizado con label descriptivo.
    Incluye soporte para íconos, estados (normal/disabled), y variables de Tkinter.
    
    Ejemplo de uso:
        combo = CTkLabeledComboBox(
            parent,
            label="Hotel",
            icon="🏨",
            textvariable=hotel_var,
            values=["Hotel 1", "Hotel 2"],
            state="normal"
        )
        combo.pack(fill='x', pady=10)
        
        # Actualizar valores
        combo.set_values(["Nuevo Hotel 1", "Nuevo Hotel 2"])
        
        # Cambiar estado
        combo.set_state("disabled")
    """
    
    def __init__(self, parent, label, icon=None, textvariable=None,
                 values=None, state="normal", command=None, **kwargs):
        """Inicializa el ComboBox con label.
        
        Args:
            parent: Widget padre
            label (str): Texto del label
            icon (str, optional): Emoji/ícono para mostrar junto al label
            textvariable (tk.StringVar, optional): Variable para almacenar el valor seleccionado
            values (list, optional): Lista de opciones del dropdown
            state (str): Estado inicial ('normal' o 'disabled')
            command (callable, optional): Función a ejecutar cuando cambia la selección
            **kwargs: Argumentos adicionales para el Frame padre
        """
        self.label_text = label
        self.icon = icon
        self.textvariable = textvariable
        self.values = values or []
        self.state_value = state
        self.command = command
        
        # Frame transparente (no queremos fondo)
        kwargs.setdefault('fg_color', "transparent")
        kwargs.setdefault('corner_radius', 0)
        
        super().__init__(parent, **kwargs)
    
    def _setup_ui(self):
        """Construye el label y el dropdown personalizado."""
        # Label
        label_text = f"{self.icon} {self.label_text}" if self.icon else self.label_text

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent",
            anchor='w'
        )
        self.label.pack(fill='x', pady=(0, Spacing.SM))

        # Usar dropdown personalizado en lugar de CTkComboBox
        # Esto soluciona los problemas de ancho y clickeabilidad
        self.combobox = CTkCustomDropdown(
            self,
            values=self.values,
            textvariable=self.textvariable,
            command=self.command,
            placeholder_text=f"Seleccionar {self.label_text.lower()}...",
        )
        self.combobox.pack(fill='x', expand=True)
    
    def set_values(self, values):
        """Actualiza los valores del combobox.

        Args:
            values (list): Nueva lista de opciones
        """
        self.values = values
        self.combobox.set_values(values)
    
    def set_state(self, state):
        """Cambia el estado del combobox.

        Args:
            state (str): 'normal' o 'disabled'
        """
        self.state_value = state
        # Deshabilitar/habilitar los widgets del dropdown
        new_state = "normal" if state == "normal" else "disabled"
        self.combobox.entry.configure(state=new_state if state == "normal" else "readonly")
        self.combobox.button.configure(state=new_state)
    
    def get_value(self):
        """Obtiene el valor actual del combobox.
        
        Returns:
            str: Valor seleccionado
        """
        if self.textvariable:
            return self.textvariable.get()
        return self.combobox.get()
    
    def set_value(self, value):
        """Establece el valor del combobox.
        
        Args:
            value (str): Valor a establecer
        """
        if self.textvariable:
            self.textvariable.set(value)
        else:
            self.combobox.set(value)
    
    def reset(self):
        """Resetea el combobox al primer valor o vacío."""
        if self.values:
            self.set_value(self.values[0])
        else:
            self.set_value("")
