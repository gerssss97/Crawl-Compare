"""Modal de configuracion (QDialog + QTabWidget). Porta ConfigModal.

3 pestañas: General (info Excel), Email (firma + template editable con validacion),
Historial (TTL de retención). El editor de template usa un QTextEdit plano
(sin los chips clicables ni autocomplete inline del original; las variables se tipean
a mano). La validacion del template se reutiliza intacta del modal CTk.
"""

import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTabWidget, QWidget,
    QTextEdit, QPushButton, QMessageBox, QTextBrowser, QComboBox, QLayout, QCheckBox,
)
from UI_qt.widgets.qt_spin_stepper import QtSpinStepper
from PySide6.QtCore import Qt, QRect, QPoint, QSize

from Core.email_templates import DEFAULT_EMAIL_TEMPLATE
from Core.services.config_service import ConfigService
from Core.services.email_senders import _PROVIDER_KEYS

_PROVIDER_LABELS = [
    "Cliente predeterminado del sistema",
    "Gmail (en el navegador)",
    "Outlook Web (en el navegador)",
    "Solo copiar al portapapeles",
]

_VARS_GLOBALES = {"hotel", "habitacion_excel", "habitacion_web", "firma"}
_VARS_PERIODO = {
    "periodo_id", "fecha_inicio_periodo", "fecha_fin_periodo",
    "fecha_inicio_busqueda", "fecha_fin_busqueda",
    "precio_excel", "precio_web", "diferencia", "estado",
}
_TAG_FOR = "{% for periodo %}"
_TAG_END = "{% end %}"


class _FlowLayout(QLayout):
    """QLayout que distribuye widgets en filas que wrappean automáticamente."""

    def __init__(self, parent=None, h_spacing=6, v_spacing=4):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []

    def addItem(self, item): self._items.append(item)
    def count(self): return len(self._items)
    def itemAt(self, i): return self._items[i] if 0 <= i < len(self._items) else None
    def takeAt(self, i): return self._items.pop(i) if 0 <= i < len(self._items) else None
    def expandingDirections(self): return Qt.Orientation(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, w): return self._layout(QRect(0, 0, w, 0), dry=True)
    def setGeometry(self, rect): super().setGeometry(rect); self._layout(rect, dry=False)
    def sizeHint(self): return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for item in self._items:
            s = s.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return s + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _layout(self, rect, dry):
        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, line_h = r.x(), r.y(), 0
        for item in self._items:
            w, h = item.sizeHint().width(), item.sizeHint().height()
            next_x = x + w + self._h_spacing
            if next_x - self._h_spacing > r.right() and line_h > 0:
                x = r.x()
                y += line_h + self._v_spacing
                next_x = x + w + self._h_spacing
                line_h = 0
            if not dry:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_h = max(line_h, h)
        return y + line_h - rect.y() + m.bottom()


