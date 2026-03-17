# Plan: Sistema Escalable de Detección de Disponibilidad

## Contexto

El scraper actual falla cuando un hotel **no tiene disponibilidad** para ciertas fechas, porque:

1. **Problema técnico detectado**: El selector `.thumb-cards_products` solo aparece cuando HAY habitaciones disponibles. Cuando no hay, aparece `.product-availability-container_unavailableMessage` en su lugar.

2. **Error manifestado**: Timeout de 30s esperando el selector → el scraping falla completamente, aunque el sitio cargó bien y retornó una respuesta válida ("sin disponibilidad").

3. **Limitación actual**: El sistema trata "sin disponibilidad" como un error técnico genérico (`precio_excel = "Error"`), sin distinguirlo de timeouts reales, CSS selector cambiado, o rate limiting.

4. **Necesidad de escalabilidad**: La solución debe funcionar para **cualquier hotel**, no solo Alvear. Cada sitio puede usar distintos selectores y mensajes de "sin disponibilidad".

## Objetivos

✅ **Detección flexible de página cargada**: Wait-for que acepte múltiples estados válidos (habitaciones disponibles, sin disponibilidad, errores del sitio)

✅ **Distinguir estados de negocio**: Diferenciar "sin disponibilidad" de "error técnico" en los modelos y UI

✅ **Escalabilidad multi-sitio**: Sistema configurable que funcione para distintos hoteles sin hardcodear selectores

✅ **UI clara**: Mostrar visualmente al usuario los 4 estados posibles:
- ✅ OK (precios coinciden)
- ❌ DIFF (discrepancia de precio)
- ⚠️ SIN_DISPONIBILIDAD (hotel sin habitaciones)
- 🔴 ERROR (timeout, CSS cambió, etc.)

## Approach Recomendado

### Fase 1: Wait-for Flexible (Soluciona timeout inmediato)

**Archivos a modificar:**
- `Hoteles/ScrawlingChinese/utils/scraper_utils.py` (línea 201)

**Cambios:**

1. **Crear función `get_flexible_wait_for()`** que retorne un JavaScript con múltiples selectores:

```python
def get_flexible_wait_for():
    """
    Wait-for que acepta múltiples estados válidos de página.
    Retorna True si encuentra:
    - Contenedor de habitaciones (disponibilidad positiva)
    - Mensaje de sin disponibilidad (disponibilidad negativa)
    - Mensaje de error del sitio
    - Página con contenido sustancial (fallback)
    """
    return """() => {
        // CASO 1: Contenido positivo (hay habitaciones)
        const positiveSelectors = [
            '.thumb-cards_products',      // Synxis (Alvear)
            '.room-list',                 // Común en booking engines
            '.hotel-room',                // Genérico
            '[class*="room"]',            // Cualquier clase con "room"
            '[class*="product"]',         // Cualquier clase con "product"
        ];

        // CASO 2: Contenido negativo (sin disponibilidad)
        const negativeSelectors = [
            '.product-availability-container_unavailableMessage',  // Synxis
            '[class*="unavailable"]',                              // Genérico
            '[class*="no-availability"]',                          // Común
            '[class*="sold-out"]',                                 // Hoteles
        ];

        // CASO 3: Mensajes de error comunes
        const errorSelectors = [
            '[class*="error"]',
            '[class*="alert"]',
        ];

        // Si encuentra CUALQUIERA, consideramos que la página cargó
        const allSelectors = [...positiveSelectors, ...negativeSelectors, ...errorSelectors];
        for (const sel of allSelectors) {
            if (document.querySelector(sel)) {
                return true;
            }
        }

        // FALLBACK: Si el body tiene contenido considerable
        const bodyLength = document.body?.innerHTML?.length || 0;
        if (bodyLength > 10000) {
            console.log('[WAIT-FOR] Fallback: body length', bodyLength);
            return true;
        }

        return false;
    }"""
```

2. **Modificar `fetch_and_process_page()`** para usar el wait-for flexible:

