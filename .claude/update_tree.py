"""Hook PostToolUse/Write: agrega un archivo nuevo al tree-directory.md si no existe."""

import json
import os
import sys

TREE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "arquitectura", "tree-directory.md"
)

SKIP_PATTERNS = ["__pycache__", ".pyc", ".env", "node_modules"]


def debe_ignorar(file_path: str) -> bool:
    return any(p in file_path for p in SKIP_PATTERNS)


def nombre_archivo(file_path: str) -> str:
    return os.path.basename(file_path)


def ya_esta_en_tree(tree: str, file_path: str) -> bool:
    nombre = nombre_archivo(file_path)
    return nombre in tree


def inferir_prefijo(file_path: str, tree: str) -> str:
    """Busca la línea de la carpeta padre en el tree y extrae su prefijo de indentación."""
    partes = file_path.replace("\\", "/").split("/")
    # Buscar la carpeta padre más cercana que aparezca en el tree
    for i in range(len(partes) - 1, 0, -1):
        carpeta = partes[i - 1]
        for linea in tree.splitlines():
            if f"{carpeta}/" in linea or f"{carpeta}/" in linea:
                # Extraer el prefijo de indentación de esa línea
                stripped = linea.lstrip("│ ")
                indent = linea[: len(linea) - len(stripped)]
                return indent + "│   "
    return "│   "


def descripcion_desde_content(content: str) -> str | None:
    """Extrae la primera línea del docstring del contenido del archivo."""
    for linea in content.splitlines():
        linea = linea.strip()
        if linea.startswith('"""') or linea.startswith("'''"):
            texto = linea.strip('"\'').strip()
            if texto:
                return texto
    return None


def descripcion_por_nombre(nombre: str) -> str:
    """Fallback: descripción genérica basada en el nombre del archivo."""
    sin_ext = os.path.splitext(nombre)[0]
    palabras = sin_ext.replace("_", " ").replace("-", " ")
    return palabras.capitalize()


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = (
        tool_input.get("file_path")
        or data.get("tool_response", {}).get("filePath")
        or ""
    )

    if not file_path:
        sys.exit(0)

    # Normalizar a forward slashes para comparación
    file_path_norm = file_path.replace("\\", "/")

    if debe_ignorar(file_path_norm):
        sys.exit(0)

    tree_path = os.path.abspath(TREE_PATH)
    if not os.path.exists(tree_path):
        sys.exit(0)

    with open(tree_path, encoding="utf-8") as f:
        tree = f.read()

    nombre = nombre_archivo(file_path_norm)

    if ya_esta_en_tree(tree, file_path_norm):
        sys.exit(0)

    # Intentar descripción desde docstring del content, fallback al nombre
    content = tool_input.get("content", "")
    desc = descripcion_desde_content(content) or descripcion_por_nombre(nombre)

    partes = file_path_norm.split("/")
    carpeta_padre = partes[-2] if len(partes) >= 2 else ""

    prefijo = inferir_prefijo(file_path_norm, tree)
    nueva_linea = f"{prefijo}├── {nombre}  # {desc}"

    lineas = tree.splitlines()
    indice_insercion = None

    for i, linea in enumerate(lineas):
        if carpeta_padre and f"{carpeta_padre}/" in linea:
            # Buscar el último archivo dentro de esa sección (antes de una subsección o línea vacía)
            for j in range(i + 1, len(lineas)):
                stripped = lineas[j].strip()
                if stripped.startswith("├──") or stripped.startswith("└──"):
                    indice_insercion = j
                elif not stripped.startswith("│") and stripped != "":
                    break
            break

    if indice_insercion is None:
        # Fallback: agregar antes del cierre del bloque de código
        for i in range(len(lineas) - 1, -1, -1):
            if lineas[i].strip() == "```":
                indice_insercion = i
                break

    if indice_insercion is not None:
        lineas.insert(indice_insercion, nueva_linea)
        with open(tree_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    main()
