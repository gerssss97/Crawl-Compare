"""Test visual Qt: simula resultados de comparacion y muestra el modal PySide6 completo.

Cubre error de scraping, mezcla OK+error, discrepancia y todo-coincide.
Sirve para verificar el layout del QtResultadosModal sin ejecutar una comparacion real.

Ejecutar desde Hoteles/:
    conda activate crawler
    python -m Tests.test_resultado_qt_visual
    python -m Tests.test_resultado_qt_visual 3   # 3=discrepancia directo
"""
import sys
import os
import datetime
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Models.periodo import Periodo
from Core.comparador_multiperiodo import ResultadoPeriodo, ResultadoComparacionMultiperiodo


# ---- Helpers ----

def _periodo(fecha_inicio, fecha_fin):
    return Periodo(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, nombre="Test")


def _url(fi, ff, adultos=1, ninos=0):
    from urllib.parse import urlencode
    params = {
        "adult": adultos, "child": ninos,
        "arrive": fi.strftime("%Y-%m-%d"), "depart": ff.strftime("%Y-%m-%d"),
        "chain": 24447, "hotel": 6933, "currency": "USD",
        "level": "hotel", "locale": "en-US",
        "productcurrency": "USD", "rooms": 1, "src": 30,
    }
    return "https://be.synxis.com/?" + urlencode(params)


# ---- Escenarios ----

def resultado_solo_error():
    """Todos los periodos fallaron — habitacion_web_matcheada es None."""
    p = _periodo(date(2026, 6, 5), date(2026, 9, 5))
    rp = ResultadoPeriodo(
        periodo=p,
        precio_excel="Error",
        precio_web=0.0,
        diferencia=0.0,
        coincide=False,
        fecha_inicio_real=date(2026, 6, 5),
        fecha_fin_real=date(2026, 9, 5),
        error_msg="No se pudieron obtener datos completos después de todos los reintentos",
        error_url="https://be.synxis.com/?adult=1&child=0&arrive=2026-06-05&depart=2026-09-05",
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=None,
        periodos=[rp],
        tiene_discrepancias=True,
    )


