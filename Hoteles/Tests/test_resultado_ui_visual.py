"""
Test visual: simula resultados de comparacion y muestra el modal CTk completo.

Cubre error de scraping, mezcla OK+error, discrepancia y todo-coincide.
Sirve para verificar como se ve el resultado, incluyendo la "URL consultada"
(hipervinculo) que ahora viaja por periodo desde el scraper.

Ejecutar desde la raiz del proyecto:
    python -m Tests.test_resultado_ui_visual
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Models.periodo import Periodo
from Core.comparador_multiperiodo import ResultadoPeriodo, ResultadoComparacionMultiperiodo


def _hacer_periodo(fecha_inicio, fecha_fin):
    return Periodo(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, nombre="Test")


def _url_periodo(fecha_inicio, fecha_fin, adultos=1, ninos=0):
    """Reconstruye la URL como la arma el scraper, para simular url_visitada."""
    from urllib.parse import urlencode
    params = {
        "adult": adultos,
        "child": ninos,
        "arrive": fecha_inicio.strftime("%Y-%m-%d"),
        "depart": fecha_fin.strftime("%Y-%m-%d"),
        "chain": 24447,
        "hotel": 6933,
        "currency": "USD",
        "level": "hotel",
        "locale": "en-US",
        "productcurrency": "USD",
        "rooms": 1,
        "src": 30,
    }
    return "https://be.synxis.com/?" + urlencode(params)


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
        url_visitada=_url_periodo(date(2026, 3, 1), date(2026, 5, 31)),
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


def resultado_discrepancia():
    """Dos periodos scrapeados OK, uno coincide y otro no. Ambos con URL consultada."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    fi1, ff1 = date(2026, 3, 1), date(2026, 5, 31)
    p1 = _hacer_periodo(fi1, ff1)
    rp1 = ResultadoPeriodo(
        periodo=p1,
        precio_excel=450.00,
        precio_web=450.00,
        diferencia=0.0,
        coincide=True,
        fecha_inicio_real=fi1,
        fecha_fin_real=ff1,
        url_visitada=_url_periodo(fi1, ff1),
    )

    fi2, ff2 = date(2026, 6, 1), date(2026, 9, 5)
    p2 = _hacer_periodo(fi2, ff2)
    rp2 = ResultadoPeriodo(
        periodo=p2,
        precio_excel=620.00,
        precio_web=685.00,
        diferencia=65.00,
        coincide=False,
        fecha_inicio_real=fi2,
        fecha_fin_real=ff2,
        url_visitada=_url_periodo(fi2, ff2),
    )

    hab_web = HabitacionWeb(
        nombre="Diplomatic Suite",
        detalles="King bed, 85 sqm, city view",
        combos=[ComboPrecio(titulo="Bed & Breakfast", descripcion="Breakfast at restaurant", precio=685.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab_web,
        periodos=[rp1, rp2],
        tiene_discrepancias=True,
        mensaje_match="[Match exacto]",
    )


def resultado_todo_coincide():
    """Todos los periodos scrapeados OK y coinciden. URL consultada por periodo, sin boton de email."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    fi1, ff1 = date(2026, 3, 1), date(2026, 5, 31)
    p1 = _hacer_periodo(fi1, ff1)
    rp1 = ResultadoPeriodo(
        periodo=p1,
        precio_excel=450.00,
        precio_web=450.00,
        diferencia=0.0,
        coincide=True,
        fecha_inicio_real=fi1,
        fecha_fin_real=ff1,
        url_visitada=_url_periodo(fi1, ff1),
    )

    fi2, ff2 = date(2026, 6, 1), date(2026, 9, 5)
    p2 = _hacer_periodo(fi2, ff2)
    rp2 = ResultadoPeriodo(
        periodo=p2,
        precio_excel=620.00,
        precio_web=620.00,
        diferencia=0.0,
        coincide=True,
        fecha_inicio_real=fi2,
        fecha_fin_real=ff2,
        url_visitada=_url_periodo(fi2, ff2),
    )

    hab_web = HabitacionWeb(
        nombre="Diplomatic Suite",
        detalles="King bed, 85 sqm, city view",
        combos=[ComboPrecio(titulo="Bed & Breakfast", descripcion="Breakfast at restaurant", precio=620.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab_web,
        periodos=[rp1, rp2],
        tiene_discrepancias=False,
        mensaje_match="[Match exacto]",
    )


def _elegir_escenario_ui(ctk):
    """Muestra una ventana CTk con un boton por escenario. Devuelve la factory elegida."""
    escenarios = [
        ("Solo error",      resultado_solo_error),
        ("Mixto OK + error", resultado_mixto),
        ("Discrepancia + URL consultada", resultado_discrepancia),
        ("Todo coincide + URL consultada", resultado_todo_coincide),
    ]

    elegido = [resultado_discrepancia]  # default si cierran sin elegir

    selector = ctk.CTkToplevel()
    selector.title("Elegir escenario")
    selector.resizable(False, False)
    selector.grab_set()

    ctk.CTkLabel(
        selector,
        text="Elegir escenario de prueba",
        font=("Segoe UI", 14, "bold"),
    ).pack(padx=24, pady=(20, 12))

    for label, factory in escenarios:
        def _click(f=factory):
            elegido[0] = f
            selector.destroy()
        ctk.CTkButton(
            selector,
            text=label,
            width=280,
            command=_click,
        ).pack(padx=24, pady=6)

    ctk.CTkFrame(selector, height=12, fg_color="transparent").pack()

    selector.wait_window()
    return elegido[0]


def main():
    import datetime
    import customtkinter as ctk
    from UI.interfaz_ctk import CrawlCompareGUI
    from UI.views import ResultadosModal

    # Si se pasa argumento CLI se usa directo; sino abre el selector visual.
    escenarios_cli = {
        "1": resultado_solo_error,
        "2": resultado_mixto,
        "3": resultado_discrepancia,
        "4": resultado_todo_coincide,
    }
    if len(sys.argv) > 1:
        factory = escenarios_cli.get(sys.argv[1].strip(), resultado_discrepancia)
        resultado = factory()
    else:
        # Necesitamos la app CTk corriendo para poder mostrar el selector
        root = ctk.CTk()
        root.withdraw()
        factory = _elegir_escenario_ui(ctk)
        root.destroy()
        resultado = factory()

    # Lanzar la app CTk completa
    root = ctk.CTk()
    app = CrawlCompareGUI(root)

    # Inyectar el resultado simulado creando el modal directamente
    def _inyectar():
        fake_id = datetime.datetime.now().isoformat(timespec='microseconds')
        snapshot = {
            'hotel': 'Hotel Test',
            'edificio': None,
            'habitacion': resultado.habitacion_excel_nombre[:50],
            'fecha_entrada': '01-06-2026',
            'fecha_salida': '05-09-2026',
            'adultos': 1,
            'ninos': 0,
            'periodos_precio': [
                {
                    'periodo': _hacer_periodo(date(2026, 3, 1), date(2026, 5, 31)),
                    'precio': 450.00,
                    'nombre_grupo': 'Temporada Baja',
                },
                {
                    'periodo': _hacer_periodo(date(2026, 6, 1), date(2026, 9, 5)),
                    'precio': 620.00,
                    'nombre_grupo': 'Temporada Alta',
                },
            ],
        }
        ResultadosModal(
            parent=root,
            comparison_id=fake_id,
            snapshot=snapshot,
            event_bus=app.event_bus,
            fonts=app.fonts,
            historial_service=app.historial_service,
            offset=0,
        )
        # Emitir el evento con el nuevo contrato de payload
        app.event_bus.emit('comparison_completed', {
            'comparison_id': fake_id,
            'resultado': resultado,
        })

    root.after(500, _inyectar)
    root.mainloop()


if __name__ == "__main__":
    main()
