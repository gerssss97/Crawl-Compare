"""Persistencia de configuración del usuario en JSON.

El archivo vive en %APPDATA%/CrawlCompare/config.json (Windows .exe),
~/.config/CrawlCompare/config.json (otros OS .exe) o junto al main.py
(modo dev). Guarda preferencias como el último Excel usado, y queda
preparado para sumar email/api keys/etc en futuras iteraciones.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


def _config_dir() -> Path:
    """Directorio donde vive config.json.

    - .exe Windows: %APPDATA%/CrawlCompare/ (persistente entre versiones)
    - .exe otros:   $XDG_CONFIG_HOME/CrawlCompare/ o ~/.config/CrawlCompare/
    - Dev:          <repo>/Hoteles/ (junto al main.py)
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "CrawlCompare"
    return Path(__file__).parent.parent.parent  # Hoteles/


def _config_path() -> Path:
    return _config_dir() / "config.json"


class ConfigService:
    """Lectura y escritura de config.json con cache en memoria. Singleton."""

    _instance: "ConfigService | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._path = _config_path()
        self._cache: dict[str, Any] = self._cargar()
        self._initialized = True

    def _cargar(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {}
        try:
            with self._path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ConfigService] Error leyendo {self._path}: {e}. Usando config vacía.")
            return {}

    def _guardar(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[ConfigService] Error escribiendo {self._path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if value is None:
            self._cache.pop(key, None)
        else:
            self._cache[key] = value
        self._guardar()

    @property
    def path(self) -> Path:
        return self._path

    def get_last_excel_path(self) -> Optional[str]:
        return self._cache.get("last_excel_path")

    def set_last_excel_path(self, path: Optional[str]) -> None:
        self.set("last_excel_path", path)

    def get_historial(self) -> list:
        return self._cache.get("historial", [])

    def set_historial(self, entradas: list) -> None:
        self.set("historial", entradas)

    def get_email_template(self) -> str | None:
        return self._cache.get("email_template", None)

    def set_email_template(self, template: str | None) -> None:
        self.set("email_template", template)

    def get_email_firma(self) -> str:
        return self._cache.get("email_firma", "Germán Lucero")

    def set_email_firma(self, firma: str | None) -> None:
        self.set("email_firma", firma)

    def get_email_provider(self) -> str:
        return self._cache.get("email_provider", "mailto")

    def set_email_provider(self, provider: str) -> None:
        self.set("email_provider", provider)

    def get_historial_ttl_dias(self) -> int:
        return int(self._cache.get("historial_ttl_dias", 7))

    def set_historial_ttl_dias(self, dias: int) -> None:
        self.set("historial_ttl_dias", int(dias))

    def get_ocultar_periodos_vencidos(self) -> bool:
        return bool(self._cache.get("ocultar_periodos_vencidos", False))

    def set_ocultar_periodos_vencidos(self, valor: bool) -> None:
        self.set("ocultar_periodos_vencidos", bool(valor))