def resultado_mixto():
    """Un periodo OK y uno con error."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    fi1, ff1 = date(2026, 3, 1), date(2026, 5, 31)
    fi2, ff2 = date(2026, 6, 1), date(2026, 9, 5)

    rp1 = ResultadoPeriodo(
        periodo=_periodo(fi1, ff1), precio_excel=450.00, precio_web=450.00,
        diferencia=0.0, coincide=True,
        fecha_inicio_real=fi1, fecha_fin_real=ff1,
        url_visitada=_url(fi1, ff1),
    )
    rp2 = ResultadoPeriodo(
        periodo=_periodo(fi2, ff2), precio_excel="Error", precio_web=0.0,
        diferencia=0.0, coincide=False,
        fecha_inicio_real=fi2, fecha_fin_real=ff2,
        error_msg="Timeout 30000ms exceeded.",
        error_url=_url(fi2, ff2),
    )
    hab = HabitacionWeb(
        nombre="Diplomatic Suite",
        detalles="King bed, 85 sqm, city view",
        combos=[ComboPrecio(titulo="Room Only", descripcion="Standard rate", precio=450.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab,
        periodos=[rp1, rp2],
        tiene_discrepancias=True,
        mensaje_match="[Match exacto]",
    )


def resultado_discrepancia():
    """Dos periodos scrapeados OK, uno coincide y otro no."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    fi1, ff1 = date(2026, 6, 16), date(2026, 9, 30)
    fi2, ff2 = date(2026, 10, 1), date(2026, 10, 14)

    rp1 = ResultadoPeriodo(
        periodo=_periodo(fi1, ff1), precio_excel=1312.50, precio_web=1400.00,
        diferencia=87.50, coincide=False,
        fecha_inicio_real=fi1, fecha_fin_real=ff1,
        url_visitada=_url(fi1, ff1),
    )
    rp2 = ResultadoPeriodo(
        periodo=_periodo(fi2, ff2), precio_excel=1500.00, precio_web=2128.00,
        diferencia=628.00, coincide=False,
        fecha_inicio_real=fi2, fecha_fin_real=ff2,
        url_visitada=_url(fi2, ff2),
    )
    hab = HabitacionWeb(
        nombre="Suite Diplomatic Prestige",
        detalles="1 King bed. Sleeps 4. 80 sq m. 2 Marble bath.",
        combos=[ComboPrecio(titulo="Bed & Breakfast", descripcion="Breakfast at restaurant", precio=1400.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab,
        periodos=[rp1, rp2],
        tiene_discrepancias=True,
        mensaje_match="Se encontró un combo con 'breakfast'. Se muestran solo ese combo.",
    )


def resultado_todo_coincide():
    """Todos los periodos coinciden — sin botón de email."""
    from Models.hotelWeb import HabitacionWeb, ComboPrecio

    fi1, ff1 = date(2026, 3, 1), date(2026, 5, 31)
    fi2, ff2 = date(2026, 6, 1), date(2026, 9, 5)

    rp1 = ResultadoPeriodo(
        periodo=_periodo(fi1, ff1), precio_excel=450.00, precio_web=450.00,
        diferencia=0.0, coincide=True,
        fecha_inicio_real=fi1, fecha_fin_real=ff1,
        url_visitada=_url(fi1, ff1),
    )
    rp2 = ResultadoPeriodo(
        periodo=_periodo(fi2, ff2), precio_excel=620.00, precio_web=620.00,
        diferencia=0.0, coincide=True,
        fecha_inicio_real=fi2, fecha_fin_real=ff2,
        url_visitada=_url(fi2, ff2),
    )
    hab = HabitacionWeb(
        nombre="Diplomatic Suite",
        detalles="King bed, 85 sqm, city view",
        combos=[ComboPrecio(titulo="Bed & Breakfast", descripcion="Breakfast at restaurant", precio=620.00)],
    )
    return ResultadoComparacionMultiperiodo(
        habitacion_excel_nombre="sgl/dbl/tpl diplomatic suite w/breakfast served at restaurant. (2 ad + 1 ch 3-12 years old)",
        habitacion_web_matcheada=hab,
        periodos=[rp1, rp2],
        tiene_discrepancias=False,
        mensaje_match="[Match exacto]",
    )


ESCENARIOS = {
    "1": ("Solo error",                    resultado_solo_error),
    "2": ("Mixto OK + error",              resultado_mixto),
    "3": ("Discrepancia + URL consultada", resultado_discrepancia),
    "4": ("Todo coincide + URL",           resultado_todo_coincide),
}


# ---- Selector visual ----

def _elegir_escenario(app):
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

    elegido = [resultado_discrepancia]

    dlg = QDialog()
    dlg.setWindowTitle("Elegir escenario")
    dlg.setFixedWidth(320)
    lay = QVBoxLayout(dlg)
    lay.setSpacing(8)
    lay.setContentsMargins(24, 20, 24, 20)

    lay.addWidget(QLabel("<b>Elegir escenario de prueba</b>"))

    for key, (label, factory) in ESCENARIOS.items():
        btn = QPushButton(f"{key}. {label}")
        btn.setMinimumHeight(36)
        def _click(f=factory):
            elegido[0] = f
            dlg.accept()
        btn.clicked.connect(_click)
        lay.addWidget(btn)

    dlg.exec()
    return elegido[0]


# ---- Main ----

def main():
    from PySide6.QtWidgets import QApplication
    from UI_qt.interfaz_qt import MainWindow

    app = QApplication(sys.argv)

    if len(sys.argv) > 1:
        factory = ESCENARIOS.get(sys.argv[1].strip(), ("", resultado_discrepancia))[1]
        resultado = factory()
    else:
        resultado = _elegir_escenario(app)()

    win = MainWindow()
    win.show()

    def _inyectar():
        from UI_qt.views.qt_resultados_modal import QtResultadosModal

        fake_id = datetime.datetime.now().isoformat(timespec="microseconds")
        snapshot = {
            "hotel": "Hotel Test",
            "edificio": None,
            "habitacion": resultado.habitacion_excel_nombre[:50],
            "fecha_entrada": "16-06-2026",
            "fecha_salida": "14-10-2026",
            "adultos": 1,
            "ninos": 0,
            "periodos_precio": [
                {
                    "periodo": _periodo(date(2026, 6, 16), date(2026, 9, 30)),
                    "precio": 1312.50,
                    "nombre_grupo": "Temporada Alta",
                },
                {
                    "periodo": _periodo(date(2026, 10, 1), date(2026, 10, 14)),
                    "precio": 1500.00,
                    "nombre_grupo": "Temporada Media",
                },
            ],
        }

        modal = QtResultadosModal(
            parent=win,
            comparison_id=fake_id,
            snapshot=snapshot,
            bridge=win.bridge,
            historial_service=win.historial_service,
            offset=0,
            theme=win._theme,
        )
        modal.show()

        win.event_bus.emit("comparison_completed", {
            "comparison_id": fake_id,
            "resultado": resultado,
        })

    from PySide6.QtCore import QTimer
    QTimer.singleShot(400, _inyectar)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
