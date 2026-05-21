import os
import sys
import subprocess


def _get_base_dir() -> str:
    """Devuelve el directorio base: carpeta temporal de PyInstaller en producción, o Hoteles/ en dev."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # PyInstaller extrae los datas del .spec acá en runtime
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_env() -> None:
    """Carga el .env desde base_dir. Si no existe, aborta con mensaje claro."""
    from dotenv import load_dotenv

    base_dir = _get_base_dir()
    env_path = os.path.join(base_dir, ".env")

    if not os.path.exists(env_path):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Archivo .env no encontrado",
            f"No se encontró el archivo .env en:\n{env_path}\n\n"
            "Asegurate de que esté en la misma carpeta que el programa."
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


def check_playwright() -> None:
    """Apunta PLAYWRIGHT_BROWSERS_PATH a los browsers embebidos en el .exe, o instala si estamos en dev."""
    if getattr(sys, "frozen", False):
        # En .exe: Chromium está embebido en _MEIPASS, apuntamos Playwright ahí
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(
            sys._MEIPASS, "playwright", "driver", "package", ".local-browsers"
        )
        return

    if _chromium_installed():
        return

    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Crawl Compare — Primera ejecución")
    root.geometry("420x140")
    root.resizable(False, False)
    root.eval("tk::PlaceWindow . center")

    tk.Label(
        root,
        text="Instalando dependencias del navegador...\nEsto solo ocurre la primera vez (puede tardar ~2 min).",
        pady=16,
        justify="center",
    ).pack()

    bar = ttk.Progressbar(root, mode="indeterminate", length=340)
    bar.pack()
    bar.start(12)

    root.update_idletasks()
    root.update()

    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )

    root.destroy()

    if result.returncode != 0:
        root2 = tk.Tk()
        root2.withdraw()
        tk.messagebox.showerror(
            "Error instalando Playwright",
            f"No se pudo instalar Chromium:\n\n{result.stderr[-500:]}"
        )
        sys.exit(1)


def run_checks() -> None:
    check_env()
    check_playwright()
