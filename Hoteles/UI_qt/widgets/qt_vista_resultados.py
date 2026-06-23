"""Vista de resultados de comparacion: QTextEdit readonly que renderiza HTML.

Reemplaza VistaResultados (tk.Text con tags). El render de tk.Text con tags
(bold, rojo, tabla monoespaciada, links) se mapea a HTML, que QTextEdit renderiza
nativamente preservando formato, colores, tabla con fuente mono y links clicables
(setOpenExternalLinks). Replica mostrar_resultado_multiperiodo de vista_resultados.py.
"""

import html as _html

from PySide6.QtWidgets import QTextBrowser


def _esc(s):
    return _html.escape(str(s))

def _url(s):
    """Escapa < > ' " pero NO & — Qt no decodifica &amp; en href antes de abrir el browser."""
    return _html.escape(str(s)).replace('&amp;', '&')


def _money(v):
    return f"${v:.2f}" if isinstance(v, (int, float)) else _esc(v)


class QtVistaResultados(QTextBrowser):
    """QTextBrowser de solo lectura que muestra el resultado multiperiodo en HTML.

    QTextBrowser (no QTextEdit) porque maneja links clicables nativamente y es
    read-only por diseño.
    """

    def __init__(self, parent=None, theme="light"):
        super().__init__(parent)
        self.setOpenExternalLinks(True)   # links clicables abren el navegador
        # Colores adaptados al tema (los demas -verde/rojo saturado- valen en ambos)
        self._theme = theme
        self._c_link = "#60A5FA" if theme == "dark" else "#0066CC"
        self._c_err = "#F87171" if theme == "dark" else "#CC0000"

    def actualizar_tema(self, theme: str) -> None:
        """Actualiza los colores hardcodeados y re-renderiza el contenido actual."""
        self._theme = theme
        self._c_link = "#60A5FA" if theme == "dark" else "#0066CC"
        self._c_err = "#F87171" if theme == "dark" else "#CC0000"
        # Re-renderizar con los nuevos colores si hay contenido
        html = self.toHtml()
        if html.strip():
            self.setHtml(html)

    def mostrar_error(self, error_msg: str):
        if "\nURL: " in error_msg:
            antes, url = error_msg.split("\nURL: ", 1)
            h = (f"<b>Error al acceder a la web:</b><br>{_esc(antes.strip())}<br><br>"
                 f"<b>URL intentada:</b><br>"
                 f"<a href='{_url(url.strip())}'>{_url(url.strip())}</a>")
        else:
            h = f"<b>Error:</b> {_esc(error_msg)}"
        self.setHtml(self._wrap(h))

    def mostrar_resultado_multiperiodo(self, resultado):
        """Renderiza el resultado en HTML (equivalente a la version tk.Text)."""
        p = []
        p.append("<h2 style='margin:0'>COMPARACIÓN MULTI-PERIODO</h2><hr>")

        p.append(f"<b>Habitación Excel:</b> {_esc(resultado.habitacion_excel_nombre)}<br>")
        if resultado.habitacion_web_matcheada:
            p.append(f"<b>Habitación Web:</b> {_esc(resultado.habitacion_web_matcheada.nombre)}<br>")
        else:
            p.append(f"<b>Habitación Web:</b> <span style='color:{self._c_err}'>(no se pudo acceder a la web)</span><br>")
        if resultado.mensaje_match:
            p.append(f"{_esc(resultado.mensaje_match)}<br>")

        # Estado global
        alguno_error = any(rp.precio_excel == "Error" for rp in resultado.periodos)
        if alguno_error:
            p.append(f"<b style='color:{self._c_err}'>Estado: ⚠ ERROR al acceder a la web</b><br>")
        elif resultado.tiene_discrepancias:
            p.append("<b>Estado: ❌ DISCREPANCIAS DETECTADAS</b><br>")
        else:
            p.append("<b style='color:#10B981'>Estado: ✅ TODO COINCIDE</b><br>")

        _c_border = "#888"
        _td = f"border:1px solid {_c_border}; padding:4px 8px"
        _th = f"{_td}; font-weight:bold; border-bottom:2px solid {_c_border}"

        # Tabla comparativa (HTML table)
        p.append("<table cellspacing='0' style='font-family:Consolas,monospace; border-collapse:collapse; margin-top:4px'>")
        p.append(f"<tr>"
                 f"<td style='{_th}'>Periodo</td>"
                 f"<td style='{_th}'>Fechas</td>"
                 f"<td align='right' style='{_th}'>Excel</td>"
                 f"<td align='right' style='{_th}'>Web</td>"
                 f"<td style='{_th}'>Estado</td></tr>")
        for rp in resultado.periodos:
            periodo = rp.periodo
            if rp.fecha_inicio_real and rp.fecha_fin_real:
                fi, ff = rp.fecha_inicio_real.strftime("%d/%m"), rp.fecha_fin_real.strftime("%d/%m")
            else:
                fi, ff = periodo.fecha_inicio.strftime("%d/%m"), periodo.fecha_fin.strftime("%d/%m")
            fechas = f"{fi}-{ff}"
            tiene_error = rp.precio_excel == "Error"
            nombre = fechas if tiene_error else (periodo.nombre or fechas)
            precio_excel = _money(rp.precio_excel)
            if tiene_error:
                estado, precio_web, color = "⚠ ERROR", "---", self._c_err
            elif rp.coincide:
                estado, precio_web, color = "✅ OK", _money(rp.precio_web), None
            else:
                estado, precio_web, color = "❌ DIFF", _money(rp.precio_web), self._c_err
            fila_color = f"color:{color}; font-weight:bold; " if color else ""
            td = f"{fila_color}{_td}"
            p.append(f"<tr>"
                     f"<td style='{td}'>{_esc(nombre)}</td>"
                     f"<td style='{td}'>{_esc(fechas)}</td>"
                     f"<td align='right' style='{td}'>{_esc(precio_excel)}</td>"
                     f"<td align='right' style='{td}'>{_esc(precio_web)}</td>"
                     f"<td style='{td}'>{_esc(estado)}</td></tr>")
        p.append("</table><br>")

        # Errores de acceso web
        con_error = [rp for rp in resultado.periodos if rp.precio_excel == "Error"]
        if con_error:
            p.append("<b>ERRORES DE ACCESO WEB:</b><br>")
            for rp in con_error:
                periodo = rp.periodo
                if rp.fecha_inicio_real and rp.fecha_fin_real:
                    fi = rp.fecha_inicio_real.strftime("%d/%m/%Y"); ff = rp.fecha_fin_real.strftime("%d/%m/%Y")
                else:
                    fi = periodo.fecha_inicio.strftime("%d/%m/%Y"); ff = periodo.fecha_fin.strftime("%d/%m/%Y")
                p.append(f"&nbsp;&nbsp;<b>{fi} - {ff}:</b><br>")
                if rp.error_url:
                    p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;URL consultada: "
                             f"<a href='{_url(rp.error_url)}'>{_url(rp.error_url)}</a><br>")
                if rp.error_msg:
                    p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;Error: {_esc(rp.error_msg)}<br>")
            p.append("<br>")

        # Detalles habitacion web
        if resultado.habitacion_web_matcheada:
            p.append("<b>DETALLES HABITACION WEB:</b><br>")
            p.append(f"&nbsp;&nbsp;Habitacion: {_esc(resultado.habitacion_web_matcheada.nombre)}<br>")
            if resultado.habitacion_web_matcheada.detalles:
                p.append(f"&nbsp;&nbsp;Detalles: {_esc(resultado.habitacion_web_matcheada.detalles)}<br>")

        # Precios web por periodo (los que no fallaron)
        ok = [rp for rp in resultado.periodos if rp.precio_excel != "Error"]
        if ok:
            p.append("<br><b>&nbsp;&nbsp;Precios Web por Periodo:</b><br>")
            for rp in ok:
                periodo = rp.periodo
                if rp.fecha_inicio_real and rp.fecha_fin_real:
                    fi = rp.fecha_inicio_real.strftime("%d/%m/%Y"); ff = rp.fecha_fin_real.strftime("%d/%m/%Y")
                else:
                    fi = periodo.fecha_inicio.strftime("%d/%m/%Y"); ff = periodo.fecha_fin.strftime("%d/%m/%Y")
                etiqueta = periodo.nombre if periodo.nombre else f"{fi} - {ff}"
                p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;Periodo: {_esc(etiqueta)}<br>")
                if rp.coincide:
                    p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>${rp.precio_web:.2f}</b><br>")
                else:
                    p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;<b style='color:{self._c_err}'>${rp.precio_web:.2f}</b>"
                             f"<span style='color:{self._c_err}'> (Excel: ${rp.precio_excel:.2f} — "
                             f"diferencia: ${rp.diferencia:.2f})</span><br>")
                if rp.url_visitada:
                    p.append(f"&nbsp;&nbsp;&nbsp;&nbsp;URL consultada: "
                             f"<a href='{_url(rp.url_visitada)}'>{_url(rp.url_visitada)}</a><br>")

        html = self._wrap("".join(p))
        self.setHtml(html)
        return html

    def _wrap(self, body):
        return (f"<style>a {{ color: {self._c_link}; }}</style>"
                f"<div style='font-family:Segoe UI,Arial; font-size:13px'>{body}</div>")
