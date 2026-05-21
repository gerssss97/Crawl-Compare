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
