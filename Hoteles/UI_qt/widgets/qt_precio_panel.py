"""Panel de precio con desglose multiperiodo (spec aprobada en Figma).

Reemplaza CTkPrecioPanel. Modos:
- Mensaje simple (sin seleccion / sin fechas).
- Precio: monto o rango grande + desglose por periodo mostrando el TRAMO de la
  reserva que cae en cada periodo (interseccion reserva∩periodo) y su precio.
- Banner de advertencia si hay gaps de cobertura.

API compatible con el handler de eventos: mostrar_precios_multiples(precios_data, gap_analysis)
y mostrar_mensaje(texto). precios_data = lista de {periodo, precio, nombre_grupo}.
"""

from datetime import datetime, date

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget,
)
from PySide6.QtCore import Qt


def _fmt_money(v):
    if isinstance(v, (int, float)):
        return f"${v:,.2f}"
    if v is None:
        return "—"
    return str(v)


def _parse_fecha(s):
    """Parsea 'DD-MM-AAAA' a date, o None."""
    try:
        return datetime.strptime(s, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None


class QtPrecioPanel(QFrame):
    """Panel de precio estimado + desglose multiperiodo."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.state = state

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(10)

        self._title = QLabel("PRECIO ESTIMADO")
        self._title.setObjectName("sectionLabel")
        outer.addWidget(self._title)

        # Area scrollable para el contenido variable
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self._scroll, stretch=1)

        self._body = QWidget()
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(8)
        self._body_lay.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._body)

        self.mostrar_mensaje("Seleccioná un hotel y habitación para ver el precio estimado")

    # ---- API publica ----
    def mostrar_mensaje(self, mensaje):
        self._title.setText("PRECIO ESTIMADO")
        self._clear_body()
        self._body_lay.addStretch()
        lbl = QLabel(mensaje)
        lbl.setObjectName("mutedLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        self._body_lay.addWidget(lbl)
        self._body_lay.addStretch()

    def limpiar(self):
        self.mostrar_mensaje("Seleccioná un hotel y habitación para ver el precio estimado")

    def mostrar_precios_multiples(self, precios_data, gap_analysis=None):
        self._clear_body()
        if not precios_data:
            self.mostrar_mensaje("(Ingrese fechas para ver precios)")
            return

        entrada = _parse_fecha(self.state.fecha_entrada_completa.get())
        salida = _parse_fecha(self.state.fecha_salida_completa.get())

        # Monto destacado: valor unico o rango
        numericos = [p['precio'] for p in precios_data if isinstance(p['precio'], (int, float))]
        if numericos:
            mn, mx = min(numericos), max(numericos)
            if mn == mx:
                self._title.setText("PRECIO ESTIMADO")
                monto = _fmt_money(mn)
            else:
                self._title.setText("RANGO DE PRECIO")
                monto = f"{_fmt_money(mn)} – {_fmt_money(mx)}"
        else:
            self._title.setText("PRECIO ESTIMADO")
            monto = _fmt_money(precios_data[0]['precio'])
        val = QLabel(monto)
        val.setObjectName("priceValue")
        self._body_lay.addWidget(val)

        # Subtitulo: noches + rango + nº periodos
        if entrada and salida:
            noches = (salida - entrada).days
            n_per = len(precios_data)
            sufijo = f" · cruza {n_per} períodos" if n_per > 1 else ""
            sub = QLabel(f"{noches} noche(s) · {entrada:%d/%m/%Y} → {salida:%d/%m/%Y}{sufijo}")
            sub.setObjectName("mutedLabel")
            self._body_lay.addWidget(sub)

        # Desglose por periodo (solo si hay mas de uno, o siempre para claridad)
        if len(precios_data) >= 1:
            self._sep()
            hdr = QLabel("DESGLOSE POR PERÍODO")
            hdr.setObjectName("mutedLabel")
            self._body_lay.addWidget(hdr)
            for item in precios_data:
                self._fila_tramo(item, entrada, salida)

        if gap_analysis is not None and getattr(gap_analysis, "tiene_gaps", False):
            self._banner_gaps(gap_analysis)

    # ---- helpers ----
    def _fila_tramo(self, item, entrada, salida):
        periodo = item['periodo']
        precio = item['precio']
        nombre = item.get('nombre_grupo') or getattr(periodo, 'nombre', '') or "Período"

        row = QFrame()
        row.setObjectName("chipRow")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 8, 12, 8)
        rl.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(2)
        lbl_nombre = QLabel(nombre)
        lbl_nombre.setObjectName("fieldLabel")
        left.addWidget(lbl_nombre)
        # Tramo de la reserva dentro de este periodo (interseccion)
        tramo_txt = self._tramo_texto(periodo, entrada, salida)
        if tramo_txt:
            lbl_tramo = QLabel(tramo_txt)
            lbl_tramo.setObjectName("mutedLabel")
            left.addWidget(lbl_tramo)
        rl.addLayout(left)
        rl.addStretch()

        lbl_precio = QLabel(_fmt_money(precio))
        lbl_precio.setObjectName("accentValue")
        rl.addWidget(lbl_precio)

        self._body_lay.addWidget(row)

    def _tramo_texto(self, periodo, entrada, salida):
        """Texto del tramo de la reserva que cae dentro del periodo (interseccion)."""
        ini = getattr(periodo, 'fecha_inicio', None)
        fin = getattr(periodo, 'fecha_fin', None)
        if not (entrada and salida and isinstance(ini, date) and isinstance(fin, date)):
            return None
        t_ini = max(entrada, ini)
        t_fin = min(salida, fin)
        if t_ini >= t_fin:
            return None
        noches = (t_fin - t_ini).days
        return f"Tu tramo: {t_ini:%d/%m} → {t_fin:%d/%m} ({noches} noche(s))"

    def _banner_gaps(self, gap_analysis):
        banner = QFrame()
        banner.setStyleSheet(
            "QFrame { background-color: #FFF3CD; border: 1px solid #FFCA28; border-radius: 8px; }"
        )
        bl = QVBoxLayout(banner)
        bl.setContentsMargins(10, 8, 10, 8)
        bl.setSpacing(2)
        t = QLabel("⚠  Cobertura parcial — hay fechas sin precio Excel")
        t.setStyleSheet("color:#856404; font-weight:bold; background:transparent; border:none;")
        bl.addWidget(t)
        try:
            desc = gap_analysis.get_gap_description()
            d = QLabel(desc)
            d.setStyleSheet("color:#856404; background:transparent; border:none;")
            d.setWordWrap(True)
            bl.addWidget(d)
        except Exception:
            pass
        self._body_lay.addWidget(banner)

    def _sep(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(128,128,128,0.25); border: none;")
        self._body_lay.addWidget(line)

    def _clear_body(self):
        while self._body_lay.count():
            it = self._body_lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
            else:
                lay = it.layout()
                if lay is not None:
                    self._clear_layout(lay)

    def _clear_layout(self, lay):
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