```python
# Línea 201 - ANTES:
wait_for="css:.thumb-cards_products",

# Línea 201 - DESPUÉS:
wait_for=get_flexible_wait_for(),
```

**Beneficio inmediato**: El scraping ya no fallará con timeout cuando el hotel no tenga disponibilidad.

---

### Fase 2: Detección de "Sin Disponibilidad" (Mejora lógica de negocio)

**Archivos a modificar:**
- `Hoteles/Models/hotelWeb.py`
- `Hoteles/ScrawlingChinese/utils/scraper_utils.py` (función `procesar_resultado_scraping`)

**Cambios:**

1. **Extender modelo `HotelWeb`** con flag de disponibilidad:

```python
# En Models/hotelWeb.py línea 15-17
class HotelWeb(BaseModel):
    habitacion: List[HabitacionWeb]
    detalles: str
    sin_disponibilidad: bool = False  # NUEVO campo
```

2. **Detectar "sin disponibilidad" en `procesar_resultado_scraping()`**:

```python
# En scraper_utils.py línea 107 - AGREGAR antes del flujo normal
async def procesar_resultado_scraping(result):
    # NUEVO: Detectar si no hay disponibilidad
    if result.html and 'product-availability-container_unavailableMessage' in result.html:
        print("ℹ️  Hotel sin disponibilidad para las fechas seleccionadas")
        return HotelWeb(
            detalles="Alvear Palace Hotel",  # TODO: parametrizar nombre hotel
            habitacion=[],  # Lista vacía
            sin_disponibilidad=True
        )

    # Flujo normal existente...
    if not (result.success and result.extracted_content):
        print(f"Error: No hay contenido extraído...")
        return None
```

**Keywords genéricas para detección multi-sitio:**
```python
# Hacer la detección más escalable
UNAVAILABLE_KEYWORDS = [
    'unavailable',
    'sold out',
    'no availability',
    'no rooms available',
    'fully booked',
]

# Buscar cualquiera en HTML
html_lower = result.html.lower()
if any(keyword in html_lower for keyword in UNAVAILABLE_KEYWORDS):
    return HotelWeb(..., sin_disponibilidad=True)
```

---

### Fase 3: Estados Diferenciados en ResultadoPeriodo (Modelo de resultados)

**Archivos a modificar:**
- `Hoteles/Core/comparador_multiperiodo.py` (clase `ResultadoPeriodo`)

**Cambios:**

1. **Agregar campo `estado` a `ResultadoPeriodo`**:

```python
# Línea 49-62 - MODIFICAR clase
class ResultadoPeriodo:
    """Resultado de comparación para un periodo específico."""

    def __init__(self, periodo: Periodo, precio_excel: float | str,
                 precio_web: float, diferencia: float, coincide: bool,
                 estado: str = "OK",  # NUEVO campo
                 fecha_inicio_real: date = None, fecha_fin_real: date = None):
        self.periodo = periodo
        self.precio_excel = precio_excel
        self.precio_web = precio_web
        self.diferencia = diferencia
        self.coincide = coincide
        self.estado = estado  # Valores: "OK" | "DIFF" | "SIN_DISPONIBILIDAD" | "ERROR"
        self.fecha_inicio_real = fecha_inicio_real
        self.fecha_fin_real = fecha_fin_real
```

2. **Mapear estados en `comparar_multiperiodo()`**:

```python
# Línea 207-216 - Al crear ResultadoPeriodo exitoso
resultado_periodo = ResultadoPeriodo(
    periodo=periodo,
    precio_excel=precio_periodo,
    precio_web=precio_web,
    diferencia=diferencia,
    coincide=coincide,
    estado="OK" if coincide else "DIFF",  # NUEVO
    fecha_inicio_real=fecha_inicio_real,
    fecha_fin_real=fecha_fin_real,
)
```

3. **Detectar "sin disponibilidad" cuando habitación no existe** (línea 159-190):

