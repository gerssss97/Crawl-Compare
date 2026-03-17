#!/usr/bin/env python3
"""
Skill /compare-debug - Debugging detallado de fuzzy matching

Muestra los 4 scores individuales de rapidfuzz, el score ponderado,
y detecta inclusión de breakfast. Útil para entender el comportamiento
del matching y ajustar pesos.
"""

import sys
import argparse
from pathlib import Path

# Agregar directorio raíz al path para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rapidfuzz import fuzz
from Core.comparador import limpiar_nombre_excel


# Colores ANSI
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Pesos del scoring (deben coincidir con Core/comparador.py:18-22)
WEIGHTS = {
    'ratio': 0.20,
    'partial': 0.30,
    'token_sort': 0.25,
    'token_set': 0.25
}


def detectar_breakfast(nombre: str) -> bool:
    """
    Detecta si el nombre incluye breakfast.

    Busca keywords: w/breakfast, with breakfast, includes breakfast, etc.
    Usa fuzzy matching parcial con umbral 75%.
    """
    keywords = [
        "w/breakfast", "with breakfast", "includes breakfast",
        "breakfast included", "incl breakfast", "bf included"
    ]

    nombre_lower = nombre.lower()

    # Búsqueda exacta primero
    for keyword in keywords:
        if keyword in nombre_lower:
            return True

    # Fuzzy matching parcial
    for keyword in keywords:
        if fuzz.partial_ratio(nombre_lower, keyword) >= 75:
            return True

    return False


def calcular_scores(nombre_excel_limpio: str, nombre_web: str) -> dict:
    """
    Calcula los 4 scores de fuzzy matching y el score ponderado.

    Returns:
        dict con keys: ratio, partial, token_sort, token_set, final
    """
    nombre_web_lower = nombre_web.lower()

    scores = {
        'ratio': fuzz.ratio(nombre_excel_limpio, nombre_web_lower),
        'partial': fuzz.partial_ratio(nombre_excel_limpio, nombre_web_lower),
        'token_sort': fuzz.token_sort_ratio(nombre_excel_limpio, nombre_web_lower),
        'token_set': fuzz.token_set_ratio(nombre_excel_limpio, nombre_web_lower)
    }

    # Calcular score ponderado
    scores['final'] = (
        scores['ratio'] * WEIGHTS['ratio'] +
        scores['partial'] * WEIGHTS['partial'] +
        scores['token_sort'] * WEIGHTS['token_sort'] +
        scores['token_set'] * WEIGHTS['token_set']
    )

    return scores


def formatear_tabla(nombre_excel: str, habitaciones_web: list[str]) -> None:
    """
    Formatea y muestra la tabla de resultados con colores ANSI.
    """
    # Header
    print(f"\n{Colors.BOLD}🔍 Fuzzy Matching Debug{Colors.RESET}")
    print("━" * 80)

    # Info de habitación Excel
    nombre_excel_limpio = limpiar_nombre_excel(nombre_excel)
    tiene_breakfast = detectar_breakfast(nombre_excel)

    print(f'Habitación Excel (limpia): "{nombre_excel_limpio}"')
    print(f'Habitación Excel (original): "{nombre_excel}"')
    print(f'Incluye breakfast: {"✅" if tiene_breakfast else "❌"}')

    print("\n" + "━" * 80 + "\n")

    # Calcular scores para todas las habitaciones web
    resultados = []
    for hab_web in habitaciones_web:
        scores = calcular_scores(nombre_excel_limpio, hab_web)
        tiene_bf = detectar_breakfast(hab_web)
        resultados.append({
            'nombre': hab_web,
            'scores': scores,
            'breakfast': tiene_bf
        })

    # Encontrar mejor match
    mejor_idx = max(range(len(resultados)), key=lambda i: resultados[i]['scores']['final'])

    # Header de tabla
    print(f"{'Habitación Web':<40} {'Ratio':<7} {'Partial':<8} {'Sort':<7} {'Set':<7} {'Final':<7} BF")
    print("─" * 80)

    # Filas de datos
    for i, resultado in enumerate(resultados):
        nombre = resultado['nombre']
        scores = resultado['scores']
        bf_icon = "✅" if resultado['breakfast'] else "❌"

        # Truncar nombre si es muy largo
        nombre_display = nombre[:38] + ".." if len(nombre) > 40 else nombre

        # Formatear scores
        ratio_str = f"{scores['ratio']:.2f}"
        partial_str = f"{scores['partial']:.2f}"
        sort_str = f"{scores['token_sort']:.2f}"
        set_str = f"{scores['token_set']:.2f}"
        final_str = f"{scores['final']:.2f}"

        # Construir línea
        linea = f"{nombre_display:<40} {ratio_str:<7} {partial_str:<8} {sort_str:<7} {set_str:<7} {final_str:<7} {bf_icon}"

        # Resaltar mejor match
        if i == mejor_idx:
            linea = f"{Colors.GREEN}{linea}  ← MEJOR MATCH{Colors.RESET}"

        print(linea)

    # Footer
    print("\n" + "━" * 80 + "\n")
    print("Pesos utilizados:")
    print(f"  • ratio:       {WEIGHTS['ratio']*100:.0f}%")
    print(f"  • partial:     {WEIGHTS['partial']*100:.0f}%")
    print(f"  • token_sort:  {WEIGHTS['token_sort']*100:.0f}%")
    print(f"  • token_set:   {WEIGHTS['token_set']*100:.0f}%")

    print(f"\n{Colors.YELLOW}💡 Tip:{Colors.RESET} Si el mejor match no es el esperado, considera ajustar los pesos")
    print(f"        en Core/comparador.py:18-22\n")


def main():
    parser = argparse.ArgumentParser(
        description="Debug fuzzy matching entre habitaciones Excel y Web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python compare_debug.py "dbl superior w/breakfast" "Double Superior Room" "Superior Double with Breakfast"
  python compare_debug.py "junior suite" "Junior Suite" "Suite Junior" "Junior Suite Deluxe"
        """
    )

    parser.add_argument(
        'habitacion_excel',
        type=str,
        help='Nombre de habitación desde Excel'
    )

    parser.add_argument(
        'habitaciones_web',
        type=str,
        nargs='+',
        help='Uno o más nombres de habitaciones web para comparar'
    )

    args = parser.parse_args()

    # Validar que haya al menos una habitación web
    if not args.habitaciones_web:
        print("❌ Error: Debes proporcionar al menos una habitación web")
        sys.exit(1)

    # Mostrar tabla
    formatear_tabla(args.habitacion_excel, args.habitaciones_web)


if __name__ == '__main__':
    main()