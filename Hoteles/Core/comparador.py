import re
from Models.hotelExcel import *
from Models.hotelWeb import *
from rapidfuzz import fuzz
from debug_config import DEBUG_FUZZY_MATCHING

def encontrar_mejor_match(nombre_excel, nombres_web):
    nombre_excel_limpio = limpiar_nombre_excel(nombre_excel)
    mejores_scores = []

    for nombre_web in nombres_web:
        # Usamos varias métricas de RapidFuzz
        score_ratio = fuzz.ratio(nombre_excel_limpio, nombre_web) / 100
        score_partial = fuzz.partial_ratio(nombre_excel_limpio, nombre_web) / 100
        score_token_sort = fuzz.token_sort_ratio(nombre_excel_limpio, nombre_web) / 100
        score_token_set = fuzz.token_set_ratio(nombre_excel_limpio, nombre_web) / 100

        # Score combinado (ajustá pesos según tu caso)
        score_total = (
            0.2 * score_ratio +
            0.3 * score_partial +
            0.25 * score_token_sort +
            0.25 * score_token_set
        )
        mejores_scores.append((nombre_web, score_total))
        # print(f"{nombre_web}': Score ratio {score_ratio:.4f}")
        # print(f"{nombre_web}': Score partial {score_partial:.4f}")
        # print(f"{nombre_web}': Score toke sort {score_token_sort:.4f}")
        # print(f"{nombre_web}': Score token set {score_token_set:.4f}")
        # print(f"{nombre_web}': Score total {score_total:.4f}")
        

    mejor_nombre_web, mejor_score = max(mejores_scores, key=lambda x: x[1])
    print(f"Mejor match para '{nombre_excel}' es '{mejor_nombre_web}' con score {mejor_score:.4f}")
    return mejor_nombre_web, mejor_score

def limpiar_nombre_excel(nombre):
    # Pasar todo a minúsculas
    nombre = nombre.lower()
    # Quitar cosas entre paréntesis
    nombre = re.sub(r"\(.*?\)", "", nombre)
    # Quitar abreviaturas típicas sgl/dbl/tpl, w/, ad, ch
    nombre = re.sub(r"\b(sgl|dbl|tpl|w|ad|ch)\b", "", nombre)
    # Quitar palabras comunes irrelevantes
    nombre = re.sub(r"\b(w/breakfast|restaurant|breakfast|served)\b", "", nombre)
    # Quitar números y caracteres especiales
    nombre = re.sub(r"[^a-z\s]", "", nombre)
    # Compactar espacios
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre


def contiene_breakfast(texto, umbral=75):
    texto_norm = texto.lower()
    patrones_relacionados = [
        "w/breakfast", "with breakfast", "includes breakfast",
        "breakfast inclusive", "breakfast included"
    ]

    # primero chequeo directo rápido
    for patron in patrones_relacionados:
        if patron in texto_norm:
            return True

    # luego fuzzy partial (subcadena)
    for patron in patrones_relacionados:
        ratio = fuzz.partial_ratio(texto_norm, patron)
        if ratio >= umbral:
            return True

    return False

def obtener_mejor_match(nombre_excel: str, habitaciones_web: list) -> tuple:
    """Realiza fuzzy matching entre nombre_excel y la lista de HabitacionWeb.

    Args:
        nombre_excel: Nombre de la habitación en el Excel
        habitaciones_web: Lista de HabitacionWeb scrapeadas

    Returns:
        Tuple (HabitacionWeb, mensaje) con el mejor match, o (None, mensaje) si no se encontró
    """
    nombres_web = [h.nombre for h in habitaciones_web]
    mejor_nombre, _ = encontrar_mejor_match(nombre_excel, nombres_web)
    for hab in habitaciones_web:
        if hab.nombre == mejor_nombre:
            return hab, "Match encontrado"
    return None, "No se encontró match"


def aplicar_filtro_breakfast(habitacion: HabitacionWeb, nombre_excel: str) -> HabitacionWeb:
    """Aplica filtro de breakfast a una habitación web si es necesario.

    Args:
        habitacion: HabitacionWeb a filtrar
        nombre_excel: Nombre de la habitación Excel (para detectar si incluye breakfast)

    Returns:
        HabitacionWeb filtrada (solo combos con breakfast) o habitación original
    """
    tiene_breakfast = contiene_breakfast(nombre_excel)

    if not tiene_breakfast:
        # No necesita filtro, devolver habitación original
        return habitacion

    # Filtrar combos que contengan breakfast
    combos_filtrados = [
        combo for combo in habitacion.combos
        if contiene_breakfast(combo.titulo)
    ]

    if not combos_filtrados:
        # Si no hay combos con breakfast, devolver habitación original
        print(f"⚠️ Advertencia: No se encontraron combos con breakfast para '{habitacion.nombre}'")
        return habitacion

    # Crear nueva habitación con combos filtrados
    print(f"→ Filtrado de breakfast aplicado: {len(habitacion.combos)} → {len(combos_filtrados)} combos")
    return HabitacionWeb(
        nombre=habitacion.nombre,
        detalles=habitacion.detalles,
        combos=combos_filtrados
    )