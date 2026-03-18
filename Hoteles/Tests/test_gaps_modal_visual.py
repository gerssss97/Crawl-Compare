"""
Test visual: muestra el modal de advertencia de gaps (CtkModalAdvertenciaGaps).

Escenarios disponibles:
  1 - Modal aislado: gap simple (1 rango sin cobertura)
  2 - Modal aislado: gaps múltiples (2 rangos sin cobertura)
  3 - Flujo completo: inyecta gaps en la interfaz CTk y simula click en "Ejecutar"

Ejecutar desde la raiz del proyecto (Hoteles/):
    python -m tests.test_gaps_modal_visual
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Core.modelo_gaps import Gap, GapAnalysis


def _hacer_gap_analysis_simple():
    """Un solo gap: 01/10/2025 - 30/04/2026 (7 meses sin cobertura)."""
    from Models.periodo import Periodo

    p1 = Periodo(fecha_inicio=date(2025, 5, 1), fecha_fin=date(2025, 9, 30), nombre="Temporada Alta 2025")
    p2 = Periodo(fecha_inicio=date(2026, 5, 1), fecha_fin=date(2026, 9, 30), nombre="Temporada Alta 2026")

    return GapAnalysis(
        fecha_entrada=date(2025, 6, 11),
        fecha_salida=date(2026, 6, 11),
        periodos_aplicables=[p1, p2],
        gaps=[Gap(date(2025, 10, 1), date(2026, 4, 30))],
    )


def _hacer_gap_analysis_multiple():
    """Dos gaps: temporada baja sin cobertura en ambos años."""
    from Models.periodo import Periodo

    p1 = Periodo(fecha_inicio=date(2025, 7, 1), fecha_fin=date(2025, 8, 31), nombre="Alta 2025")
    p2 = Periodo(fecha_inicio=date(2026, 7, 1), fecha_fin=date(2026, 8, 31), nombre="Alta 2026")

    return GapAnalysis(
        fecha_entrada=date(2025, 6, 1),
        fecha_salida=date(2026, 9, 30),
        periodos_aplicables=[p1, p2],
        gaps=[
            Gap(date(2025, 6, 1), date(2025, 6, 30)),
            Gap(date(2025, 9, 1), date(2026, 6, 30)),
            Gap(date(2026, 9, 1), date(2026, 9, 30)),
        ],
    )


def test_modal_aislado(gap_analysis):
    """Abre el modal CTk directamente, sin la interfaz completa."""
    import customtkinter as ctk
    from UI.components.ctk_modal_advertencia_gaps import CtkModalAdvertenciaGaps

    root = ctk.CTk()
    root.geometry("600x400")
    root.title("Ventana padre (de fondo)")

    resultado = {"respuesta": None}

    def callback(confirmo):
        resultado["respuesta"] = confirmo
        estado = "CONFIRMÓ — ejecutaría comparación" if confirmo else "CANCELÓ"
        print(f"\nUsuario: {estado}")
        root.destroy()

    # Abrir modal después de que la ventana padre esté lista
    root.after(300, lambda: CtkModalAdvertenciaGaps(root, gap_analysis, callback))

    root.mainloop()
    return resultado["respuesta"]


def test_flujo_completo(gap_analysis):
    """
    Inyecta el gap_analysis en la interfaz CTk completa y simula
    que el usuario clickea 'Ejecutar Comparación' con gaps sin confirmar.

    Resultado esperado:
    - El panel de precios muestra el banner amarillo de advertencia
    - Al simular 'ejecutar', aparece el modal de gaps
    """
    import customtkinter as ctk
    from UI.interfaz_ctk import CrawlCompareGUI

    root = ctk.CTk()
    app = CrawlCompareGUI(root)

    def _inyectar():
        # Simular que ya hay precios calculados con gaps
        app.state.gap_analysis_actual = gap_analysis
        app.state.gap_confirmado = False

        # Armar precios_data falsos para que el panel muestre algo
        from Models.periodo import Periodo
        precios_data = [
            {
                "periodo": gap_analysis.periodos_aplicables[0],
                "precio": 250.00,
                "nombre_grupo": "Temporada Alta 2025",
            }
        ]
        if len(gap_analysis.periodos_aplicables) > 1:
            precios_data.append({
                "periodo": gap_analysis.periodos_aplicables[1],
                "precio": 280.00,
                "nombre_grupo": "Temporada Alta 2026",
            })

        # Mostrar precios con banner de gaps en el panel
        app.precio_panel.mostrar_precios_multiples(precios_data, gap_analysis)

        print("\nGaps inyectados. El panel debería mostrar el banner amarillo.")
        print("Ahora disparando evento 'mostrar_modal_gaps' para simular click en Ejecutar...\n")

        # Simular que el controlador dispara el modal (como si el usuario hubiera clickeado Ejecutar)
        root.after(800, lambda: app.event_bus.emit("mostrar_modal_gaps", {"gap_analysis": gap_analysis}))

    root.after(500, _inyectar)
    root.mainloop()


def main():
    print("=== Test Visual: Modal de Gaps ===\n")
    print("Escenarios:")
    print("  1 - Modal aislado: gap simple (1 rango)")
    print("  2 - Modal aislado: gaps múltiples (3 rangos)")
    print("  3 - Flujo completo en la interfaz CTk (gap simple)")
    print("  4 - Flujo completo en la interfaz CTk (gaps múltiples)")
    opcion = input("\nElegir [1/2/3/4, Enter=1]: ").strip() or "1"

    if opcion == "1":
        test_modal_aislado(_hacer_gap_analysis_simple())
    elif opcion == "2":
        test_modal_aislado(_hacer_gap_analysis_multiple())
    elif opcion == "3":
        test_flujo_completo(_hacer_gap_analysis_simple())
    elif opcion == "4":
        test_flujo_completo(_hacer_gap_analysis_multiple())
    else:
        print("Opción inválida.")


if __name__ == "__main__":
    main()
