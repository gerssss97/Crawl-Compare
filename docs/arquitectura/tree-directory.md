# Tree Directory — Crawl-Compare

Estructura completa del proyecto. Actualizar cuando se agreguen/muevan archivos.

> ⭐ = archivos clave / más modificados

```
Hoteles/
├── main.py                          # Punto de entrada (toggle USE_CUSTOMTKINTER)
├── app.py                           # App wrapper
├── debug_config.py                  # Flags de debug globales (DEBUG_SCRAPING_PIPELINE, DEBUG_LLM_MARKDOWN, DEBUG_CRAWL4AI_VERBOSE, DEBUG_FUZZY_MATCHING, DEBUG_EXCEL_PARSING)
├── .env                             # Variables de entorno (no en git)
│
├── Core/
│   ├── comparador.py                # Fuzzy matching (scores, print debug)
│   ├── comparador_multiperiodo.py   # Lógica multi-periodo ⭐
│   ├── controller.py                # Fachada de servicios + GestorService (singleton recargable) ⭐
│   ├── excel_resolver.py            # Resuelve qué Excel cargar al arrancar
│   ├── gestor_datos.py              # Orquestador Excel/Web
│   ├── periodo_utils.py             # Utilidades de periodos
│   ├── servicio_habitaciones.py     # Servicio de habitaciones
│   └── services/
│       └── config_service.py        # Persistencia de config.json (último Excel, etc.) ⭐
│
├── Models/
│   ├── hotelExcel.py                # HotelExcel (Pydantic)
│   ├── hotelWeb.py                  # HotelWeb (Pydantic)
│   ├── habitacion_unificada.py      # HabitacionUnificada
│   └── periodo.py                   # Periodo
│
├── ExtractorDatos/
│   ├── extractor.py                 # Parser Excel (openpyxl) ⭐
│   ├── extractor_old.py             # Legacy
│   ├── utils.py                     # Parsing de fechas (print debug)
│   └── contexto_extraccion.py
│
├── Deploy/
│   ├── build_manifest.py           # Manifest declarativo del bundle (estilo package.json) ⭐
│   ├── smoke_test.py               # Checks post-build de módulos críticos (--self-test) ⭐
│   ├── crawl_compare.spec          # Config PyInstaller (lee de build_manifest.py)
│   ├── startup_check.py            # Checks de entorno al arrancar (.env, Chromium)
│   ├── build.bat                   # Script de build + corre smoke test post-compilación
│   └── __init__.py
│
├── ScrawlingChinese/
│   ├── crawler.py                   # Scraper async (Crawl4AI + DeepSeek-R1) ⭐
│   ├── config.py                    # Configuración scraper
│   └── utils/
│       └── scraper_utils.py
│
├── UI/
│   ├── interfaz_ctk.py              # CrawlCompareGUI — interfaz principal ⭐
│   │
│   ├── state/
│   │   ├── event_bus.py             # EventBus pub/sub ⭐
│   │   └── app_state.py             # AppState centralizado ⭐
│   │
│   ├── components/
│   │   ├── ctk_base_component.py    # Base para CTk* ⭐
│   │   ├── ctk_card.py              # Card container
│   │   ├── ctk_custom_dropdown.py   # Dropdown personalizado
│   │   ├── ctk_date_input.py        # Input de fechas
│   │   ├── ctk_labeled_combobox.py  # Combobox con label
│   │   ├── ctk_labeled_entry.py     # Entry con label
│   │   ├── ctk_periodos_panel.py    # Panel de periodos ⭐
│   │   ├── ctk_precio_panel.py      # Panel de precio ⭐
│   │   └── ctk_progress_panel.py    # Panel de progreso
│   │
│   ├── views/
│   │   ├── vista_resultados.py      # Tabla comparativa multi-periodo ⭐
│   │   ├── modal_email.py           # Modal para enviar email
│   │   └── config_modal.py          # Modal de configuración (4 pestañas)
│   │
│   ├── controllers/
│   │   ├── controlador_hotel.py     # Carga hoteles/habitaciones (re-carga en excel.loaded) ⭐
│   │   ├── controlador_precios.py   # Calcula precio según periodos ⭐
│   │   ├── controlador_comparacion.py  # Orquesta comparación ⭐
│   │   ├── controlador_validacion.py   # Orquesta validators (devuelve ValidationResult)
│   │   └── validators/
│   │       ├── base.py              # ValidationError, ValidationResult, Validator (Protocol)
│   │       ├── fechas_validator.py  # Formato/orden de fechas
│   │       ├── campos_validator.py  # Campos completos
│   │       └── excel_validator.py   # Excel cargado (defensivo)
│   │
│   ├── styles/
│   │   ├── colors.py                # Paleta de colores (PRIMARY, SECONDARY, semánticos, neutrales)
│   │   ├── button_styles.py         # Helpers primary_button() / secondary_button()
│   │   ├── typography.py            # Tipografías
│   │   ├── fonts.py
│   │   └── spacing.py               # Espaciados
│   │
│   └── utils/
│       ├── scrollbar_utils.py
│       └── validadores_fecha.py
│
├── Data/
│   └── Extracto.xls                 # Datos Excel (no en git)
│
└── Tests/
    ├── testExtractor2.py
    ├── test_email_modal_visual.py
    ├── test_error_ui_visual.py
    ├── test_extractor.py
    ├── test_gmtp_direct.py
    ├── test_gmtp_validation.py
    └── test_periodos_ui.py
```
