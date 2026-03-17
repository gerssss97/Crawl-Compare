"""Test visual: abre el modal de envio de email con datos de prueba."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date
import customtkinter as ctk

from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo, ResultadoPeriodo
from Models.hotelExcel import Periodo
from Models.hotelWeb import HabitacionWeb
from UI.interfaz_ctk import CrawlCompareGUI


def _hacer_resultado_fake():
    periodo = Periodo(
        nombre="Temporada Alta",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 30),
        precio=1000.0,
    )
    rp = ResultadoPeriodo(
        periodo=periodo,
        precio_excel=1000.0,
        precio_web=1862.0,
        diferencia=862.0,
        coincide=False,
        fecha_inicio_real=date(2026, 6, 5),
        fecha_fin_real=date(2026, 6, 30),
    )
    hab_web = HabitacionWeb(nombre="Suite Diplomatic Prestige", detalles="Habitacion completa", combos=[])
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="dbl/sgl suite king palace w/bb",
        habitacion_web_matcheada=hab_web,
        periodos=[rp],
        tiene_discrepancias=True,
        mensaje_match="Habitacion completa",
    )


def main():
    root = ctk.CTk()
    root.withdraw()  # ocultar ventana principal

    app = CrawlCompareGUI(root)

    # Inyectar datos de prueba en el state
    app.state.hotel.set("Palacio Duhau - Park Hyatt Buenos Aires")
    app.state.habitacion.set("dbl/sgl suite king palace w/bb")
    resultado = _hacer_resultado_fake()
    app.state.resultado_multiperiodo = resultado

    # Simular los periodos/precios que calcularía ControladorPrecios
    rp = resultado.periodos[0]
    app.state.periodos_precio = [
        {
            "periodo": rp.periodo,
            "precio": rp.precio_excel,
            "nombre_grupo": rp.periodo.nombre,
        }
    ]

    # Abrir modal directamente
    app._abrir_ventana_email()

    # Cuando se cierre el modal, salir
    root.mainloop()


if __name__ == "__main__":
    main()