```python
# Línea 170-190 - Cuando no es primer periodo
if idx > 0:
    habitacion_actual = None
    for hab in hotel_web.habitacion:
        if hab.nombre == habitacion_web_matcheada.nombre:
            habitacion_actual = hab
            break

    if not habitacion_actual:
        # ANTES: raise ValueError(...)
        # DESPUÉS: Crear resultado con estado SIN_DISPONIBILIDAD
        print(f"⚠️ Habitación '{habitacion_web_matcheada.nombre}' no encontrada en periodo {idx}")

        resultados_periodos.append(ResultadoPeriodo(
            periodo=periodo,
            precio_excel=precio_periodo,
            precio_web=0.0,
            diferencia=0.0,
            coincide=False,
            estado="SIN_DISPONIBILIDAD",  # NUEVO estado
            fecha_inicio_real=fecha_inicio_real,
            fecha_fin_real=fecha_fin_real,
        ))
        continue  # Continuar con siguiente periodo
```

4. **Detectar cuando `hotel_web.sin_disponibilidad=True`** (primer periodo):

```python
# Línea 145-156 - Después del scraping
hotel_web = await dar_hotel_web(...)

# NUEVO: Detectar si el hotel retornó sin disponibilidad
if hotel_web and hotel_web.sin_disponibilidad:
    print(f"⚠️ Hotel sin disponibilidad para periodo {idx}")
    resultados_periodos.append(ResultadoPeriodo(
        periodo=periodo,
        precio_excel=precio_periodo,
        precio_web=0.0,
        diferencia=0.0,
        coincide=False,
        estado="SIN_DISPONIBILIDAD",
        fecha_inicio_real=fecha_inicio_real,
        fecha_fin_real=fecha_fin_real,
    ))
    continue  # Continuar con siguiente periodo

# Flujo normal...
if not hotel_web or not hotel_web.habitacion:
    raise ValueError(f"Error scrapeando periodo {idx}")
```

5. **Cambiar manejo de errores genéricos** (línea 229-247):

```python
except Exception as e:
    print(f"⚠️ ERROR técnico en periodo {idx}: {str(e)}")

    resultados_periodos.append(ResultadoPeriodo(
        periodo=periodo,
        precio_excel=precio_periodo,
        precio_web=0.0,
        diferencia=0.0,
        coincide=False,
        estado="ERROR",  # NUEVO: distinguir de SIN_DISPONIBILIDAD
        fecha_inicio_real=fecha_inicio_real,
        fecha_fin_real=fecha_fin_real,
    ))
```

---

### Fase 4: UI con Estados Diferenciados (Vista de resultados)

**Archivos a modificar:**
- `Hoteles/UI/views/vista_resultados.py`

**Cambios:**

1. **Mapear estados a emojis** (línea 185-214):

```python
# Línea 209 - ANTES:
estado_str = "✅ OK" if res_periodo.coincide else "❌ DIFF"

# Línea 209 - DESPUÉS:
estado_icons = {
    "OK": "✅ OK",
    "DIFF": "❌ DIFF",
    "SIN_DISPONIBILIDAD": "⚠️ NO DISPONIBLE",
    "ERROR": "🔴 ERROR TÉCNICO"
}
estado_str = estado_icons.get(res_periodo.estado, "❓ DESCONOCIDO")
```

2. **Actualizar status global** (línea 145-150):

```python
# ANTES:
if resultado.tiene_discrepancias:
    self.agregar("❌ DISCREPANCIAS DETECTADAS\n\n", tags=("bold",))
else:
    self.agregar("✅ TODO COINCIDE\n\n")

# DESPUÉS:
tiene_sin_disponibilidad = any(
    p.estado == "SIN_DISPONIBILIDAD" for p in resultado.periodos
)
tiene_errores = any(
    p.estado == "ERROR" for p in resultado.periodos
)

if tiene_errores:
    self.agregar("🔴 ERRORES TÉCNICOS DETECTADOS\n\n", tags=("bold",))
elif tiene_sin_disponibilidad:
    self.agregar("⚠️ ALGUNOS PERIODOS SIN DISPONIBILIDAD\n\n", tags=("bold",))
elif resultado.tiene_discrepancias:
    self.agregar("❌ DISCREPANCIAS DE PRECIO DETECTADAS\n\n", tags=("bold",))
else:
    self.agregar("✅ TODO COINCIDE\n\n")
```

