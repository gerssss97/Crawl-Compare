# ============================================================
# debug_config.py — Flags de debug globales
#
# Convención de nombres: DEBUG_<AREA>_<DETALLE>
# El nombre debe responder a "qué loguea" no "dónde se usa".
#
# Importar desde cualquier módulo:
#   from debug_config import DEBUG_LLM_MARKDOWN, DEBUG_FUZZY_MATCHING
# ============================================================

# ===== SCRAPING =====

# Muestra la ventana del browser durante el scraping.
# En False (default), Chromium corre en headless (sin GUI), lo que
# es más rápido y no interrumpe al usuario. Activar solo para debug visual.
SHOW_BROWSER = False

# Logging detallado del pipeline de scraping en cada intento:
# - Nivel 1 (Crawl4AI): result.success / error_message / status_code / tamaños HTML+markdown
# - Nivel 2 (Markdown→LLM): stats del markdown enviado a Groq (volcado a stdout, no archivo)
# - Nivel 3 (Respuesta Groq): respuesta cruda del LLM, parseo JSON, razón de "incompleto"
# Útil para diagnosticar por qué falla un intento (especialmente en .exe).
DEBUG_SCRAPING_PIPELINE = False

# Guarda el markdown enviado al LLM como archivo debug_llm_input_*.txt tras cada scrape.
# OJO: crea un archivo por cada intento. Para debug puntual en .exe usar DEBUG_SCRAPING_PIPELINE
# (que vuelca al stdout y se captura en output.log).
DEBUG_LLM_MARKDOWN = False

# Verbose logging interno de Crawl4AI ([INIT], [FETCH], [SCRAPE], etc.)
# y prints de gestor_datos sobre pickle/cache.
DEBUG_CRAWL4AI_VERBOSE = False

# ===== COMPARACIÓN =====

# Prints del proceso de fuzzy matching entre habitaciones Excel y Web.
DEBUG_FUZZY_MATCHING = False

# ===== EXTRACCIÓN EXCEL =====

# Prints del parseo de fechas y nombres en ExtractorDatos/utils.py.
DEBUG_EXCEL_PARSING = False

# ===== STARTUP =====

# Informa qué Excel se intentó cargar al iniciar la app y si tuvo éxito o falló.
# Útil para diagnosticar problemas de configuración en el arranque.
DEBUG_STARTUP_EXCEL_LOAD = False

# ===== PIPELINE DE COMPARACIÓN =====

# Imprime el progreso completo del pipeline de comparación multi-periodo:
# - Nombre de habitación comparada y cantidad de periodos detectados
# - Número de periodo actual y fechas de scraping calculadas
# - Confirmación de scraping fresco (gestor_datos)
# - URL construida para el scraper y JSON crudo extraído del LLM (scraper_utils)
DEBUG_COMPARISON_PIPELINE = False

# ============================================================
# Override automático en producción (.exe)
# ============================================================
# En el .exe queremos ciertos logs SIEMPRE activos, sin importar
# lo que diga el código fuente más arriba. Así, si el usuario reporta
# un bug, ya tenemos información del runtime en crawl_compare_YYYYMMDD.log
# sin necesidad de rebuildear con flags distintos.
#
# En dev (sin sys.frozen) los flags quedan como los configuraste arriba.
# ============================================================
import sys as _sys
if getattr(_sys, "frozen", False):
    DEBUG_SCRAPING_PIPELINE = True       # pipeline de cada intento de scrape
    DEBUG_FUZZY_MATCHING = True          # scores del matching Excel↔Web
    DEBUG_COMPARISON_PIPELINE = True     # contexto multi-periodo + URLs + JSON
    DEBUG_STARTUP_EXCEL_LOAD = True      # carga de Excel al arrancar
    DEBUG_CRAWL4AI_VERBOSE = True        # verbose interno de Crawl4AI + cache

    # Los siguientes quedan en False INCLUSO en .exe:
    # DEBUG_LLM_MARKDOWN     — genera un archivo por intento (llena disco)
    # DEBUG_EXCEL_PARSING    — muy verboso, solo útil para diagnosticar parseo
