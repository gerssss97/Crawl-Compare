"""Controlador de validaciones de negocio."""

from datetime import datetime
from tkinter import messagebox


class ControladorValidacion:
    """Controlador de validaciones de negocio.

    Centraliza todas las validaciones de la aplicación:
    - Validación de fechas
    - Validación de orden de fechas
    - Validación de campos completos

    Ejemplo de uso:
        controlador = ControladorValidacion(estado_app)
        if controlador.validar_todo():
            # Proceder con la comparación
            pass
    """

    def __init__(self, estado_app):
        """Inicializa el controlador de validación.

        Args:
            estado_app (AppState): Estado centralizado de la aplicación
        """
        self.estado_app = estado_app

    def validar_fecha(self, fecha_str, nombre_campo):
        """Valida formato y existencia de fecha.

        Args:
            fecha_str (str): Fecha en formato DD-MM-AAAA
            nombre_campo (str): Nombre del campo para mensajes de error

        Returns:
            bool: True si es válida, False si no
        """
        try:
            fecha_dt = datetime.strptime(fecha_str, "%d-%m-%Y")
            fecha_actual = datetime.now()

            if fecha_actual > fecha_dt:
                messagebox.showerror(
                    "Error",
                    f"La fecha de {nombre_campo} debe ser mayor o igual a la actual."
                )
                return False

            return True
        except ValueError:
            messagebox.showerror(
                "Error",
                f"La fecha de {nombre_campo} debe tener formato DD-MM-AAAA y ser válida."
            )
            return False

    def validar_orden_fechas(self, fecha_entrada_str, fecha_salida_str):
        """Valida que salida sea posterior a entrada.

        Args:
            fecha_entrada_str (str): Fecha entrada en formato DD-MM-AAAA
            fecha_salida_str (str): Fecha salida en formato DD-MM-AAAA

        Returns:
            bool: True si el orden es correcto, False si no
        """
        try:
            fecha_entrada = datetime.strptime(fecha_entrada_str, "%d-%m-%Y")
            fecha_salida = datetime.strptime(fecha_salida_str, "%d-%m-%Y")
        except ValueError:
            return False

        if fecha_salida <= fecha_entrada:
            messagebox.showerror(
                "Error",
                "La fecha de salida debe ser posterior a la de entrada."
            )
            return False

        return True

    def validar_campos_completos(self):
        """Valida que todos los campos requeridos estén completos.

        Returns:
            bool: True si todos los campos están completos, False si no
        """
        campos = {
            "Fecha de entrada": self.estado_app.fecha_entrada_completa.get(),
            "Fecha de salida": self.estado_app.fecha_salida_completa.get(),
            "Número de adultos": self.estado_app.adultos.get(),
            "Número de niños": self.estado_app.ninos.get(),
            "Habitación Excel": self.estado_app.habitacion.get(),
            "Precio": self.estado_app.precio.get()
        }

        for nombre, valor in campos.items():
            # Validar que no esté vacío
            if valor in ("", None, "(ninguna seleccionada)"):
                messagebox.showerror(
                    "Error",
                    f"El campo '{nombre}' no puede estar vacío. Por favor, revísalo."
                )
                return False

            # Validación especial para adultos
            if nombre == "Número de adultos":
                try:
                    if int(valor) <= 0:
                        messagebox.showerror(
                            "Error",
                            "Debe haber al menos 1 adulto."
                        )
                        return False
                except (ValueError, TypeError):
                    messagebox.showerror(
                        "Error",
                        "El número de adultos debe ser un valor numérico válido."
                    )
                    return False

        return True

    def validar_todo(self):
        """Ejecuta todas las validaciones.

        Returns:
            bool: True si todas las validaciones pasan, False si no
        """
        # Validar campos completos primero
        if not self.validar_campos_completos():
            return False

        # Obtener fechas
        fecha_entrada = self.estado_app.fecha_entrada_completa.get()
        fecha_salida = self.estado_app.fecha_salida_completa.get()

        # Validar fecha de entrada
        if not self.validar_fecha(fecha_entrada, "entrada"):
            return False

        # Validar fecha de salida
        if not self.validar_fecha(fecha_salida, "salida"):
            return False

        # Validar orden de fechas
        if not self.validar_orden_fechas(fecha_entrada, fecha_salida):
            return False

        return True
