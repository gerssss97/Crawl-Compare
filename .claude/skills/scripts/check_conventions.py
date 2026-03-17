#!/usr/bin/env python3
"""
Skill /check-conventions - Validación de convenciones del proyecto

Analiza archivos Python y verifica cumplimiento de:
1. Nombres en español
2. BaseComponent pattern
3. Controlador pattern
4. Docstrings presentes
"""

import ast
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple


# Colores ANSI
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Palabras en inglés comunes que NO deberían estar en nombres de archivos
# (excepto las permitidas)
PALABRAS_INGLESAS = {
    'user', 'manager', 'handler', 'controller', 'service', 'model',
    'view', 'form', 'widget', 'component', 'panel', 'button', 'input',
    'output', 'data', 'extractor', 'loader', 'saver', 'reader', 'writer',
    'comparison', 'validator', 'state', 'event', 'bus', 'app', 'interface',
    'hotel', 'room', 'period', 'price', 'combo', 'reservation', 'result',
    'scraper', 'crawler', 'web', 'excel'
}

# Palabras permitidas (términos técnicos o nombres propios)
PALABRAS_PERMITIDAS = {
    'test', 'config', 'utils', 'base', 'main', 'app', 'init'
}

# Métodos requeridos para BaseComponent
METODOS_BASECOMPONENT = {'_setup_ui', 'get_value', 'set_value'}
METODOS_BASECOMPONENT_OPCIONALES = {'reset'}


