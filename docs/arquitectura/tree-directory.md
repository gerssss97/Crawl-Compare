# Tree Directory — Crawl-Compare

Estructura completa del proyecto. Actualizar cuando se agreguen/muevan archivos.

> ⭐ = archivos clave / más modificados

```
Hoteles/
├── main.py                          # Punto de entrada
├── app.py                           # App wrapper
├── debug_config.py                  # Flags de debug globales
├── .env                             # Variables de entorno (no en git)
│
├── Core/
│   ├── comparador.py                # Fuzzy matching (scores, print debug)
│   ├── comparador_multiperiodo.py   # Lógica multi-periodo ⭐
│   ├── controller.py                # Fachada de servicios + GestorService (singleton recargable) ⭐
│   ├── excel_resolver.py            # Resuelve qué Excel cargar al arrancar
│   ├── gestor_datos.py              # Orquestador Excel/Web
│   ├── periodo_utils.py             # Utilidades de periodos
│   ├── email_templates.py           # Template predeterminado de email (DEFAULT_EMAIL_TEMPLATE)
│   ├── servicio_habitaciones.py     # Servicio de habitaciones
│   └── services/
│       ├── config_service.py        # Persistencia de config.json (último Excel, etc.) ⭐
│       └── email_senders.py         # MailtoSender — abre cliente de email del SO vía mailto:
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
│   ├── utils.py                     # Parsing de fechas
│   └── contexto_extraccion.py
│
├── Deploy/
│   ├── build_manifest.py            # Manifest declarativo del bundle (estilo package.json) ⭐
│   ├── smoke_test.py                # Checks post-build de módulos críticos (--self-test) ⭐
│   ├── crawl_compare.spec           # Config PyInstaller (lee de build_manifest.py)
│   ├── startup_check.py             # Checks de entorno al arrancar (.env, Chromium)
│   ├── build.bat                    # Script de build + corre smoke test post-compilación
│   └── __init__.py
│
├── ScrawlingChinese/
│   ├── crawler.py                   # crawl_alvear(), crawl_faena(), make_scraper(), CRAWLERS ⭐
│   ├── config.py                    # Configuración legacy (backward compat)
│   ├── site_configs/                # Strategy 1: config específica por hotel
│   │   ├── __init__.py
│   │   ├── alvear.py                # AlvearConfig (DOM selectors pendientes)
│   │   └── faena.py                 # FaenaConfig (DOM selectors del handoff) ⭐
│   ├── parsers/                     # Strategy 2: método de extracción
│   │   ├── __init__.py
│   │   ├── base.py                  # Protocol RoomParser
│   │   ├── llm_parser.py            # LLMParser: Groq/LLM vía Crawl4AI
│   │   └── dom_parser.py            # DOMParser: BeautifulSoup sin LLM
│   └── utils/
│       ├── hotel_scraper.py         # HotelScraper: Template Method (flujo fijo) ⭐
│       └── scraper_utils.py         # get_browser_config(), fechas_validas(), helpers
│
├── UI_qt/                           # Interfaz principal PySide6 ⭐
│   ├── interfaz_qt.py               # MainWindow — ventana principal ⭐
│   ├── spike_resize.py              # Spike de layout 2-columnas (legacy, no prod)
│   ├── spike_visual.py              # Mini test visual (legacy, no prod)
│   ├── test_fase1_headless.py       # Test headless Fase 1 (legacy, no prod)
│   │
│   ├── assets/
│   │   ├── app_icon.ico             # Ícono de la aplicación (titlebar + taskbar)
│   │   ├── convert_icons.py         # Script one-shot: convierte SVGs de Feather a PNGs light/dark
│   │   └── icons/
│   │       ├── *.svg                # SVGs originales de Feather Icons
│   │       ├── light/               # PNGs trazo #374151 (sobre fondo claro)
│   │       └── dark/                # PNGs trazo #F9FAFB (sobre fondo oscuro)
│   │
│   ├── controllers/                 # Lógica de negocio y orquestación ⭐
│   │   ├── __init__.py
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
│   ├── services/
│   │   ├── __init__.py
│   │   └── historial_service.py     # CRUD del historial de comparaciones (persiste en config.json)
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── event_bus.py             # EventBus pub/sub ⭐
│   │   ├── app_state.py             # AppState centralizado ⭐
│   │   ├── event_bridge.py          # Puente EventBus → Qt Signals (thread-safe)
│   │   └── observable.py            # ObservableVar: reemplazo de tk.Variable con API Qt Signal
│   │
│   ├── styles/
│   │   ├── __init__.py              # Re-exporta todo: Palette, build_qss, constantes, Colors, Typography, Spacing
│   │   ├── palette.py               # Tokens de color dual-mode (light/dark) ⭐
│   │   ├── constants.py             # Constantes de dimensión Qt-específicas ⭐
│   │   ├── stylesheet.py            # Generador del QSS global desde las constantes ⭐
│   │   ├── colors.py                # Paleta legacy (Colors — usada en spike y stylesheet)
│   │   ├── spacing.py               # Espaciados y radios (Spacing)
│   │   ├── typography.py            # Tipografías (Typography)
│   │   ├── qt_icons.py              # Icons helper — QIcon desde PNG de Feather (light/dark)
│   │   ├── icons_gen.py             # Genera chevrons PNG en memoria para QSS
│   │   ├── theme.py                 # Paletas dual-mode (theme helper legacy)
│   │   └── _generated/              # Chevrons pre-generados (usados en build)
│   │
│   ├── utils/
│   │   ├── __init__.py              # normalizar_hotel_nombre
│   │   └── validadores_fecha.py     # Validadores de fechas DD-MM-AAAA
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   ├── qt_config_modal.py       # Modal de configuración (QDialog + QTabWidget) ⭐
│   │   ├── qt_historial_modal.py    # Modal de historial de comparaciones previas ⭐
│   │   └── qt_resultados_modal.py   # Modal de resultado de una comparación (QDialog no-modal) ⭐
│   │
│   └── widgets/
│       ├── __init__.py
│       ├── qt_labeled_combo.py      # Combo con label + typeahead + ObservableVar ⭐
│       ├── qt_date_edit.py          # Campo de fecha QDateEdit + escritura manual
│       ├── qt_form_reserva.py       # Card 'Selección de Reserva'
│       ├── qt_form_fechas.py        # Card 'Fechas y Huéspedes'
│       ├── qt_precio_panel.py       # Panel de precio con desglose multiperiodo ⭐
│       ├── qt_periodos_panel.py     # Panel de periodos con filas expandibles ⭐
│       ├── qt_vista_resultados.py   # Vista de resultados (QTextEdit HTML readonly)
│       ├── qt_progress_panel.py     # Panel de progreso del scraping
│       └── qt_spin_stepper.py       # Widget stepper [-] value [+]
│
├── Data/
│   └── Extracto.xls                 # Datos Excel (no en git)
│
└── Tests/
    ├── testExtractor2.py
    ├── test_error_ui_visual.py
    ├── test_extractor.py
│   │   ├── hotel_scraper.py  # Hotel scraper
│   ├── requirements.txt  # Requirements
    └── test_periodos_ui.py
│   ├── tree-directory.md  # Tree directory
│   ├── qt_interact_combo_popup.py  # Qt interact combo popup
│   ├── feedback_run_skill_gui_blocking.md  # Feedback run skill gui blocking
│   ├── HANDOFF-combo-popup.md  # Handoff combo popup
│   ├── diagnostico_faena.py  # Diagnostico faena
│   ├── analizar_faena.py  # Analizar faena
│   ├── diagnostico_faena_v2.py  # Diagnostico faena v2
│   ├── faena_browser.html  # Faena browser
│   ├── extraer_rooms.py  # Extraer rooms
│   ├── extraer_cards.py  # Extraer cards
│   ├── HANDOFF-scraper-faena.md  # Handoff scraper faena
│   ├── multi-hotel-strategy-pattern.md  # Multi hotel strategy pattern
│   ├── alvear.py  # Alvear
│   ├── llm_parser.py  # Extrae habitaciones mandando el HTML al LLM (Groq). Flujo actual del Alvear.
│   ├── dom_parser.py  # Extrae habitaciones con BeautifulSoup sobre HTML crudo. Sin LLM.
│   ├── test_scraper.py  # Extrae --parser=llm|dom de la lista de args y devuelve (args_restantes, parser_type).
│   ├── test_firefox_accor.py  # Test firefox accor
```

