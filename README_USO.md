# Crawl-Compare - Comparador de Precios

Aplicación para comparar precios de habitaciones entre datos de Excel y scraping web.

## 🚀 Inicio Rápido

### Ejecutar la aplicación

Desde la raíz del proyecto:

```bash
python app.py
```

### Alternativas

También podés ejecutar directamente:

```bash
python UI/interfaz.py
```

O desde el archivo de tests:

```bash
python main.py
```

## 📁 Estructura del Proyecto

```
Crawl-Compare/
├── app.py                  ← PUNTO DE ENTRADA PRINCIPAL ⭐
├── main.py                 ← Punto de entrada alternativo (testing)
│
├── UI/                     ← Interfaz de usuario
│   ├── interfaz.py         ← Aplicación principal
│   │
│   ├── state/              ← Gestión de estado
│   │   ├── event_bus.py    ← Sistema de eventos pub/sub
│   │   └── app_state.py    ← Estado centralizado
│   │
│   ├── styles/             ← Estilos y temas
│   │   └── fonts.py        ← Gestor de fuentes
│   │
│   ├── components/         ← Componentes reutilizables
│   │   ├── date_input.py
│   │   ├── labeled_combobox.py
│   │   ├── periodos_panel.py
│   │   ├── precio_panel.py
│   │   └── entrada_etiquetada.py
│   │
│   ├── views/              ← Vistas compuestas
│   │   ├── formulario_seleccion_hotel.py
│   │   ├── formulario_reserva.py
│   │   └── vista_resultados.py
│   │
│   └── controllers/        ← Lógica de negocio
│       ├── controlador_hotel.py
│       ├── controlador_validacion.py
│       └── controlador_comparacion.py
│
├── Core/                   ← Lógica de negocio central
│   ├── controller.py       ← Controlador principal
│   ├── gestor_datos.py     ← Gestión de datos
│   ├── comparador.py       ← Algoritmos de comparación
│   └── periodo_utils.py    ← Utilidades de periodos
│
├── Models/                 ← Modelos de datos (Pydantic)
│   ├── hotelExcel.py       ← Modelos para datos de Excel
│   ├── hotelWeb.py         ← Modelos para datos web
│   └── periodo.py          ← Modelo de periodo
│
├── ExtractorDatos/         ← Extracción de datos de Excel
│   ├── extractor.py
│   └── utils.py
│
├── ScrawlingChinese/       ← Web scraping
│   ├── crawler.py
│   ├── config.py
│   └── utils/
│
├── Tests/                  ← Tests y validaciones
│   ├── test_extractor.py
│   └── testExtractor2.py
│
└── Data/                   ← Datos de entrada
    └── Extracto_prueba2.xlsx
```

## 🎯 Uso de la Aplicación

1. **Seleccionar Hotel**: Elegí el hotel de la lista desplegable
2. **Seleccionar Edificio** (si aplica): Algunos hoteles tienen edificios
3. **Seleccionar Habitación**: Elegí la habitación a comparar
4. **Ingresar Fechas**: Fecha de entrada y salida (DD-MM-AAAA)
5. **Ingresar Huéspedes**: Cantidad de adultos y niños
6. **Ejecutar Comparación**: Click en "Ejecutar comparación"
7. **Ver Resultados**: Se muestra la comparación con la web
8. **Enviar Email** (opcional): Si hay diferencias, podés enviar un email

## 🏗️ Arquitectura

La aplicación sigue una arquitectura **MVC Event-Driven**:

- **State Layer**: Gestión centralizada del estado de la aplicación
- **Components Layer**: Componentes UI reutilizables y autocontenidos
- **Views Layer**: Vistas compuestas por múltiples componentes
- **Controllers Layer**: Lógica de negocio separada de la UI
- **Core Layer**: Servicios y utilidades compartidas

### Sistema de Eventos

La aplicación usa un **EventBus** para comunicación desacoplada:

- `hotel_changed`: Cuando cambia la selección de hotel
- `edificio_changed`: Cuando cambia la selección de edificio
- `habitacion_changed`: Cuando cambia la selección de habitación
- `comparison_started`: Al iniciar comparación
- `comparison_completed`: Al completar comparación exitosamente
- `comparison_error`: Si ocurre un error en la comparación

## 🧪 Testing

### Modo Debug del EventBus

Para ver todos los eventos que se emiten, descomentá esta línea en `interfaz.py`:

```python
# self.event_bus.enable_debug()  # Descomentar para debugging
```

### Tests Unitarios

Ejecutar tests:

```bash
python -m pytest Tests/
```

## 📝 Dependencias

- **tkinter**: GUI (incluido en Python)
- **pydantic**: Validación de modelos
- **openpyxl**: Lectura de Excel
- **rapidfuzz**: Fuzzy matching para comparación
- **beautifulsoup4**: Web scraping
- **aiohttp**: Requests asíncronos

## 🔧 Desarrollo

### Agregar un Nuevo Componente

1. Crear archivo en `UI/components/`
2. Heredar de `BaseComponent`
3. Implementar `_setup_ui()`, `get_value()`, `set_value()`
4. Exportar en `UI/components/__init__.py`

### Agregar un Nuevo Controlador

1. Crear archivo en `UI/controllers/`
2. Recibir `estado_app` y `event_bus` en constructor
3. Suscribirse a eventos necesarios
4. Emitir eventos cuando corresponda
5. Exportar en `UI/controllers/__init__.py`

## 📧 Contacto

Desarrollado por German Lucero
Email: gerlucero1997@gmail.com

---

**Versión**: 2.0 (Reestructurada)
**Última actualización**: Diciembre 2024
