"""
Test visual: simula un error de scraping y muestra la interfaz CTk completa.

Ejecutar desde la raiz del proyecto:
    python -m Tests.test_error_ui_visual
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Models.periodo import Periodo
from Core.comparador_multiperiodo import ResultadoPeriodo, ResultadoComparacionMultiperiodo


def _hacer_periodo(fecha_inicio, fecha_fin):
    return Periodo(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, nombre="Test")


def resultado_solo_error():
    """Todos los periodos fallaron — habitacion_web_matcheada es None."""
    p1 = _hacer_periodo(date(2026, 6, 5), date(2026, 9, 5))
    rp1 = ResultadoPeriodo(
        periodo=p1,
        precio_excel="Error",
        precio_web=0.0,
        diferencia=0.0,
        coincide=False,
        fecha_inicio_real=date(2026, 6, 5),
        fecha_fin_real=date(2026, 9, 5),
        error_msg="No se pudieron obtener datos completos después de todos los reintentos",
        error_url="https://be.synxis.com/?adult=1&child=0&arrive=2026-06-05&depart=2026-09-05&chain=24447&hotel=6933&currency=USD&level=hotel&locale=en-US&productcurrency=USD&rooms=1&src=30",
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=None,
        periodos=[rp1],
        tiene_discrepancias=True,
    )


def resultado_mixto():
    """Un periodo OK y uno con error."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    p1 = _hacer_periodo(date(2026, 3, 1), date(2026, 5, 31))
    rp1 = ResultadoPeriodo(
        periodo=p1,
        precio_excel=450.00,
        precio_web=450.00,
        diferencia=0.0,
        coincide=True,
        fecha_inicio_real=date(2026, 3, 1),
        fecha_fin_real=date(2026, 5, 31),
    )

    p2 = _hacer_periodo(date(2026, 6, 1), date(2026, 9, 5))
    rp2 = ResultadoPeriodo(
        periodo=p2,
        precio_excel="Error",
        precio_web=0.0,
        diferencia=0.0,
        coincide=False,
        fecha_inicio_real=date(2026, 6, 1),
        fecha_fin_real=date(2026, 9, 5),
        error_msg="Fallaron todos los intentos de extracción: Failed on navigating ACS-GOTO: Page.goto: Timeout 30000ms exceeded.",
        error_url="https://be.synxis.com/?adult=1&child=0&arrive=2026-06-01&depart=2026-09-05&chain=24447&hotel=6933&currency=USD&level=hotel&locale=en-US&productcurrency=USD&rooms=1&src=30",
    )

    hab_web = HabitacionWeb(
        nombre="Diplomatic Suite",
        detalles="King bed, 85 sqm, city view",
        combos=[ComboPrecio(titulo="Room Only", descripcion="Standard room only rate", precio=450.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab_web,
        periodos=[rp1, rp2],
        tiene_discrepancias=True,
        mensaje_match="[Match exacto]",
    )


def main():
    import customtkinter as ctk
    from UI.interfaz_ctk import CrawlCompareGUI

    # Elegir escenario
    print("Escenarios disponibles:")
    print("  1 - Solo error (sin acceso a la web)")
    print("  2 - Mixto (un periodo OK + un periodo con error)")
    opcion = input("Elegir [1/2, Enter=1]: ").strip() or "1"

    if opcion == "2":
        resultado = resultado_mixto()
    else:
        resultado = resultado_solo_error()

    # Lanzar la app CTk completa
    root = ctk.CTk()
    app = CrawlCompareGUI(root)

    # Inyectar el resultado simulado después de que la ventana esté lista
    def _inyectar():
        app._on_comparison_completed(resultado)

    root.after(500, _inyectar)
    root.mainloop()


if __name__ == "__main__":
    main()