---

## docs/problemas/

Bitácoras de investigación por problema concreto. Ver [README](../problemas/README.md).

```
docs/problemas/
├── README.md                        # Índice con tabla de todos los issues
└── scraper/
    ├── antibot-tls.md               # TLS fingerprinting de api.accor.com ✅
    ├── firefox-crawl4ai.md          # Bug Crawl4AI 0.4.x con Firefox ✅
│   ├── crawl-dispatch-hardcoded.md  # Crawl dispatch hardcoded
    └── currency-market.md           # EUR/USD/ARS, pos geolocation, taxes 🔧
│   ├── diag_accor_currency.py  # Diag accor currency
│   ├── diag_accor_pos.py  # Hace un fetch directo usando Playwright Firefox (bypass TLS fingerprinting).
│   ├── diag_accor_markets.py  # Diag accor markets
│   ├── taxes-y-desacople-precio-web.md  # Taxes y desacople precio web
│   ├── progress.md  # Progress
│   ├── task-1-brief.md  # Task 1 brief
│   ├── task-1-report.md  # Retorna el precio total (base + impuestos) para un combo.
│   ├── task-2-brief.md  # Task 2 brief
│   ├── task-2-report.md  # Retorna el precio total (base + impuestos) para una habitaciÃ³n.
│   ├── task-3-brief.md  # Task 3 brief
│   ├── task-3-report.md  # Retorna el precio total despuÃ©s de aplicar filtro de breakfast.
│   ├── task-4-brief.md  # Task 4 brief
│   ├── task-4-report.md  # Task 4 report
│   ├── task-5-brief.md  # Task 5 brief
│   ├── task-5-report.md  # Task 5 report
│   ├── task-6-brief.md  # Task 6 brief
│   ├── task-6-report.md  # Task 6 report
│   ├── task-7-brief.md  # Task 7 brief
│   ├── task-7-report.md  # Task 7 report
│   ├── task-8-brief.md  # Task 8 brief
│   ├── task-8-report.md  # Task 8 report
│   ├── HANDOFF-dispatch-faena-wiring.md  # Handoff dispatch faena wiring
```
