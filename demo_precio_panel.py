"""Demo de CTkPrecioPanel - Muestra diferentes estados del panel de precios."""

import sys
sys.path.append('.')

from datetime import date
import customtkinter as ctk
from UI.components import CTkPrecioPanel
from UI.styles import Colors, Spacing

# Mock de objeto Periodo (para simular datos reales)
class MockPeriodo:
    def __init__(self, id, fecha_inicio, fecha_fin, nombre=None):
        self.id = id
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.nombre = nombre

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Crear ventana
root = ctk.CTk()
root.title("Demo - CTkPrecioPanel")
root.geometry("500x800")
root.configure(fg_color=Colors.BACKGROUND)

# Header
header = ctk.CTkFrame(root, fg_color=Colors.HEADER_BG, corner_radius=0)
header.pack(fill='x')

title = ctk.CTkLabel(
    header,
    text="Demo de CTkPrecioPanel",
    font=("Inter", 18, "bold"),
    text_color=Colors.HEADER_TEXT
)
title.pack(pady=16)

# Scrollable content
scrollable = ctk.CTkScrollableFrame(
    root,
    fg_color="transparent",
    scrollbar_button_color=Colors.PRIMARY,
    scrollbar_button_hover_color=Colors.PRIMARY_HOVER
)
scrollable.pack(fill='both', expand=True, padx=32, pady=20)

# ========================================
# ESTADO 1: Panel Vacío
# ========================================
label1 = ctk.CTkLabel(
    scrollable,
    text="[1] Estado Vacio (sin habitacion seleccionada)",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label1.pack(fill='x', pady=(0, 10))

panel1 = CTkPrecioPanel(scrollable)
panel1.pack(fill='x', pady=(0, Spacing.LG))

# ========================================
# ESTADO 2: Panel con mensaje custom
# ========================================
label2 = ctk.CTkLabel(
    scrollable,
    text="[2] Mensaje Custom (ingrese fechas)",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label2.pack(fill='x', pady=(Spacing.LG, 10))

panel2 = CTkPrecioPanel(scrollable)
panel2.pack(fill='x', pady=(0, Spacing.LG))
panel2._mostrar_mensaje("(Ingrese fechas para ver precios)")

# ========================================
# ESTADO 3: Un solo periodo con precio
# ========================================
label3 = ctk.CTkLabel(
    scrollable,
    text="[3] Un Solo Periodo",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label3.pack(fill='x', pady=(Spacing.LG, 10))

panel3 = CTkPrecioPanel(scrollable)
panel3.pack(fill='x', pady=(0, Spacing.LG))

# Datos de ejemplo - 1 periodo
periodo1 = MockPeriodo(
    id=1,
    fecha_inicio=date(2026, 12, 1),
    fecha_fin=date(2027, 3, 15),
    nombre="Temporada Alta"
)

precios_1_periodo = [
    {
        'periodo': periodo1,
        'precio': 45000.00,
        'nombre_grupo': 'Temporada Alta'
    }
]

panel3.mostrar_precios_multiples(precios_1_periodo)

# ========================================
# ESTADO 4: Múltiples periodos (2-3)
# ========================================
label4 = ctk.CTkLabel(
    scrollable,
    text="[4] Multiples Periodos (2-3 items)",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label4.pack(fill='x', pady=(Spacing.LG, 10))

panel4 = CTkPrecioPanel(scrollable)
panel4.pack(fill='x', pady=(0, Spacing.LG))

# Datos de ejemplo - 3 periodos
periodo2 = MockPeriodo(
    id=2,
    fecha_inicio=date(2027, 3, 16),
    fecha_fin=date(2027, 6, 30),
    nombre="Temporada Media"
)

periodo3 = MockPeriodo(
    id=3,
    fecha_inicio=date(2027, 7, 1),
    fecha_fin=date(2027, 9, 14),
    nombre="Temporada Baja"
)

precios_multiples = [
    {
        'periodo': periodo1,
        'precio': 45000.00,
        'nombre_grupo': 'Temporada Alta'
    },
    {
        'periodo': periodo2,
        'precio': 32000.50,
        'nombre_grupo': 'Temporada Media'
    },
    {
        'periodo': periodo3,
        'precio': 25000.00,
        'nombre_grupo': 'Temporada Baja'
    }
]

panel4.mostrar_precios_multiples(precios_multiples)

# ========================================
# ESTADO 5: Con precio en texto (no numérico)
# ========================================
label5 = ctk.CTkLabel(
    scrollable,
    text="[5] Precio con Texto (Consultar / Sin precio)",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label5.pack(fill='x', pady=(Spacing.LG, 10))

panel5 = CTkPrecioPanel(scrollable)
panel5.pack(fill='x', pady=(0, Spacing.LG))

precios_con_texto = [
    {
        'periodo': periodo1,
        'precio': 45000.00,
        'nombre_grupo': 'Temporada Alta'
    },
    {
        'periodo': periodo2,
        'precio': 'Consultar',
        'nombre_grupo': 'Temporada Media'
    },
    {
        'periodo': periodo3,
        'precio': 'Sin precio disponible',
        'nombre_grupo': 'Temporada Baja'
    }
]

panel5.mostrar_precios_multiples(precios_con_texto)

# ========================================
# ESTADO 6: Muchos periodos (con scroll)
# ========================================
label6 = ctk.CTkLabel(
    scrollable,
    text="[6] Muchos Periodos (scroll automatico)",
    font=("Inter", 14, "bold"),
    text_color=Colors.TEXT_PRIMARY,
    anchor='w'
)
label6.pack(fill='x', pady=(Spacing.LG, 10))

panel6 = CTkPrecioPanel(scrollable)
panel6.pack(fill='x', pady=(0, Spacing.LG))

# Generar 5 periodos
muchos_periodos = []
for i in range(1, 6):
    p = MockPeriodo(
        id=i,
        fecha_inicio=date(2027, i*2, 1),
        fecha_fin=date(2027, i*2, 28),
        nombre=f"Periodo {i}"
    )
    muchos_periodos.append({
        'periodo': p,
        'precio': 30000 + (i * 5000),
        'nombre_grupo': f'Grupo {i}'
    })

panel6.mostrar_precios_multiples(muchos_periodos)

# Footer
footer = ctk.CTkLabel(
    root,
    text="El panel adapta su diseno segun la cantidad de periodos",
    font=("Inter", 11),
    text_color=Colors.TEXT_DISABLED
)
footer.pack(pady=(10, 15))

# Instrucciones
print("\n" + "="*60)
print("Demo de CTkPrecioPanel")
print("="*60)
print("\nEstados mostrados:")
print("   1. Vacio (sin seleccion)")
print("   2. Mensaje custom")
print("   3. Un solo periodo")
print("   4. Multiples periodos (2-3)")
print("   5. Con precios en texto ('Consultar')")
print("   6. Muchos periodos (con scroll interno)")
print("\nObserva:")
print("   - Gradientes azules para los periodos")
print("   - Precios numericos con fondo verde")
print("   - Precios texto con fondo blanco")
print("   - Scroll automatico cuando hay 4+ periodos")
print("   - Fechas con formato DD/MM/YYYY")
print("\nCerra la ventana para terminar\n")

root.mainloop()
