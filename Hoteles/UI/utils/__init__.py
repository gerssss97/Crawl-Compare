"""Utilidades generales para la interfaz de usuario."""


def normalizar_hotel_nombre(nombre: str) -> str:
    """Convierte el nombre de un hotel al formato interno del Excel: 'nombre (a)'."""
    return nombre.lower() + " (a)"


__all__ = ['crear_scrollbar_autohide', 'normalizar_hotel_nombre']