class ValidationResult:
    """Resultado de validación de un archivo."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    @property
    def status(self) -> str:
        """Retorna ✅/⚠️/❌ según el estado."""
        if self.errors:
            return "❌"
        if self.warnings:
            return "⚠️ "
        return "✅"

    @property
    def is_ok(self) -> bool:
        """True si no hay errores ni warnings."""
        return not self.errors and not self.warnings


def detectar_nombres_ingles(file_path: Path) -> List[str]:
    """
    Detecta si el nombre del archivo contiene palabras en inglés.

    Returns:
        Lista de palabras en inglés encontradas (vacía si está OK)
    """
    nombre = file_path.stem  # Nombre sin extensión
    nombre_parts = nombre.split('_')

    palabras_encontradas = []
    for part in nombre_parts:
        if part.lower() in PALABRAS_INGLESAS and part.lower() not in PALABRAS_PERMITIDAS:
            palabras_encontradas.append(part)

    return palabras_encontradas


def sugerir_nombre_espanol(nombre_ingles: str) -> str:
    """
    Sugiere traducción al español de un nombre de archivo.

    Mapeo simple de palabras comunes.
    """
    traducciones = {
        'user': 'usuario',
        'manager': 'gestor',
        'handler': 'manejador',
        'controller': 'controlador',
        'service': 'servicio',
        'model': 'modelo',
        'view': 'vista',
        'form': 'formulario',
        'widget': 'widget',
        'component': 'componente',
        'panel': 'panel',
        'button': 'boton',
        'input': 'entrada',
        'output': 'salida',
        'data': 'datos',
        'extractor': 'extractor',
        'loader': 'cargador',
        'saver': 'guardador',
        'reader': 'lector',
        'writer': 'escritor',
        'comparison': 'comparacion',
        'validator': 'validador',
        'state': 'estado',
        'event': 'evento',
        'bus': 'bus',
        'interface': 'interfaz',
        'hotel': 'hotel',
        'room': 'habitacion',
        'period': 'periodo',
        'price': 'precio',
        'combo': 'combo',
        'reservation': 'reserva',
        'result': 'resultado',
        'scraper': 'scraper',
        'crawler': 'crawler',
        'web': 'web',
        'excel': 'excel'
    }

    parts = nombre_ingles.split('_')
    parts_traducidas = [traducciones.get(p.lower(), p) for p in parts]
    return '_'.join(parts_traducidas)


def analizar_archivo(file_path: Path) -> ValidationResult:
    """
    Analiza un archivo Python y valida convenciones.

    Returns:
        ValidationResult con errores, warnings y successes
    """
    result = ValidationResult(file_path)

    # Leer contenido
    try:
        contenido = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result.errors.append(f"No se pudo leer archivo: {e}")
        return result

    # Parsear AST
    try:
        tree = ast.parse(contenido, filename=str(file_path))
    except SyntaxError as e:
        result.errors.append(f"Error de sintaxis: {e}")
        return result

    # 1. Validar nombres en español
    palabras_ingles = detectar_nombres_ingles(file_path)
    if palabras_ingles:
        sugerencia = sugerir_nombre_espanol(file_path.stem)
        result.errors.append(
            f'Nombre contiene inglés: "{", ".join(palabras_ingles)}"\n'
            f'      → Sugerencia: renombrar a "{sugerencia}.py"'
        )
    else:
        result.successes.append("Nombre en español")

    # 2. Validar docstring de módulo
    module_docstring = ast.get_docstring(tree)
    if not module_docstring:
        result.warnings.append("Falta docstring de módulo")
    else:
        result.successes.append("Docstrings presentes")

    # 3. Analizar clases
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Validar BaseComponent pattern
            if any(isinstance(base, ast.Name) and base.id == 'BaseComponent' for base in node.bases):
                validar_basecomponent(node, result)

            # Validar Controlador pattern
            if 'Controlador' in node.name or 'Controller' in node.name:
                validar_controlador(node, result)

            # Validar docstring de clase
            class_docstring = ast.get_docstring(node)
            if not class_docstring:
                result.warnings.append(f"Falta docstring en clase: {node.name}")

    return result


def validar_basecomponent(class_node: ast.ClassDef, result: ValidationResult) -> None:
    """
    Valida que una clase que hereda de BaseComponent tenga los métodos requeridos.
    """
    metodos_encontrados = set()

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            metodos_encontrados.add(node.name)

            # Validar docstring de método (solo para métodos públicos)
            if not node.name.startswith('_') or node.name == '__init__':
                method_docstring = ast.get_docstring(node)
                if not method_docstring:
                    result.warnings.append(f"Falta docstring en método: {node.name}()")

    # Verificar métodos requeridos
    metodos_faltantes = METODOS_BASECOMPONENT - metodos_encontrados
    if metodos_faltantes:
        result.errors.append(
            f'Faltan métodos requeridos: {", ".join(metodos_faltantes)}'
        )
    else:
        result.successes.append("BaseComponent pattern correcto")
        result.successes.append(f'Métodos requeridos: {", ".join(METODOS_BASECOMPONENT)}')


def validar_controlador(class_node: ast.ClassDef, result: ValidationResult) -> None:
    """
    Valida que un controlador tenga el constructor correcto.
    """
    init_encontrado = False
    params_correctos = False

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == '__init__':
            init_encontrado = True

            # Verificar parámetros: self, estado_app, event_bus
            param_names = [arg.arg for arg in node.args.args]
            if 'estado_app' in param_names and 'event_bus' in param_names:
                params_correctos = True
                result.successes.append("Controlador pattern correcto")
            else:
                result.errors.append(
                    f'Constructor de controlador debe tener parámetros: '
                    f'self, estado_app, event_bus\n'
                    f'      → Encontrado: {", ".join(param_names)}'
                )

    if not init_encontrado:
        result.errors.append("Controlador debe tener método __init__")


def formatear_resultado(result: ValidationResult) -> str:
    """
    Formatea el resultado de validación con colores y emojis.
    """
    lines = []

    # Status + nombre de archivo
    status_color = Colors.GREEN if result.status == "✅" else (
        Colors.YELLOW if result.status == "⚠️ " else Colors.RED
    )
    lines.append(f"{status_color}{result.status} {result.file_path.name}{Colors.RESET}")

    # Successes
    for success in result.successes:
        lines.append(f"   ✓ {success}")

    # Warnings
    for warning in result.warnings:
        lines.append(f"   {Colors.YELLOW}⚠️  {warning}{Colors.RESET}")

    # Errors
    for error in result.errors:
        lines.append(f"   {Colors.RED}❌ {error}{Colors.RESET}")

    return '\n'.join(lines)


def escanear_directorio(path: Path) -> List[ValidationResult]:
    """
    Escanea recursivamente un directorio buscando archivos .py.

    Returns:
        Lista de ValidationResult
    """
    resultados = []

    if path.is_file():
        if path.suffix == '.py':
            resultados.append(analizar_archivo(path))
    else:
        for py_file in path.rglob('*.py'):
            # Ignorar __pycache__ y archivos de test
            if '__pycache__' in str(py_file):
                continue

            resultados.append(analizar_archivo(py_file))

    return resultados


def generar_resumen(resultados: List[ValidationResult]) -> str:
    """
    Genera tabla resumen de validación.
    """
    total = len(resultados)
    sin_problemas = sum(1 for r in resultados if r.is_ok)
    con_warnings = sum(1 for r in resultados if r.warnings and not r.errors)
    con_errores = sum(1 for r in resultados if r.errors)

    # Contar violaciones por tipo
    tipos_violaciones = defaultdict(int)
    for r in resultados:
        for error in r.errors:
            if 'inglés' in error:
                tipos_violaciones['Nombres en inglés'] += 1
            elif 'BaseComponent' in error or 'métodos requeridos' in error:
                tipos_violaciones['BaseComponent incompleto'] += 1
            elif 'Controlador' in error:
                tipos_violaciones['Controlador incompleto'] += 1

        for warning in r.warnings:
            if 'docstring' in warning:
                tipos_violaciones['Docstrings faltantes'] += 1

    lines = [
        f"\n{Colors.BOLD}📊 Resumen{Colors.RESET}",
        "━" * 80,
        "",
        f"Archivos analizados:  {total}",
        f"✅ Sin problemas:     {sin_problemas} ({sin_problemas/total*100:.0f}%)" if total > 0 else "✅ Sin problemas:     0",
        f"⚠️  Con warnings:     {con_warnings} ({con_warnings/total*100:.0f}%)" if total > 0 else "⚠️  Con warnings:     0",
        f"❌ Con errores:       {con_errores} ({con_errores/total*100:.0f}%)" if total > 0 else "❌ Con errores:       0",
    ]

    if tipos_violaciones:
        lines.append("\nViolaciones por tipo:")
        for tipo, count in sorted(tipos_violaciones.items()):
            lines.append(f"  • {tipo:30} {count}")

    lines.append(f"\n{Colors.YELLOW}💡 Tip:{Colors.RESET} Consulta docs/desarrollo/convenciones.md para detalles de cada convención")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Valida convenciones del proyecto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python check_conventions.py UI/components/
  python check_conventions.py UI/controllers/controlador_hotel.py
  python check_conventions.py .
        """
    )

    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default='UI/',
        help='Directorio o archivo a analizar (default: UI/)'
    )

    args = parser.parse_args()

    # Resolver path
    path = Path(args.path)
    if not path.exists():
        print(f"{Colors.RED}❌ Error: Path no existe: {path}{Colors.RESET}")
        sys.exit(1)

    # Header
    print(f"\n{Colors.BOLD}🔍 Validando Convenciones del Proyecto{Colors.RESET}")
    print("━" * 80)
    print(f"\nEscaneando: {path}\n")
    print("━" * 80 + "\n")

    # Escanear
    resultados = escanear_directorio(path)

    if not resultados:
        print(f"{Colors.YELLOW}⚠️  No se encontraron archivos .py en {path}{Colors.RESET}")
        sys.exit(0)

    # Mostrar resultados
    for resultado in resultados:
        print(formatear_resultado(resultado))
        print()  # Espacio entre archivos

    # Resumen
    print("━" * 80)
    print(generar_resumen(resultados))
    print()

    # Exit code: 1 si hay errores, 0 si solo warnings o OK
    if any(r.errors for r in resultados):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
