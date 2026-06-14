"""Modal de configuracion (QDialog + QTabWidget). Porta ConfigModal.

4 pestañas: General (info Excel), Email (firma + template editable con validacion),
API Keys y Scraping (placeholders). El editor de template usa un QTextEdit plano
(sin los chips clicables ni autocomplete inline del original; las variables se tipean
a mano). La validacion del template se reutiliza intacta del modal CTk.
"""

import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget,
    QTextEdit, QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from Core.email_templates import DEFAULT_EMAIL_TEMPLATE
from Core.services.config_service import ConfigService

_VARS_GLOBALES = {"hotel", "habitacion_excel", "habitacion_web", "firma"}
_VARS_PERIODO = {
    "periodo_id", "fecha_inicio_periodo", "fecha_fin_periodo",
    "fecha_inicio_busqueda", "fecha_fin_busqueda",
    "precio_excel", "precio_web", "diferencia", "estado",
}
_TAG_FOR = "{% for periodo %}"
_TAG_END = "{% end %}"


class QtConfigModal(QDialog):
    """Modal de configuracion con pestañas."""

    def __init__(self, parent, excel_path: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.resize(620, 560)
        self.setModal(True)
        self._config = ConfigService()
        self._excel_path = excel_path

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        lay.addWidget(self.tabs)

        self.tabs.addTab(self._tab_general(), "General")
        self.tabs.addTab(self._tab_email(), "Email")
        self.tabs.addTab(self._tab_placeholder("Próximamente: GROQ_API_KEY"), "API Keys")
        self.tabs.addTab(self._tab_placeholder("Próximamente: delays, timeouts, modo headless."), "Scraping")

    def _tab_general(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setAlignment(Qt.AlignTop)
        t = QLabel("Archivo Excel actual"); t.setObjectName("cardTitle"); v.addWidget(t)
        lbl = QLabel(self._excel_path if self._excel_path else "No hay archivo Excel cargado.")
        lbl.setObjectName("mutedLabel"); lbl.setWordWrap(True); v.addWidget(lbl)
        hint = QLabel('Para cambiar el archivo, cerrá este modal y usá el botón "Cambiar" de la barra superior.')
        hint.setObjectName("mutedLabel"); hint.setWordWrap(True); v.addWidget(hint)
        return w

    def _tab_placeholder(self, mensaje):
        w = QWidget()
        v = QVBoxLayout(w)
        lbl = QLabel(mensaje)
        lbl.setObjectName("mutedLabel"); lbl.setWordWrap(True); lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(lbl)
        return w

    def _tab_email(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)

        v.addWidget(self._lbl("Firma"))
        self._firma = QTextEdit()
        self._firma.setFixedHeight(70)
        self._firma.setPlainText(self._config.get_email_firma() or "")
        v.addWidget(self._firma)

        v.addWidget(self._lbl("Template del email"))
        hint = QLabel("Variables: {hotel}, {habitacion_excel}, {habitacion_web}, {firma} (globales) · "
                      "dentro de {% for periodo %}...{% end %}: {precio_excel}, {precio_web}, {diferencia}, {estado}, etc.")
        hint.setObjectName("mutedLabel"); hint.setWordWrap(True); v.addWidget(hint)

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
        btns.addStretch()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("btnPrimary")
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
