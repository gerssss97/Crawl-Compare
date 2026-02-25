"""Test rápido de los fixes de dropdown."""

import customtkinter as ctk
from UI.components import CTkLabeledComboBox
from UI.styles import Colors, Spacing

def test_dropdown():
    """Prueba el dropdown con los fixes aplicados."""
    root = ctk.CTk()
    root.title("Test Dropdown Fixes")
    root.geometry("600x400")

    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Crear un dropdown de prueba
    dropdown = CTkLabeledComboBox(
        main_frame,
        label="Selecciona una opción",
        values=["Opción 1 - Texto largo para ver si llena", "Opción 2 - Corta", "Opción 3"],
    )
    dropdown.pack(fill="x", pady=20)

    # Label informativo
    info_label = ctk.CTkLabel(
        main_frame,
        text="✓ Click en cualquier parte del dropdown abre el menú\n✓ El fondo del dropdown debe llenar hasta la flecha",
        text_color=Colors.TEXT_SECONDARY,
        justify="left"
    )
    info_label.pack(anchor="w", pady=10)

    # Frame de demostración adicional
    demo_frame = ctk.CTkFrame(main_frame, fg_color=Colors.PRIMARY_LIGHT, corner_radius=8)
    demo_frame.pack(fill="x", pady=20, padx=10)

    demo_text = ctk.CTkLabel(
        demo_frame,
        text="Intenta:\n1. Hacer click en el texto del dropdown\n2. Hacer click en la flecha\n3. Revisar que el fondo de las opciones llena todo el ancho",
        text_color=Colors.TEXT_PRIMARY,
        justify="left"
    )
    demo_text.pack(fill="x", padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    test_dropdown()
