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


class GmailWebSender:
    """Abre Gmail en el navegador con el compose precargado."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        su = urllib.parse.quote(asunto, safe="")
        body = urllib.parse.quote(cuerpo, safe="")
        to = urllib.parse.quote(destinatario, safe="")
        url = f"https://mail.google.com/mail/?view=cm&to={to}&su={su}&body={body}"
        webbrowser.open(url)


class OutlookWebSender:
    """Abre Outlook Web en el navegador con el compose precargado."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        subject = urllib.parse.quote(asunto, safe="")
        body = urllib.parse.quote(cuerpo, safe="")
        to = urllib.parse.quote(destinatario, safe="")
        url = (
            f"https://outlook.live.com/mail/0/deeplink/compose"
            f"?to={to}&subject={subject}&body={body}"
        )
        webbrowser.open(url)


class ClipboardSender:
    """Copia el cuerpo del email al portapapeles sin abrir ningún cliente."""

    copied: bool = False

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        self.copied = False
        if _PYPERCLIP_OK:
            try:
                pyperclip.copy(cuerpo)
                self.copied = True
            except Exception:
                pass


_PROVIDER_KEYS = ["mailto", "gmail_web", "outlook_web", "clipboard"]


def get_sender(provider: str) -> MailtoSender | GmailWebSender | OutlookWebSender | ClipboardSender:
    if provider == "gmail_web":
        return GmailWebSender()
    if provider == "outlook_web":
        return OutlookWebSender()
    if provider == "clipboard":
        return ClipboardSender()
    return MailtoSender()
