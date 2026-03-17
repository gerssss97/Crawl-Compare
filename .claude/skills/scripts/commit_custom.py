#!/usr/bin/env python3
"""
Skill /commit-custom - Generación de commits conventional en español

Crea commits con formato conventional, preview interactivo.
"""

import sys
import subprocess
import argparse


# Colores ANSI
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Tipos de commits
TIPOS_COMMIT = {
    '1': ('feat', 'Nueva funcionalidad'),
    '2': ('fix', 'Corrección de bug'),
    '3': ('style', 'Cambios de formato (sin afectar lógica)'),
    '4': ('refactor', 'Refactorización de código'),
    '5': ('test', 'Agregar o modificar tests'),
    '6': ('docs', 'Cambios en documentación'),
    '7': ('chore', 'Tareas de mantenimiento'),
}


def ejecutar_comando(cmd):
    """
    Ejecuta comando de shell y retorna output.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"{Colors.RED}❌ Error ejecutando comando: {e}{Colors.RESET}")
        return ""


def mostrar_git_status():
    """
    Muestra git status para contexto.
    """
    print(f"\n{Colors.BLUE}📊 Git Status:{Colors.RESET}")
    status = ejecutar_comando("git status --short")
    if status:
        print(status)
    else:
        print("  (no hay cambios)")


def mostrar_git_diff():
    """
    Muestra git diff de archivos staged (primeras 20 líneas).
    """
    print(f"\n{Colors.BLUE}📝 Git Diff (staged):{Colors.RESET}")
    diff = ejecutar_comando("git diff --cached --stat")
    if diff:
        print(diff)
    else:
        print("  (no hay archivos staged)")


def modo_interactivo():
    """
    Modo interactivo con prompts paso a paso.

    Returns:
        dict con tipo, scope, mensaje, descripcion
    """
    print(f"\n{Colors.BOLD}╔{'═'*64}╗{Colors.RESET}")
    print(f"{Colors.BOLD}║{' '*20}Crear Commit Custom{' '*24}║{Colors.RESET}")
    print(f"{Colors.BOLD}╚{'═'*64}╝{Colors.RESET}")

    # Mostrar contexto
    mostrar_git_status()
    mostrar_git_diff()

    print(f"\n{'━'*66}\n")

    # 1. Tipo de commit
    print(f"{Colors.BOLD}Tipo de commit:{Colors.RESET}")
    for key, (tipo, desc) in TIPOS_COMMIT.items():
        print(f"  {key}. {tipo:<10} - {desc}")

    while True:
        tipo_input = input(f"\n{Colors.YELLOW}Seleccione tipo [1-7]: {Colors.RESET}").strip()
        if tipo_input in TIPOS_COMMIT:
            tipo, _ = TIPOS_COMMIT[tipo_input]
            break
        print(f"{Colors.RED}❌ Opción inválida{Colors.RESET}")

    # 2. Scope (opcional)
    scope = input(f"\n{Colors.YELLOW}Scope (área del proyecto, Enter para omitir): {Colors.RESET}").strip()

    # 3. Mensaje corto
    while True:
        mensaje = input(f"\n{Colors.YELLOW}Mensaje corto (<70 caracteres): {Colors.RESET}").strip()
        if not mensaje:
            print(f"{Colors.RED}❌ El mensaje no puede estar vacío{Colors.RESET}")
            continue
        if len(mensaje) > 70:
            print(f"{Colors.RED}❌ Mensaje muy largo ({len(mensaje)} chars), máximo 70{Colors.RESET}")
            continue
        break

    # 4. Descripción extendida (opcional)
    print(f"\n{Colors.YELLOW}Descripción extendida (opcional, Enter x2 para terminar):{Colors.RESET}")
    lineas_descripcion = []
    lineas_vacias_consecutivas = 0

    while True:
        linea = input("> ")

        if not linea:
            lineas_vacias_consecutivas += 1
            if lineas_vacias_consecutivas >= 2:
                break
        else:
            lineas_vacias_consecutivas = 0
            lineas_descripcion.append(linea)

    descripcion = '\n'.join(lineas_descripcion).strip()

    return {
        'tipo': tipo,
        'scope': scope,
        'mensaje': mensaje,
        'descripcion': descripcion
    }


def construir_mensaje_commit(tipo, scope, mensaje, descripcion):
    """
    Construye el mensaje completo del commit.

    Args:
        tipo: str - feat, fix, etc.
        scope: str - Opcional
        mensaje: str - Mensaje corto
        descripcion: str - Descripción extendida (opcional)

    Returns:
        str - Mensaje completo del commit
    """
    # Primera línea
    if scope:
        primera_linea = f"{tipo}({scope}): {mensaje}"
    else:
        primera_linea = f"{tipo}: {mensaje}"

    # Construir mensaje completo
    partes = [primera_linea]

    if descripcion:
        partes.append("")  # Línea vacía
        partes.append(descripcion)

    return '\n'.join(partes)


def mostrar_preview(mensaje_commit):
    """
    Muestra preview del commit.
    """
    print(f"\n{'━'*66}\n")
    print(f"{Colors.BOLD}📋 Preview del Commit:{Colors.RESET}")
    print(f"{'━'*66}")
    print(f"{Colors.GREEN}{mensaje_commit}{Colors.RESET}")
    print(f"{'━'*66}\n")


def confirmar():
    """
    Pide confirmación al usuario.

    Returns:
        bool - True si confirma, False si cancela
    """
    while True:
        respuesta = input(f"{Colors.YELLOW}¿Crear este commit? [y/n]: {Colors.RESET}").strip().lower()
        if respuesta in ['y', 'yes', 's', 'si', 'sí']:
            return True
        if respuesta in ['n', 'no']:
            return False
        print(f"{Colors.RED}❌ Respuesta inválida{Colors.RESET}")


def crear_commit(mensaje_commit):
    """
    Crea el commit usando git.

    Args:
        mensaje_commit: str - Mensaje completo del commit

    Returns:
        bool - True si exitoso, False si falla
    """
    # Escapar comillas en el mensaje
    mensaje_escaped = mensaje_commit.replace('"', '\\"')

    # Construir comando con heredoc para mejor manejo de multilínea
    cmd = f'''git commit -m "{mensaje_escaped}"'''

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            print(f"\n{Colors.GREEN}✅ Commit creado exitosamente{Colors.RESET}")

            # Obtener hash del commit
            commit_hash = ejecutar_comando("git rev-parse --short HEAD")
            if commit_hash:
                print(f"   Hash: {Colors.BOLD}{commit_hash}{Colors.RESET}")

            print(f"\n{Colors.GREEN}🎉 Listo!{Colors.RESET}\n")
            return True
        else:
            print(f"\n{Colors.RED}❌ Error al crear commit:{Colors.RESET}")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.RESET}")
        return False


def modo_directo(tipo, scope, mensaje):
    """
    Modo directo con parámetros.

    Args:
        tipo: str - Tipo de commit
        scope: str o None
        mensaje: str - Mensaje del commit

    Returns:
        dict con tipo, scope, mensaje, descripcion (vacía)
    """
    # Validar tipo
    tipos_validos = [t for t, _ in TIPOS_COMMIT.values()]
    if tipo not in tipos_validos:
        print(f"{Colors.RED}❌ Tipo inválido: {tipo}{Colors.RESET}")
        print(f"Tipos válidos: {', '.join(tipos_validos)}")
        sys.exit(1)

    # Validar longitud del mensaje
    if len(mensaje) > 70:
        print(f"{Colors.RED}❌ Mensaje muy largo ({len(mensaje)} chars), máximo 70{Colors.RESET}")
        sys.exit(1)

    return {
        'tipo': tipo,
        'scope': scope or '',
        'mensaje': mensaje,
        'descripcion': ''
    }


def main():
    parser = argparse.ArgumentParser(
        description="Crear commits conventional en español",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Modo interactivo (recomendado)
  python commit_custom.py

  # Modo directo
  python commit_custom.py feat comparacion "Mejorar fuzzy matching"
  python commit_custom.py fix scraper "Corregir timeout"
  python commit_custom.py docs readme "Actualizar guía"

Tipos disponibles:
  feat      - Nueva funcionalidad
  fix       - Corrección de bug
  style     - Cambios de formato
  refactor  - Refactorización
  test      - Tests
  docs      - Documentación
  chore     - Mantenimiento
        """
    )

    parser.add_argument(
        'tipo',
        type=str,
        nargs='?',
        help='Tipo de commit (feat, fix, style, etc.)'
    )

    parser.add_argument(
        'scope',
        type=str,
        nargs='?',
        help='Scope del commit (opcional)'
    )

    parser.add_argument(
        'mensaje',
        type=str,
        nargs='?',
        help='Mensaje del commit'
    )

    args = parser.parse_args()

    # Determinar modo
    if args.tipo and args.mensaje:
        # Modo directo
        data = modo_directo(args.tipo, args.scope, args.mensaje)
    elif not args.tipo:
        # Modo interactivo
        data = modo_interactivo()
    else:
        # Parámetros incompletos
        print(f"{Colors.RED}❌ Parámetros incompletos{Colors.RESET}")
        print("Uso:")
        print("  Modo interactivo: python commit_custom.py")
        print("  Modo directo:     python commit_custom.py <tipo> [scope] <mensaje>")
        sys.exit(1)

    # Construir mensaje
    mensaje_commit = construir_mensaje_commit(
        data['tipo'],
        data['scope'],
        data['mensaje'],
        data['descripcion']
    )

    # Mostrar preview
    mostrar_preview(mensaje_commit)

    # Confirmar
    if not confirmar():
        print(f"\n{Colors.YELLOW}⚠️  Commit cancelado{Colors.RESET}\n")
        sys.exit(0)

    # Crear commit
    exito = crear_commit(mensaje_commit)

    sys.exit(0 if exito else 1)


if __name__ == '__main__':
    main()
