import re
from difflib import SequenceMatcher
from models.hotel import *
from rapidfuzz import fuzz

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

def obtener_mejor_match_con_breakfast(combo_elegido, hab_web):
    # Normalizar combo_elegido
    tiene_breakfast = contiene_breakfast(combo_elegido)
    # Extraer nombres de habitaciones web
    nombres_web = [habitacion.nombre for habitacion in hab_web]

    # Buscar mejor match de nombre
    mejor_nombre, _ = encontrar_mejor_match(combo_elegido, nombres_web)
    print("MEJOR NOMBRE WEB ",mejor_nombre)
    print("COMBO ELEGIDO",combo_elegido)
    for habitacion in hab_web:
        if habitacion.nombre == mejor_nombre:
            print("HABITACION ENCONTRADA",habitacion.nombre)
            if tiene_breakfast:
                print("FILTRANDO POR BREAKFAST")
                print_habitacion_web(habitacion)
                # Filtrar combos que tengan algún indicio de breakfast en el título
                combos_filtrados = [
                    combo for combo in habitacion.combos
                    if contiene_breakfast(combo.titulo)
                ]
                if combos_filtrados:
                    habitacion = Habitacion(
                        nombre=habitacion.nombre,
                        detalles=habitacion.detalles,
                        combos=combos_filtrados
                    )
                    print("devolvi habitacion con breakfast")
                    # Retorna la misma habitación, pero con los combos filtrados
                    return habitacion, "Se encontró un combo con 'breakfast'. Se muestran solo ese combo."
                else:
                    return habitacion, "Se buscó un combo con 'breakfast', pero no se encontró ninguno con dicho detalle en la web."
            else:
                print("devolvi habitacion")
                return habitacion, "Habitacion completa"  # No requiere filtrado
    print("NO COINCIDENTES CON",mejor_nombre)
    return None, "No se encontró ninguna habitación que coincida con el nombre proporcionado."