---

### Fase 5: Escalabilidad Multi-Sitio (Configuración por hotel)

**Archivos a crear/modificar:**
- `Hoteles/ScrawlingChinese/utils/site_configs/` (nueva carpeta)
- `Hoteles/ScrawlingChinese/utils/site_configs/alvear_config.py` (nuevo)
- `Hoteles/ScrawlingChinese/utils/scraper_utils.py` (usar configs)

**Estructura propuesta:**

```python
# site_configs/alvear_config.py
class AlvearConfig:
    """Configuración específica para Alvear Palace Hotel (Synxis)."""

    BASE_URL = "https://be.synxis.com/"
    CSS_SELECTOR = ".thumb-cards_products .app_col-sm-12..."

    # Selectores de disponibilidad
    POSITIVE_SELECTORS = [
        '.thumb-cards_products',
        '.room-card',
    ]

    NEGATIVE_SELECTORS = [
        '.product-availability-container_unavailableMessage',
    ]

    # Keywords de sin disponibilidad en HTML
    UNAVAILABLE_KEYWORDS = [
        'unavailable',
        'not available',
        'sold out',
    ]

    @staticmethod
    def construir_params_busqueda(fecha_ingreso, fecha_egreso, adultos, ninos):
        return {
            "adult": adultos,
            "child": ninos,
            "arrive": fecha_ingreso,
            "depart": fecha_egreso,
            "chain": 24447,
            "hotel": 6933,
            "currency": "USD",
            # ...
        }
```

**Uso en `scraper_utils.py`:**

```python
def get_flexible_wait_for(site_config):
    """Genera wait-for basado en configuración del sitio."""
    positive = site_config.POSITIVE_SELECTORS
    negative = site_config.NEGATIVE_SELECTORS

    # Generar JavaScript dinámicamente
    return f"""() => {{
        const positiveSelectors = {json.dumps(positive)};
        const negativeSelectors = {json.dumps(negative)};
        // ... lógica de detección
    }}"""

# En fetch_and_process_page()
site_config = AlvearConfig()  # TODO: parametrizar
wait_for = get_flexible_wait_for(site_config)
```

**Futuro multi-hotel:**

```python
# site_configs/__init__.py
HOTEL_CONFIGS = {
    "alvear": AlvearConfig,
    "marriott": MarriottConfig,  # Futuro
    "hilton": HiltonConfig,      # Futuro
}

def get_hotel_config(hotel_nombre: str):
    if hotel_nombre not in HOTEL_CONFIGS:
        raise KeyError(f"Hotel '{hotel_nombre}' no configurado")
    return HOTEL_CONFIGS[hotel_nombre]()
```

---

## Archivos Críticos a Modificar

| Archivo | Líneas | Cambios |
|---------|--------|---------|
| `ScrawlingChinese/utils/scraper_utils.py` | 320 | Agregar `get_flexible_wait_for()`, modificar línea 201, detectar sin disponibilidad en `procesar_resultado_scraping()` |
| `Models/hotelWeb.py` | 84 | Agregar campo `sin_disponibilidad: bool = False` a `HotelWeb` |
| `Core/comparador_multiperiodo.py` | 271 | Agregar campo `estado` a `ResultadoPeriodo`, mapear estados en 3 lugares (líneas 145-156, 170-190, 207-216, 229-247) |
| `UI/views/vista_resultados.py` | 214 | Mapear estados a emojis (línea 209), actualizar status global (línea 145-150) |

**Archivos nuevos (opcional, Fase 5):**
- `ScrawlingChinese/utils/site_configs/alvear_config.py`
- `ScrawlingChinese/utils/site_configs/__init__.py`

---

## Patterns Reutilizables

### ✅ Ya existen en el código (reutilizar):

