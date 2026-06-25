#!/usr/bin/env python
"""
multiperiodo_test.py - Test multi-periodo con datos fake o scraping real (PySide6)

Uso:
    python multiperiodo_test.py [--modo fake|real] [--hotel HOTEL] [--habitacion HAB]

Ejemplos:
    python multiperiodo_test.py
    python multiperiodo_test.py --modo fake --hotel "Alvear Palace" --habitacion "dbl superior"
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Agregar Hoteles/ al path
hoteles_dir = Path(__file__).parent.parent.parent.parent / "Hoteles"
sys.path.insert(0, str(hoteles_dir))
os.chdir(str(hoteles_dir))

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton, QScrollArea,
    QWidget, QMessageBox, QTextEdit,
)
from PySide6.QtCore import Qt

from Core.controller import dar_hoteles_excel, generar_texto_email_multiperiodo
from Core.comparador_multiperiodo import ResultadoComparacionMultiperiodo, ResultadoPeriodo
from Core.servicio_habitaciones import unificar_habitaciones
from Models.hotelWeb import HabitacionWeb, ComboPrecio
from UI_qt.widgets.qt_vista_resultados import QtVistaResultados


class MultiperiodoTestDialog(QDialog):
    """Formulario PySide6 para inventar datos web por periodo."""

    def __init__(self, habitacion_unificada, hotel, periodos_aplicables, parent=None):
        super().__init__(parent)
        self.habitacion_unificada = habitacion_unificada
        self.hotel = hotel
        self.periodos_aplicables = periodos_aplicables
        self.resultado = None

        self.setWindowTitle("Test Multi-Periodo — Inventar Datos Web")
        self.resize(560, 420)

        self._precio_inputs = {}  # {periodo.id: QDoubleSpinBox}
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 16, 20, 16)

        titulo = QLabel(f"Habitación: {self.habitacion_unificada.nombre}")
        titulo.setStyleSheet("font-weight: bold; font-size: 14px;")
        lay.addWidget(titulo)

        lay.addWidget(QLabel(f"Periodos aplicables: {len(self.periodos_aplicables)}"))

        # Nombre habitación web
        nombre_form = QFormLayout()
        self._nombre_input = QLineEdit("Double Superior Room with Breakfast")
        nombre_form.addRow("Habitación Web:", self._nombre_input)
        lay.addLayout(nombre_form)

        # Scroll con un QDoubleSpinBox por periodo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)
        form.setSpacing(6)

        for periodo in self.periodos_aplicables:
            nombre = periodo.nombre or f"Periodo {periodo.id}"
            label = f"{nombre} ({periodo.fecha_inicio.strftime('%d/%m')}–{periodo.fecha_fin.strftime('%d/%m')})"
            spin = QDoubleSpinBox()
            spin.setRange(0, 99999)
            spin.setValue(150.0)
            spin.setPrefix("$ ")
            spin.setDecimals(2)
            self._precio_inputs[periodo.id] = spin
            form.addRow(label, spin)

        scroll.setWidget(container)
        lay.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton("Generar Comparación")
        btn.setDefault(True)
        btn.clicked.connect(self._generar)
        btn_row.addWidget(btn)
        lay.addLayout(btn_row)

    def _generar(self):
        nombre_web = self._nombre_input.text().strip()
        if not nombre_web:
            QMessageBox.warning(self, "Error", "Ingresá un nombre para la habitación web.")
            return

        combos = []
        for periodo in self.periodos_aplicables:
            precio = self._precio_inputs[periodo.id].value()
            nombre = periodo.nombre or f"Periodo {periodo.id}"
            combos.append(ComboPrecio(
                titulo=nombre_web,
                descripcion=f"Inventado para testing - {nombre}",
                precio=precio,
            ))

        habitacion_web = HabitacionWeb(
            nombre=nombre_web,
            detalles="Habitación inventada para testing multi-periodo",
            combos=combos,
        )

        try:
            resultados_periodos = []
            tiene_discrepancias = False

            for periodo in self.periodos_aplicables:
                precio_excel = self.habitacion_unificada.precio_para_periodo(periodo.id)
                nombre = periodo.nombre or f"Periodo {periodo.id}"
                combo = next((c for c in combos if nombre in c.descripcion), None)
                precio_web = combo.precio if combo else 0.0

                if isinstance(precio_excel, (int, float)):
                    diferencia = precio_web - precio_excel
                    coincide = abs(diferencia) < 1.0
                else:
                    diferencia = 0.0
                    coincide = True

                if not coincide:
                    tiene_discrepancias = True

                resultados_periodos.append(ResultadoPeriodo(
                    periodo=periodo,
                    precio_excel=precio_excel,
                    precio_web=precio_web,
                    diferencia=diferencia,
                    coincide=coincide,
                    fecha_inicio_real=periodo.fecha_inicio,
                    fecha_fin_real=periodo.fecha_fin,
                ))

            self.resultado = ResultadoComparacionMultiperiodo(
                habitacion_excel_nombre=self.habitacion_unificada.nombre,
                habitacion_web_matcheada=habitacion_web,
                periodos=resultados_periodos,
                tiene_discrepancias=tiene_discrepancias,
                mensaje_match=f"Match manual: {nombre_web}",
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error durante comparación:\n{e}")
            import traceback
            traceback.print_exc()


class ResultadosWindow(QWidget):
    """Ventana standalone con QtVistaResultados."""

    def __init__(self, resultado, email_text=None, parent=None):
        super().__init__(None, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Resultado Multi-Periodo (Test)")
        self.resize(780, 560)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        vista = QtVistaResultados()
        vista.mostrar_resultado_multiperiodo(resultado)
        lay.addWidget(vista, stretch=1)

        if email_text:
            btn = QPushButton("Mostrar email generado")
            btn.clicked.connect(lambda: self._mostrar_email(email_text))
            lay.addWidget(btn)

    def _mostrar_email(self, texto):
        dlg = QDialog(self)
        dlg.setWindowTitle("Email generado (NO enviado)")
        dlg.resize(700, 500)
        v = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(texto)
        v.addWidget(te)
        b = QPushButton("Cerrar")
        b.clicked.connect(dlg.accept)
        v.addWidget(b)
        dlg.exec()


def modo_fake(hotel_nombre, habitacion_nombre):
    print("\n🧪 Test Multi-Periodo — Modo FAKE\n")
    print("📂 Cargando datos de Excel...")
    hoteles_excel = dar_hoteles_excel()

    hotel = next((h for h in hoteles_excel if hotel_nombre.lower() in h.nombre.lower()), None)
    if not hotel:
        print(f"❌ No se encontró hotel '{hotel_nombre}'")
        print(f"Disponibles: {', '.join(h.nombre for h in hoteles_excel)}")
        sys.exit(1)
    print(f"✅ Hotel: {hotel.nombre}")

    todas_habitaciones = []
    for tipo in hotel.tipos:
        todas_habitaciones.extend(tipo.habitaciones)
    todas_habitaciones.extend(hotel.habitaciones_directas)

    habitaciones_unificadas = unificar_habitaciones(todas_habitaciones)
    habitacion_unificada = next(
        (h for h in habitaciones_unificadas if habitacion_nombre.lower() in h.nombre.lower()), None
    )
    if not habitacion_unificada:
        print(f"❌ No se encontró habitación '{habitacion_nombre}'")
        for h in habitaciones_unificadas[:20]:
            print(f"  - {h.nombre}")
        sys.exit(1)
    print(f"✅ Habitación: {habitacion_unificada.nombre}")

    todos_ids = habitacion_unificada.todos_los_periodos()
    periodos_aplicables = [hotel.periodo_por_id(pid) for pid in todos_ids if hotel.periodo_por_id(pid)]
    if not periodos_aplicables:
        print("❌ La habitación no tiene periodos asociados")
        sys.exit(1)
    print(f"✅ Periodos: {len(periodos_aplicables)}\n")

    app = QApplication.instance() or QApplication(sys.argv)

    dialog = MultiperiodoTestDialog(habitacion_unificada, hotel, periodos_aplicables)
    if dialog.exec() != QDialog.Accepted or not dialog.resultado:
        print("Cancelado.")
        return

    resultado = dialog.resultado

    email_text = generar_texto_email_multiperiodo(hotel, resultado)
    tmp_dir = Path(__file__).parent.parent.parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    email_file = tmp_dir / f"multiperiodo-test-email-{ts}.txt"
    email_file.write_text(email_text, encoding="utf-8")
    print(f"💾 Email guardado en: {email_file}")

    win = ResultadosWindow(resultado, email_text=email_text)
    win.show()
    app.exec()


def modo_real(hotel_nombre, habitacion_nombre):
    print("\n🧪 Test Multi-Periodo — Modo REAL\n")
    print("⚠️  Modo real no implementado todavía. Usá --modo fake por ahora.")


def main():
    parser = argparse.ArgumentParser(description="Test multi-periodo con datos fake o real")
    parser.add_argument("--modo", choices=["fake", "real"], default="fake")
    parser.add_argument("--hotel", default=None)
    parser.add_argument("--habitacion", default=None)
    args = parser.parse_args()

    modo_fake(args.hotel or "Alvear Palace", args.habitacion or "dbl superior") \
        if args.modo == "fake" else modo_real(args.hotel or "Alvear Palace", args.habitacion or "dbl superior")


if __name__ == "__main__":
    main()
