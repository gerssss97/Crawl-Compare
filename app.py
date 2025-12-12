#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crawl-Compare - Comparador de precios de habitaciones
======================================================

Aplicación para comparar precios de habitaciones entre Excel y Web.

Uso:
    python app.py

Autor: German Lucero
"""

import sys
import os

# Asegurarse de que el directorio raíz esté en el path
if __name__ == "__main__":
    raiz_proyecto = os.path.dirname(os.path.abspath(__file__))
    if raiz_proyecto not in sys.path:
        sys.path.insert(0, raiz_proyecto)

from UI.interfaz import run_interfaz


def main():
    """Punto de entrada principal de la aplicación."""
    print("=" * 70)
    print(" CRAWL-COMPARE - Comparador de Precios de Habitaciones".center(70))
    print("=" * 70)
    print()

    try:
        run_interfaz()
    except KeyboardInterrupt:
        print("\n\nAplicación cerrada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