1. **Retry robusto**: `fetch_and_process_page()` ya tiene 3 intentos con backoff
2. **Validación granular**: `procesar_resultado_scraping()` ya valida habitación por habitación
3. **Multi-período resiliente**: Si un periodo falla, continúa con los demás
4. **Event-driven UI**: EventBus ya emite `comparison_completed` con resultados

### 🆕 Nuevos patterns que agregamos:

1. **Wait-for flexible**: Múltiples selectores OR para detectar página cargada
2. **Estados de negocio**: Distinguir "sin disponibilidad" de "error técnico"
3. **Configuración por sitio**: Centralizar selectores y keywords en configs
4. **Detección por keywords**: Buscar patterns en HTML para detectar estados

---

## Verificación End-to-End

### 1. Testing Manual

```bash
# Ejecutar app
python Hoteles/UI/interfaz.py

# Steps:
1. Seleccionar hotel Alvear
2. Seleccionar habitación
3. Ingresar fechas SIN disponibilidad (ej: fechas muy lejanas)
4. Click "Ejecutar Comparación"

# Resultado esperado:
- NO debe fallar con timeout
- Tabla debe mostrar "⚠️ NO DISPONIBLE" para ese periodo
- Status global: "⚠️ ALGUNOS PERIODOS SIN DISPONIBILIDAD"
```

### 2. Testing con `/multiperiodo-test` skill

```bash
# En CLI de Claude Code
/multiperiodo-test

# Usar fechas fake sin disponibilidad
# Verificar que estado = "SIN_DISPONIBILIDAD"
```

### 3. Testing de selectores flexibles

```python
# En debug_html_errors/, abrir HTML guardado
# Verificar que contiene:
# - .product-availability-container_unavailableMessage (sin disponibilidad)
# - O .thumb-cards_products (con disponibilidad)

# Confirmar que wait_for detecta ambos casos
```

### 4. Testing multi-periodo mixto

```bash
# Periodo 1: Con disponibilidad → estado "OK" o "DIFF"
# Periodo 2: Sin disponibilidad → estado "SIN_DISPONIBILIDAD"
# Periodo 3: Error técnico → estado "ERROR"

# Verificar que cada estado se renderiza correctamente
```

---

## Consideraciones

### Performance
- El wait-for flexible NO agrega latencia (solo cambia la condición de espera)
- La detección de keywords en HTML es O(n) pero el HTML ya está en memoria

### Backwards Compatibility
- El campo `sin_disponibilidad=False` por defecto → código existente sigue funcionando
- El campo `estado` tiene default `"OK"` → no rompe código legacy
- Los cambios son aditivos, no destructivos

### Escalabilidad
- **Fase 1-4**: Funcionan para Alvear inmediatamente
- **Fase 5**: Permite agregar Marriott/Hilton en el futuro sin tocar código core

### Edge Cases
- ¿Qué pasa si el HTML no tiene ninguno de los selectores? → Fallback a bodyLength > 10000
- ¿Qué pasa si la habitación existe en periodo 1 pero no en periodo 2? → Estado "SIN_DISPONIBILIDAD" solo para periodo 2
- ¿Qué pasa si hay timeout real (red caída)? → Estado "ERROR" (exception genérica)

---

## Priorización de Fases

**Mínimo viable** (soluciona el error inmediato):
- ✅ Fase 1: Wait-for flexible

**Recomendado** (experiencia de usuario completa):
- ✅ Fase 1-4: Wait-for + estados diferenciados + UI clara

**Opcional** (preparación multi-hotel):
- ⚪ Fase 5: Configuración por sitio

---

## Próximos Pasos

Una vez aprobado el plan:

1. **Implementar Fase 1** (5 min) → Testing → Confirmar que no hay más timeouts
2. **Implementar Fases 2-3** (15 min) → Testing → Confirmar estados correctos
3. **Implementar Fase 4** (10 min) → Testing E2E → Confirmar UI clara
4. **(Opcional) Fase 5** cuando se agregue un segundo hotel

**Tiempo total estimado**: 30-40 minutos
