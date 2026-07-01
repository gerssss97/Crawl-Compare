"""Checks de arranque: .env, Playwright/Chromium. Sin dependencia de Tkinter."""
import os
import sys
import subprocess
from typing import Optional, Callable


def _get_base_dir() -> str:
    """Devuelve el directorio base: carpeta temporal de PyInstaller en producción, o Hoteles/ en dev."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_qapp_instance = None  # referencia a nivel de módulo para evitar GC prematuro


def _qapp():
    """Devuelve el QApplication activo o crea uno y lo retiene en módulo."""
    global _qapp_instance
    from PySide6.QtWidgets import QApplication
    existing = QApplication.instance()
    if existing is not None:
        return existing
    _qapp_instance = QApplication(sys.argv)
    return _qapp_instance


def check_env() -> None:
    """Carga el .env desde base_dir. Si no existe, muestra error y aborta."""
    from dotenv import load_dotenv

    base_dir = _get_base_dir()
    env_path = os.path.join(base_dir, ".env")

    if not os.path.exists(env_path):
        from PySide6.QtWidgets import QMessageBox
        app = _qapp()
        QMessageBox.critical(
            None,
            "Archivo .env no encontrado",
            f"No se encontró el archivo .env en:\n{env_path}\n\n"
            "Asegurate de que esté en la misma carpeta que el programa.",
        )
        sys.exit(1)

    load_dotenv(env_path)


def _chromium_installed() -> bool:
    """Verifica si el ejecutable de Chromium de Playwright existe en el sistema."""
    from pathlib import Path
    appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA", "")
    ms_playwright = Path(appdata) / "ms-playwright"
    if not ms_playwright.exists():
        return False
    return any(ms_playwright.glob("chromium-*/chrome-win/chrome.exe"))


def _firefox_installed() -> bool:
    """Verifica si el ejecutable de Firefox de Playwright existe en el sistema."""
    from pathlib import Path
    appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA", "")
    ms_playwright = Path(appdata) / "ms-playwright"
    if not ms_playwright.exists():
        return False
    return any(ms_playwright.glob("firefox-*/firefox/firefox.exe"))


def check_playwright() -> None:
    """Apunta PLAYWRIGHT_BROWSERS_PATH a los browsers embebidos en el .exe, o instala si estamos en dev."""
    if getattr(sys, "frozen", False):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(
            sys._MEIPASS, "playwright", "driver", "package", ".local-browsers"
        )
        return

    chromium_ok = _chromium_installed()
    firefox_ok = _firefox_installed()
    if chromium_ok and firefox_ok:
        return

    browsers = []
    if not chromium_ok:
        browsers.append("chromium")
    if not firefox_ok:
        browsers.append("firefox")

    from PySide6.QtWidgets import QProgressDialog, QMessageBox
    from PySide6.QtCore import Qt

    app = _qapp()
    dlg = QProgressDialog(
        f"Instalando dependencias del navegador ({', '.join(browsers)})...\nEsto solo ocurre la primera vez (puede tardar ~2 min).",
        None,  # sin botón cancelar
        0, 0,  # min=max=0 → indeterminado
    )
    dlg.setWindowTitle("Crawl Compare — Primera ejecución")
    dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
    dlg.setMinimumWidth(420)
    dlg.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    dlg.show()
    app.processEvents()

    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install"] + browsers,
        capture_output=True,
        text=True,
    )

    dlg.close()

    if result.returncode != 0:
        QMessageBox.critical(
            None,
            "Error instalando Playwright",
            f"No se pudieron instalar los browsers ({', '.join(browsers)}):\n\n{result.stderr[-500:]}",
        )
        sys.exit(1)


def run_checks(on_progress: Optional[Callable[[str], None]] = None) -> None:
    _notify = on_progress or (lambda msg: None)

    _notify("Verificando configuración...")
    check_env()

    _notify("Verificando navegador...")
    check_playwright()
