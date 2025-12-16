"""Utilidades para manejo de scrollbars en la interfaz."""

from tkinter import ttk


def crear_scrollbar_autohide(widget, scrollbar, layout_manager='grid'):
    """Crea un callback para auto-hide de scrollbar.

    Esta función devuelve un callback que oculta/muestra automáticamente
    un scrollbar según si el contenido excede el tamaño visible del widget.

    Args:
        widget: Widget que contiene el scrollbar (para referencia, no usado actualmente)
        scrollbar: El widget Scrollbar a mostrar/ocultar
        layout_manager: 'grid' o 'pack' según el layout manager usado

    Returns:
        callable: Función callback(first, last) para usar con yscrollcommand

    Ejemplo de uso con grid:
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        callback = crear_scrollbar_autohide(text, scrollbar, layout_manager='grid')
        text.configure(yscrollcommand=callback)

    Ejemplo de uso con pack:
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        callback = crear_scrollbar_autohide(canvas, scrollbar, layout_manager='pack')
        canvas.configure(yscrollcommand=callback)
    """

    def autohide_callback(first, last):
        """Callback que oculta/muestra scrollbar según necesidad.

        Args:
            first: Posición inicial visible (0.0 a 1.0)
            last: Posición final visible (0.0 a 1.0)
        """
        first, last = float(first), float(last)

        # Si todo el contenido es visible (first=0.0, last=1.0), ocultar scrollbar
        if first <= 0.0 and last >= 1.0:
            if layout_manager == 'grid':
                scrollbar.grid_remove()
            elif layout_manager == 'pack':
                scrollbar.pack_forget()
        else:
            # Mostrar scrollbar
            if layout_manager == 'grid':
                scrollbar.grid()
            elif layout_manager == 'pack':
                scrollbar.pack(side='right', fill='y')

        # Actualizar posición del scrollbar
        scrollbar.set(first, last)

    return autohide_callback
