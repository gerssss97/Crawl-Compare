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
│   │   ├── ctk_base_component.py        # Base para CTk* ⭐
│   │   ├── ctk_card.py                  # Card container
│   │   ├── ctk_custom_dropdown.py       # Dropdown personalizado
│   │   ├── ctk_date_input.py            # Input de fechas
│   │   ├── ctk_labeled_combobox.py      # Combobox con label
│   │   ├── ctk_labeled_entry.py         # Entry con label
│   │   ├── ctk_modal_advertencia_gaps.py  # Modal de advertencia para gaps de cobertura
│   │   ├── ctk_inline_suggester.py      # Autocomplete inline para tk.Text (trigger_char, n, options)
│   │   ├── ctk_periodos_panel.py        # Panel de periodos ⭐
│   │   ├── ctk_precio_panel.py          # Panel de precio ⭐
│   │   ├── ctk_progress_panel.py        # Panel de progreso
│   │   └── ctk_text_editor.py           # CTkTextbox con shortcuts de edición + autocomplete opcional
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── historial_service.py     # CRUD del historial de comparaciones (persiste en config.json)
│   │
│   ├── views/
│   │   ├── vista_resultados.py      # Tabla comparativa multi-periodo ⭐
│   │   ├── resultados_modal.py      # Modal autónomo de resultados (uno por comparación) ⭐
│   │   ├── config_modal.py          # Modal de configuración (4 pestañas)
│   │   └── historial_modal.py       # Modal de historial de comparaciones previas
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
│   │   ├── icons.py                 # Icons singleton — carga CTkImage de cada ícono una sola vez
│   │   ├── typography.py            # Tipografías
│   │   ├── fonts.py
│   │   └── spacing.py               # Espaciados
│   │
│   ├── assets/
│   │   ├── convert_icons.py         # Script one-shot: convierte SVGs de Feather a PNGs light/dark
│   │   └── icons/
│   │       ├── *.svg                # SVGs originales de Feather Icons
│   │       ├── light/               # PNGs trazo #374151 (sobre fondo claro)
│   │       └── dark/                # PNGs trazo #F9FAFB (sobre fondo oscuro)
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
    ├── test_error_ui_visual.py
    ├── test_extractor.py
│   │   ├── ctk_inline_suggester.py  # CTkInlineSuggester â€” popup de sugerencias inline para tk.Text.
│   ├── error_logger.py  # Logger persistente para .exe: tee de stdout/stderr + excepthook con messagebox.
│   ├── splash.py  # Splash screen de arranque del .exe: ventana tk pura con label de estado y barra indeterminada.
│   ├── _verif_urls.py  # Verificacion temporal: renderiza el texto del resultado mixto y mixto-OK.
│   │   ├── observable.py  # ObservableVar: reemplazo de tk.Variable con la misma API, respaldado por Signal de Qt.
│   │   ├── theme.py  # Paletas dual-mode (light/dark) y generador de QSS desde las constantes del proyecto.
│   │   ├── event_bridge.py  # Puente EventBus -> Qt Signals (thread-safe). Fase 6 del plan de migracion.
│   │   ├── qt_resultados_modal.py  # Modal de resultado de una comparacion (QDialog no-modal, uno por comparison_id).
│   │   ├── qt_historial_modal.py  # Modal de historial de comparaciones previas (QDialog).
│   │   ├── qt_config_modal.py  # Modal de configuracion (QDialog + QTabWidget). Porta ConfigModal.
│   ├── test_resultado_qt_visual.py  # Test visual Qt: simula resultados de comparacion y muestra el modal PySide6 completo.
│   ├── startup_worker.py  # Worker QThread para correr run_checks() sin bloquear el hilo principal.
    └── test_periodos_ui.py
│   ├── inline-suggester.md  # Inline suggester
│   ├── cheu-fijate-que-el-serene-aurora.md  # Cheu fijate que el serene aurora
│   ├── splash-screen-y-logging.md  # Splash screen y logging
│   ├── check_build_deps.py  # Hook PostToolUse: avisa cuando se modifican archivos del build (manifest, spec, assets).
│   ├── TODO.md  # Todo
│   ├── optimized-beaming-hare.md  # Optimized beaming hare
│   ├── distribucion-handoff.md  # Distribucion handoff
│   ├── plan-instalador-diferenciado.md  # Plan instalador diferenciado
│   ├── mira-docs-deploy-build-deploy-md-y-docs-luminous-petal.md  # Mira docs deploy build deploy md y docs luminous petal
│   ├── resize_probe.py  # Mide el costo de re-layout durante un resize simulado de la ventana principal.
│   ├── resize_bisect.py  # BisecciÃ³n del costo de re-layout en resize.
│   ├── feedback_explicar_solucion_sin_modal.md  # Feedback explicar solucion sin modal
│   ├── resize_drawmethod.py  # Compara el costo de resize segun el preferred_drawing_method de CTk.
│   ├── resize_subtree.py  # Mide el impacto de ocultar subarboles durante el resize (opcion A').
│   ├── resize_placeholder.py  # Mide la opcion A' real: durante el drag, reemplazar todo el content_frame
│   ├── HANDOFF.md  # Handoff
│   ├── plan-migracion-gui.md  # Plan migracion gui
│   ├── project-migracion-pyside6.md  # Project migracion pyside6
│   ├── project-conda-env-crawler.md  # Project conda env crawler
│   ├── spike_resize.py  # Spike de Fase 0: prototipo PySide6 que reproduce el layout 2-columnas y mide el resize.
│   ├── troubleshooting-qt.md  # Troubleshooting qt
│   ├── spike_visual.py  # Mini test visual de Fase 0: abre la ventana del spike y la deja abierta para probar el resize a mano.
│   ├── test_fase1_headless.py  # Test headless de Fase 1: AppState v2 (sin Tkinter) + controladores reales sin cambios.
│   ├── interfaz_qt.py  # Ventana principal PySide6 (Fase 2: shell + estilo).
│   ├── qt_labeled_combo.py  # Combo con label arriba, sincronizado con una ObservableVar del AppState.
│   ├── qt_date_edit.py  # Campo de fecha: QDateEdit con calendario desplegable + escritura manual.
│   ├── qt_form_reserva.py  # Card 'Seleccion de Reserva': hotel + edificio (dinamico) + habitacion.
│   ├── qt_form_fechas.py  # Card 'Fechas y Huespedes': fecha entrada/salida (con validacion cruzada) + adultos/ninos.
│   ├── qt_precio_panel.py  # Panel de precio con desglose multiperiodo (spec aprobada en Figma).
│   ├── qt_periodos_panel.py  # Panel de periodos con filas expandibles (spec aprobada en Figma).
│   ├── qt_vista_resultados.py  # Vista de resultados de comparacion: QTextEdit readonly que renderiza HTML.
│   ├── qt_progress_panel.py  # Panel de progreso del scraping: label de estado + QProgressBar.
│   ├── screenshot.py  # Screenshot
│   ├── app-screenshot.md  # App screenshot
│   ├── qt_spin_stepper.py  # Widget stepper [-] value [+] para cantidades pequeÃ±as (adultos, niÃ±os).
│   ├── historial-viewer-persistido.md  # Historial viewer persistido
```