class QtConfigModal(QDialog):
    """Modal de configuracion con pestañas."""

    def __init__(self, parent, excel_path: str | None = None, on_excel_changed=None,
                 on_periodos_setting_changed=None, config_service: ConfigService | None = None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.resize(620, 560)
        self.setModal(True)
        self._config = config_service if config_service is not None else ConfigService()
        self._excel_path = excel_path
        self._on_excel_changed = on_excel_changed
        self._on_periodos_setting_changed = on_periodos_setting_changed

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        lay.addWidget(self.tabs)

        self.tabs.addTab(self._tab_general(), "General")
        self.tabs.addTab(self._tab_email(), "Email")
        self.tabs.addTab(self._tab_historial(), "Historial")

    def _tab_general(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignTop)

        t = QLabel("Archivo Excel actual")
        t.setObjectName("cardTitle")
        v.addWidget(t)

        self._lbl_excel_path = QLabel(
            self._excel_path if self._excel_path else "No hay archivo Excel cargado."
        )
        self._lbl_excel_path.setWordWrap(True)
        v.addWidget(self._lbl_excel_path)

        btn_row = QHBoxLayout()
        btn_cambiar = QPushButton("Cambiar archivo Excel")
        btn_cambiar.setObjectName("btnPrimarySmall")
        btn_cambiar.clicked.connect(self._cambiar_excel_modal)
        btn_row.addWidget(btn_cambiar)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._chk_vencidos = QCheckBox("Ocultar períodos con fechas vencidas")
        self._chk_vencidos.setChecked(self._config.get_ocultar_periodos_vencidos())
        self._chk_vencidos.stateChanged.connect(self._on_ocultar_vencidos_changed)
        v.addWidget(self._chk_vencidos)

        return w

    def _on_ocultar_vencidos_changed(self, _):
        self._config.set_ocultar_periodos_vencidos(self._chk_vencidos.isChecked())
        if self._on_periodos_setting_changed:
            self._on_periodos_setting_changed()

    def _cambiar_excel_modal(self):
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog
        current = self._excel_path
        initialdir = str(Path(current).parent) if current else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", initialdir,
            "Archivos Excel (*.xlsx *.xls);;Todos los archivos (*.*)",
        )
        if not path:
            return
        if self._on_excel_changed:
            try:
                self._on_excel_changed(path)
                self._excel_path = path
                self._lbl_excel_path.setText(path)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error al cargar Excel",
                    f"No se pudo cargar el archivo:\n{path}\n\nDetalle: {e}",
                )

    def _tab_historial(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setAlignment(Qt.AlignTop)

        v.addWidget(self._lbl("Días de retención del historial"))
        hint_ttl = QLabel(
            "Las comparaciones más antiguas que este valor se eliminan automáticamente."
        )
        hint_ttl.setObjectName("mutedLabel"); hint_ttl.setWordWrap(True); v.addWidget(hint_ttl)
        self._ttl_spin = QtSpinStepper(
            min_val=1, max_val=365,
            default=self._config.get_historial_ttl_dias(),
            step=1,
        )
        v.addWidget(self._ttl_spin)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("btnPrimarySmall")
        btn_guardar.clicked.connect(self._guardar_historial_cfg)
        btns.addWidget(btn_guardar)
        v.addLayout(btns)
        return w

    def _guardar_historial_cfg(self):
        self._config.set_historial_ttl_dias(self._ttl_spin.value())
        QMessageBox.information(self, "Guardado", "Configuración del historial guardada.")

    def _tab_email(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)

        v.addWidget(self._lbl("Cliente de email"))
        self._provider = QComboBox()
        self._provider.addItems(_PROVIDER_LABELS)
        current = self._config.get_email_provider()
        idx = _PROVIDER_KEYS.index(current) if current in _PROVIDER_KEYS else 0
        self._provider.setCurrentIndex(idx)
        v.addWidget(self._provider)

        v.addWidget(self._lbl("Firma"))
        self._firma = QTextEdit()
        self._firma.setFixedHeight(48)
        self._firma.setPlainText(self._config.get_email_firma() or "")
        v.addWidget(self._firma)

        v.addWidget(self._lbl("Template del email"))
        v.addWidget(self._vars_chips())

        self._template = QTextEdit()
        self._template.setPlainText(self._config.get_email_template() or DEFAULT_EMAIL_TEMPLATE)
        v.addWidget(self._template, stretch=1)

        tip = QLabel("Tip: dejá el área vacía para usar el template predeterminado del sistema.")
        tip.setObjectName("mutedLabel"); v.addWidget(tip)

        btns = QHBoxLayout()
        btn_rest = QPushButton("Restaurar predeterminado")
        btn_rest.setObjectName("btnSecondary")
        btn_rest.clicked.connect(self._restaurar_template)
        btns.addWidget(btn_rest)
        btn_preview = QPushButton("Vista previa")
        btn_preview.setObjectName("btnSecondary")
        btn_preview.clicked.connect(self._mostrar_preview)
        btns.addWidget(btn_preview)
        btns.addStretch()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("btnPrimarySmall")
        btn_guardar.clicked.connect(self._guardar_email)
        btns.addWidget(btn_guardar)
        v.addLayout(btns)
        return w

    def _lbl(self, texto):
        l = QLabel(texto); l.setObjectName("fieldLabel"); return l

    # ---- validacion (portada del original) ----
    def _validar_template(self, template):
        count_for = template.count(_TAG_FOR)
        count_end = template.count(_TAG_END)
        if count_for != count_end or count_for > 1:
            return ("Bloque mal formado: cada '{% for periodo %}' necesita exactamente un "
                    "'{% end %}', y solo puede haber un bloque.")
        tiene_bloque = count_for == 1
        if tiene_bloque:
            exterior = template.replace(template.split(_TAG_FOR)[1].split(_TAG_END)[0], "")
            exterior = exterior.replace(_TAG_FOR, "").replace(_TAG_END, "")
        else:
            exterior = template
        fuera = set(re.findall(r"\{(\w+)\}", exterior)) & _VARS_PERIODO
        if fuera:
            lista = ", ".join(f"{{{v}}}" for v in sorted(fuera))
            return (f"Las siguientes variables solo pueden usarse dentro del bloque "
                    f"{{% for periodo %}}...{{% end %}}:\n{lista}")
        todos = set(re.findall(r"\{(\w+)\}", template))
        desconocidas = todos - _VARS_GLOBALES - _VARS_PERIODO
        if desconocidas:
            lista = ", ".join(f"{{{v}}}" for v in sorted(desconocidas))
            return f"Variable(s) desconocida(s): {lista}\nCorregí el nombre antes de guardar."
        return None

    def _guardar_email(self):
        firma = self._firma.toPlainText().strip()
        template = self._template.toPlainText().strip()
        if template:
            error = self._validar_template(template)
            if error:
                QMessageBox.critical(self, "Error en el template", error)
                return
        self._config.set_email_firma(firma or None)
        self._config.set_email_template(template or None)
        self._config.set_email_provider(_PROVIDER_KEYS[self._provider.currentIndex()])
        QMessageBox.information(self, "Guardado", "Configuración de email guardada.")

    def _restaurar_template(self):
        resp = QMessageBox.question(
            self, "Restaurar",
            "¿Restaurar el template predeterminado?\nSe perderá el template actual.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self._template.setPlainText(DEFAULT_EMAIL_TEMPLATE)
            self._config.set_email_template(None)

    def _vars_chips(self):
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        grid.setColumnStretch(1, 1)

        lbl_glob = QLabel("Globales:")
        lbl_glob.setAlignment(Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(lbl_glob, 0, 0)
        glob_w = QWidget()
        glob_lay = _FlowLayout(glob_w, h_spacing=4, v_spacing=2)
        glob_lay.setContentsMargins(0, 0, 0, 0)
        for var in ["hotel", "habitacion_excel", "habitacion_web", "firma"]:
            glob_lay.addWidget(self._chip(var))
        grid.addWidget(glob_w, 0, 1)

        lbl_per = QLabel("En bloque for:")
        lbl_per.setAlignment(Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(lbl_per, 1, 0)
        per_w = QWidget()
        per_lay = _FlowLayout(per_w, h_spacing=4, v_spacing=2)
        per_lay.setContentsMargins(0, 0, 0, 0)
        for var in ["periodo_id", "fecha_inicio_periodo", "fecha_fin_periodo",
                    "fecha_inicio_busqueda", "fecha_fin_busqueda",
                    "precio_excel", "precio_web", "diferencia", "estado"]:
            per_lay.addWidget(self._chip(var))
        grid.addWidget(per_w, 1, 1)

        return container

    def _chip(self, var_name):
        btn = QPushButton(f"{{{var_name}}}")
        btn.setObjectName("varChip")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _, v=var_name: self._template.insertPlainText(f"{{{v}}}"))
        return btn

    # ---- vista previa ----

    _MOCK_DATA = {
        "hotel": "Hotel Las Leñas",
        "habitacion_excel": "Suite Superior (2 adultos)",
        "habitacion_web": "Superior Suite - 2 pax",
        # "firma" se completa en runtime con el valor actual del campo self._firma
        "periodos": [
            {
                "periodo_id": "1",
                "fecha_inicio_periodo": "2026-07-01",
                "fecha_fin_periodo": "2026-07-15",
                "fecha_inicio_busqueda": "2026-07-03",
                "fecha_fin_busqueda": "2026-07-10",
                "precio_excel": "$45.000",
                "precio_web": "$52.300",
                "diferencia": "$7.300",
                "estado": "⚠ Discrepancia",
            },
            {
                "periodo_id": "2",
                "fecha_inicio_periodo": "2026-07-16",
                "fecha_fin_periodo": "2026-07-31",
                "fecha_inicio_busqueda": "2026-07-18",
                "fecha_fin_busqueda": "2026-07-28",
                "precio_excel": "$48.000",
                "precio_web": "$48.000",
                "diferencia": "$0",
                "estado": "✓ OK",
            },
        ],
    }

    def _render_preview(self, template: str, mock_data: dict) -> str:
        """Renderiza el template con datos de muestra.

        Lógica:
        1. Encuentra el bloque {% for periodo %}...{% end %} con regex.
        2. Por cada dict en mock_data["periodos"] sustituye las variables del bloque.
        3. Une todas las iteraciones y reemplaza el bloque original.
        4. Sustituye las variables globales en el texto restante.

        Retorna el texto renderizado, o un mensaje de error si algo falla.
        """
        if not template.strip():
            return "(el template está vacío)"

        try:
            bloque_re = re.compile(
                r"\{%\s*for periodo\s*%\}(.*?)\{%\s*end\s*%\}",
                re.DOTALL,
            )
            match = bloque_re.search(template)

            if match:
                cuerpo_bloque = match.group(1)
                iteraciones = []
                for periodo in mock_data.get("periodos", []):
                    iteracion = cuerpo_bloque
                    for key, val in periodo.items():
                        iteracion = iteracion.replace(f"{{{key}}}", str(val))
                    iteraciones.append(iteracion)
                bloque_renderizado = "".join(iteraciones)
                resultado = bloque_re.sub(bloque_renderizado, template)
            else:
                resultado = template

            # sustituye variables globales (firma se toma del campo actual)
            globales = {k: v for k, v in mock_data.items() if k != "periodos"}
            for key, val in globales.items():
                resultado = resultado.replace(f"{{{key}}}", str(val))

            return resultado

        except Exception as exc:
            return f"[Error al renderizar el template: {exc}]"

    def _mostrar_preview(self):
        """Construye el QDialog de vista previa y lo muestra."""
        template = self._template.toPlainText()

        mock = dict(self._MOCK_DATA)
        mock["firma"] = self._firma.toPlainText().strip() or "(sin firma)"

        resultado = self._render_preview(template, mock)

        dlg = QDialog(self)
        dlg.setWindowTitle("Vista previa del email")
        dlg.resize(600, 500)
        dlg.setModal(True)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        browser = QTextBrowser()
        browser.setPlainText(resultado)
        lay.addWidget(browser, stretch=1)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecondary")
        btn_cerrar.clicked.connect(dlg.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_cerrar)
        lay.addLayout(btn_row)

        dlg.exec()
