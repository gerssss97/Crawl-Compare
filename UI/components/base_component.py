"""Base component class for all reusable UI widgets."""

from tkinter import ttk


class BaseComponent(ttk.Frame):
    """Clase base para componentes reutilizables de la UI.

    Proporciona una estructura consistente para crear widgets personalizados
    que siguen el mismo patrón de inicialización, configuración y acceso a datos.

    Los componentes hijos deben implementar los métodos abstractos para definir
    su comportamiento específico.

    Ejemplo de uso:
        class MyComponent(BaseComponent):
            def _setup_ui(self):
                label = tk.Label(self, text="Hello")
                label.pack()

            def get_value(self):
                return "some value"

            def set_value(self, value):
                # update UI with value
                pass
    """

    def __init__(self, parent, **kwargs):
        """Inicializa el componente.

        Args:
            parent: Widget padre de Tkinter
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Construye la interfaz del componente.

        Las subclases DEBEN implementar este método para crear los widgets
        internos del componente.

        Raises:
            NotImplementedError: Si la subclase no implementa este método
        """
        raise NotImplementedError("Subclases deben implementar _setup_ui")

    def _bind_events(self):
        """Conecta eventos internos del componente.

        Las subclases PUEDEN sobrescribir este método para conectar
        event handlers específicos. Por defecto no hace nada.
        """
        pass

    def get_value(self):
        """Obtiene el valor actual del componente.

        Las subclases DEBEN implementar este método para devolver
        el valor apropiado.

        Returns:
            El valor actual del componente (tipo depende de la subclase)

        Raises:
            NotImplementedError: Si la subclase no implementa este método
        """
        raise NotImplementedError("Subclases deben implementar get_value")

    def set_value(self, value):
        """Establece el valor del componente.

        Las subclases DEBEN implementar este método para actualizar
        el estado interno con el valor proporcionado.

        Args:
            value: El valor a establecer (tipo depende de la subclase)

        Raises:
            NotImplementedError: Si la subclase no implementa este método
        """
        raise NotImplementedError("Subclases deben implementar set_value")

    def reset(self):
        """Resetea el componente a su estado inicial.

        Las subclases PUEDEN sobrescribir este método para definir
        el comportamiento de reseteo. Por defecto no hace nada.
        """
        pass

    def enable(self):
        """Habilita el componente y todos sus widgets hijos."""
        for child in self.winfo_children():
            try:
                child.configure(state='normal')
            except:
                # Algunos widgets no soportan el estado 'normal'
                pass

    def disable(self):
        """Deshabilita el componente y todos sus widgets hijos."""
        for child in self.winfo_children():
            try:
                child.configure(state='disabled')
            except:
                # Algunos widgets no soportan el estado 'disabled'
                pass
