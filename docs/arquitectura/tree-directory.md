# Tree Directory — Crawl-Compare

Estructura completa del proyecto. Actualizar cuando se agreguen/muevan archivos.

> ⭐ = archivos clave / más modificados

```
Hoteles/
├── main.py                          # Punto de entrada (toggle USE_CUSTOMTKINTER)
├── app.py                           # App wrapper
├── .env                             # Variables de entorno (no en git)
│
├── Core/
│   ├── comparador.py                # Fuzzy matching (scores, print debug)
│   ├── comparador_multiperiodo.py   # Lógica multi-periodo ⭐
│   ├── controller.py                # Fachada de servicios
│   ├── gestor_datos.py              # Orquestador Excel/Web
│   ├── periodo_utils.py             # Utilidades de periodos
│   └── servicio_habitaciones.py     # Servicio de habitaciones
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
│   │   └── vista_resultados.py      # Tabla comparativa multi-periodo ⭐
│   │
│   ├── controllers/
│   │   ├── controlador_hotel.py     # Carga hoteles/habitaciones ⭐
│   │   ├── controlador_precios.py   # Calcula precio según periodos ⭐
│   │   ├── controlador_comparacion.py  # Orquesta comparación ⭐
│   │   └── controlador_validacion.py   # Valida inputs
│   │
│   ├── styles/
│   │   ├── colors.py                # Paleta de colores
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
