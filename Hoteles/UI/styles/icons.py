from pathlib import Path
from PIL import Image
import customtkinter as ctk

_BASE = Path(__file__).parent.parent / "assets" / "icons"


def _load(name: str, size=(20, 20)) -> ctk.CTkImage:
    """Ícono adaptable al appearance mode (light/dark)."""
    return ctk.CTkImage(
        light_image=Image.open(_BASE / "light" / f"{name}.png"),
        dark_image=Image.open(_BASE / "dark" / f"{name}.png"),
        size=size,
    )


def _load_header(name: str, size=(20, 20)) -> ctk.CTkImage:
    """Ícono trazo blanco fijo — para el header, que es oscuro en ambos modos."""
    img = Image.open(_BASE / "dark" / f"{name}.png")
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


class Icons:
    # Íconos adaptables — para cards, panels, botones sobre fondo claro/azul
    CLOCK        = None
    SETTINGS     = None
    FOLDER       = None
    HOME         = None
    TRASH        = None
    DOLLAR       = None
    ALERT        = None
    X_CIRCLE     = None
    CHECK_CIRCLE = None

    # Íconos para el header (siempre trazo blanco)
    CLOCK_HEADER        = None
    SETTINGS_HEADER     = None
    FOLDER_HEADER       = None
    HOME_HEADER         = None
    TRASH_HEADER        = None
    DOLLAR_HEADER       = None
    ALERT_HEADER        = None
    X_CIRCLE_HEADER     = None
    CHECK_CIRCLE_HEADER = None

    @classmethod
    def load(cls):
        cls.CLOCK        = _load("clock")
        cls.SETTINGS     = _load("settings")
        cls.FOLDER       = _load("folder")
        cls.HOME         = _load("home")
        cls.TRASH        = _load("trash-2")
        cls.DOLLAR       = _load("dollar-sign")
        cls.ALERT        = _load("alert-triangle")
        cls.X_CIRCLE     = _load("x-circle")
        cls.CHECK_CIRCLE = _load("check-circle")

        cls.CLOCK_HEADER        = _load_header("clock")
        cls.SETTINGS_HEADER     = _load_header("settings")
        cls.FOLDER_HEADER       = _load_header("folder")
        cls.HOME_HEADER         = _load_header("home")
        cls.TRASH_HEADER        = _load_header("trash-2")
        cls.DOLLAR_HEADER       = _load_header("dollar-sign")
        cls.ALERT_HEADER        = _load_header("alert-triangle")
        cls.X_CIRCLE_HEADER     = _load_header("x-circle")
        cls.CHECK_CIRCLE_HEADER = _load_header("check-circle")
