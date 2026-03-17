"""Configuración tipográfica centralizada."""

class Typography:
    """Sistema de tipografía del sistema."""
    
    # Familia de fuente
    FAMILY = "Inter"
    FALLBACK = ("Segoe UI", "Arial", "sans-serif")
    
    # Tamaños (en pixeles)
    H1 = 18       # Títulos principales
    H2 = 16       # Títulos de secciones
    BODY = 14     # Texto normal
    SMALL = 12    # Labels, hints
    PRECIO = 28   # Precios destacados
    
    # Pesos (solo "normal" y "bold" son válidos en Tkinter)
    NORMAL = "normal"
    BOLD = "bold"
    
    # Alias para compatibilidad (mapea a valores válidos)
    MEDIUM = "normal"  # Medium se mapea a normal en Tkinter
