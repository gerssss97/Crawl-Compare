"""Componente base para CustomTkinter - Clase padre de todos los componentes."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing


class CTkBaseComponent(ctk.CTkFrame):
    """Clase base para todos los componentes CustomTkinter.
    
    Proporciona:
    - Configuración de estilos por defecto
    - Método _setup_ui() para sobreescribir
    - Acceso a sistema de estilos centralizado
    
    Ejemplo de uso:
        class MiComponente(CTkBaseComponent):
            def _setup_ui(self):
                label = ctk.CTkLabel(self, text="Hola")
                label.pack()
    """
    
    def __init__(self, parent, **kwargs):
        """Inicializa el componente base.
        
        Args:
            parent: Widget padre de CustomTkinter
            **kwargs: Argumentos adicionales para CTkFrame
        """
        # Configurar defaults con nuestros estilos
        kwargs.setdefault('fg_color', Colors.SURFACE)
        kwargs.setdefault('corner_radius', Spacing.RADIUS_MD)
        kwargs.setdefault('border_width', 0)
        
        super().__init__(parent, **kwargs)
        self._setup_ui()
    
    def _setup_ui(self):
        """Método para sobreescribir en subclases.
        
        Acá va la lógica de construcción de la UI de cada componente.
        """
        pass
    
    def get_value(self):
        """Método opcional para obtener el valor del componente.
        
        Sobreescribir en subclases que manejen datos.
        """
        raise NotImplementedError("Subclase debe implementar get_value()")
    
    def set_value(self, value):
        """Método opcional para establecer el valor del componente.
        
        Sobreescribir en subclases que manejen datos.
        
        Args:
            value: Valor a establecer
        """
        raise NotImplementedError("Subclase debe implementar set_value()")
    
    def reset(self):
        """Método opcional para resetear el componente a su estado inicial.
        
        Sobreescribir en subclases que necesiten reseteo.
        """
        pass
