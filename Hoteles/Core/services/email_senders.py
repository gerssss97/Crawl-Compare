import urllib.parse
import webbrowser

try:
    import pyperclip
    _PYPERCLIP_OK = True
except ImportError:
    _PYPERCLIP_OK = False

_MAILTO_BODY_LIMIT = 1800
_CLIPBOARD_NOTICE = "\n\n---\n[Tabla completa copiada al portapapeles — Ctrl+V para pegar]"


class MailtoSender:
    """Abre el cliente de email del SO con los datos precargados.

    Limitación de Windows: la URL mailto: tiene un límite práctico de ~2000
    chars. Si el cuerpo codificado supera _MAILTO_BODY_LIMIT, se copia el
    cuerpo completo al portapapeles y se trunca el body del mailto.
    """

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        cuerpo_encoded = urllib.parse.quote(cuerpo, safe="")

        if len(cuerpo_encoded) > _MAILTO_BODY_LIMIT:
            if _PYPERCLIP_OK:
                try:
                    pyperclip.copy(cuerpo)
                except Exception:
                    pass

            notice_encoded = urllib.parse.quote(_CLIPBOARD_NOTICE, safe="")
            espacio_disponible = _MAILTO_BODY_LIMIT - len(notice_encoded)
            cuerpo_truncado = urllib.parse.unquote(cuerpo_encoded[:espacio_disponible])
            cuerpo_a_usar = cuerpo_truncado + _CLIPBOARD_NOTICE
        else:
            cuerpo_a_usar = cuerpo

        asunto_encoded = urllib.parse.quote(asunto, safe="")
        body_encoded = urllib.parse.quote(cuerpo_a_usar, safe="")

        url = f"mailto:{destinatario}?subject={asunto_encoded}&body={body_encoded}"
        webbrowser.open(url)
