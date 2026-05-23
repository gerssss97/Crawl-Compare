"""Card component - Contenedor visual para agrupar elementos relacionados."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent


class CTkCard(CTkBaseComponent):
    """Card con título opcional y contenedor de contenido.
    
    Proporciona un marco visual consistente para agrupar elementos relacionados.
    Incluye:
    - Borde sutil
    - Título opcional con ícono
    - Frame de contenido (content_frame) donde agregar widgets
    
    Ejemplo de uso:
        card = CTkCard(parent, title="SELECCIÓN DE RESERVA", icon="🏨")
        card.pack(fill='x', pady=10)
        
        # Agregar contenido al content_frame
        label = ctk.CTkLabel(card.content_frame, text="Contenido")
        label.pack()
    """
    
    def __init__(self, parent, title=None, icon=None, **kwargs):
        """Inicializa la card.
        
        Args:
            parent: Widget padre
            title (str, optional): Título a mostrar en la parte superior
            icon (str, optional): Emoji/ícono a mostrar junto al título
            **kwargs: Argumentos adicionales para CTkFrame
        """
        self.title_text = title
        self.icon = icon
        
        # Configurar estilo de card
        kwargs.setdefault('fg_color', Colors.SURFACE)
        kwargs.setdefault('corner_radius', Spacing.RADIUS_MD)
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('border_color', Colors.BORDER)
        
        super().__init__(parent, **kwargs)
    
    def _setup_ui(self):
        """Construye la estructura interna de la card."""
        # Si hay título, crear área de título
        if self.title_text:
            self._crear_titulo()
        
        # Crear frame de contenido (donde el usuario pondrá sus widgets)
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        
        # Padding del content_frame
        padding_top = Spacing.SM if self.title_text else Spacing.CARD_PADDING
        
        self.content_frame.pack(
            fill='both',
            expand=True,
            padx=Spacing.CARD_PADDING,
            pady=(padding_top, Spacing.CARD_PADDING)
        )
    
    def _crear_titulo(self):
        """Crea el área de título de la card."""
        self.title_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.title_frame.pack(
            fill='x',
            padx=Spacing.CARD_PADDING,
            pady=(Spacing.CARD_PADDING, Spacing.SM)
        )

        # Ícono con fuente del sistema para emojis a color
        if self.icon:
            icon_label = ctk.CTkLabel(
                self.title_frame,
                text=self.icon,
                font=("Segoe UI", Typography.SMALL),
                text_color=Colors.TEXT_SECONDARY,
                anchor='w'
            )
            icon_label.pack(side='left', padx=(0, Spacing.XS))

        # Texto del título
        title_label = ctk.CTkLabel(
            self.title_frame,
            text=self.title_text,
            font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
            text_color=Colors.TEXT_SECONDARY,
            anchor='w'
        )
        title_label.pack(side='left', fill='x', expand=True)
    
    def set_title(self, new_title):
        """Actualiza el título de la card.
        
        Args:
            new_title (str): Nuevo título
        """
        self.title_text = new_title
        # TODO: Implementar actualización dinámica del título si es necesario
    
    def clear_content(self):
        """Limpia todo el contenido de la card."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
