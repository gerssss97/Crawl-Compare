# Documentación del Proyecto

Índice maestro de toda la documentación del comparador de precios de hoteles.

---

## 🚀 Inicio Rápido

**Primera vez con el proyecto?**

1. [Setup del Entorno](desarrollo/setup.md) - Configuración completa paso a paso
2. [Arquitectura Overview](arquitectura/overview.md) - Entender la estructura del proyecto
3. [Convenciones de Código](desarrollo/convenciones.md) - Patrones y reglas del proyecto

---

## 📖 Guía de Navegación

### "Quiero empezar a desarrollar"

1. [Setup](desarrollo/setup.md) - Instalar dependencias
2. [Testing](desarrollo/testing.md) - Ejecutar tests
3. [Convenciones](desarrollo/convenciones.md) - Patrones de código
4. [Debugging](desarrollo/debugging.md) - Técnicas de debugging

### "El scraper no funciona"

1. [Troubleshooting](scraper/troubleshooting.md) - Tabla de errores comunes ⭐
2. [Cómo Funciona](scraper/como-funciona.md) - Arquitectura del scraper
3. [Configuración](scraper/configuracion.md) - Ajustar parámetros

### "¿Cómo funciona el sistema multi-período?"

1. [Multi-Período](negocio/multiperiodo.md) - Sistema completo ⭐
2. [Periodos](negocio/periodos.md) - Extracción y asignación
3. [Comparación](negocio/comparacion.md) - Fuzzy matching

### "Quiero agregar un componente UI"

1. [Componentes](ui/componentes.md) - Todos los componentes base
2. [Convenciones](desarrollo/convenciones.md) - Pattern BaseComponent
3. [Event-Driven MVC](arquitectura/event-driven-mvc.md) - Flujo de eventos

### "Tengo un problema visual con CTk (scroll raro, esquinas borrosas, overflow)"

1. [Troubleshooting CTk](ui/troubleshooting-ctk.md) - Problemas conocidos de CTk ⭐

### "¿Cómo agrego otro hotel (ej: Marriott)?"

1. [Multi-Sitio](scraper/multi-sitio.md) - Guía completa paso a paso ⭐
2. [Configuración](scraper/configuracion.md) - Config por sitio
3. [Cómo Funciona](scraper/como-funciona.md) - Entender crawler

---

## 📂 Estructura de la Documentación

### Arquitectura

Diseño y patrones del sistema.

| Archivo | Descripción |
|---------|-------------|
| [overview.md](arquitectura/overview.md) | Diagrama de capas, responsabilidades |
| [event-driven-mvc.md](arquitectura/event-driven-mvc.md) | EventBus, AppState, flujo completo |
| [flujos-principales.md](arquitectura/flujos-principales.md) | 3 flujos con diagramas mermaid |
| [modelo-datos.md](arquitectura/modelo-datos.md) | Modelos Pydantic, relaciones |

### Desarrollo

Setup, testing, debugging, convenciones.

| Archivo | Descripción |
|---------|-------------|
| [setup.md](desarrollo/setup.md) | Instalación paso a paso ⭐ |
| [testing.md](desarrollo/testing.md) | Tests de Excel, UI, scraper, negocio |
| [debugging.md](desarrollo/debugging.md) | EventBus debug, prints, pdb |
| [convenciones.md](desarrollo/convenciones.md) | Nombres en español, patterns ⭐ |

### Scraper

Web scraping con LLM.

| Archivo | Descripción |
|---------|-------------|
| [como-funciona.md](scraper/como-funciona.md) | Crawl4AI + DeepSeek-R1, flujo completo |
| [configuracion.md](scraper/configuracion.md) | URLs, selectores, LLM strategy |
| [troubleshooting.md](scraper/troubleshooting.md) | Tabla de errores y soluciones ⭐ |
| [multi-sitio.md](scraper/multi-sitio.md) | Agregar Marriott, Hilton, etc. |

### Lógica de Negocio

Comparación, periodos, emails.

| Archivo | Descripción |
|---------|-------------|
| [comparacion.md](negocio/comparacion.md) | Fuzzy matching con RapidFuzz |
| [multiperiodo.md](negocio/multiperiodo.md) | Sistema multi-período completo ⭐ |
| [periodos.md](negocio/periodos.md) | Extracción, asignación, inferencia |
| [email.md](negocio/email.md) | Envío vía mailto (cliente del SO), generación de texto |

### UI

Interfaz gráfica CustomTkinter (activa) + Tkinter legacy.

| Archivo | Descripción |
|---------|-------------|
| [componentes.md](ui/componentes.md) | Componentes CTk (activos) + legacy (DateInputWidget, etc.) |
| [vistas.md](ui/vistas.md) | 3 vistas compuestas (Formularios, Resultados) |
| [controladores.md](ui/controladores.md) | 4 controladores (Hotel, Validación, etc.) |
| [pantallas.md](ui/pantallas.md) | Layout completo, flujos, estados |
| [modales.md](ui/modales.md) | Modal de email, MessageBox, futuros |
| [troubleshooting-ctk.md](ui/troubleshooting-ctk.md) | Problemas conocidos de CTk: scaling, scroll, rendering ⭐ |

### Features

Planes y documentación de features grandes que cruzan capas (Core + UI + Deploy).

| Archivo | Descripción |
|---------|-------------|
| [seleccion-excel-y-config.md](features/seleccion-excel-y-config.md) | Selección de Excel + validators desacoplados + modal de config ⭐ |
| [email-config-opciones.md](features/email-config-opciones.md) | Opciones evaluadas para configurar envío de email (decisión pendiente) 📋 |

---

## 🛠️ Skills Disponibles

### /test-scraper

Testing rápido del scraper con tiempos.

```bash
python .claude/skills/scripts/test_scraper.py alvear 15-02-2026 16-02-2026
```

**Documentación**: [.claude/skills/test-scraper.md](../.claude/skills/test-scraper.md)

### /multiperiodo-test

Testing multi-período con modo fake (UI para inventar datos).

```bash
python .claude/skills/scripts/multiperiodo_test.py --modo fake
```

**Documentación**: [.claude/skills/multiperiodo-test.md](../.claude/skills/multiperiodo-test.md)

### /compare-debug

Debug de fuzzy matching con scores detallados.

```bash
python .claude/skills/scripts/compare_debug.py "dbl superior w/breakfast" "Double Superior Room"
```

**Documentación**: [.claude/skills/compare-debug.md](../.claude/skills/compare-debug.md)

### /check-conventions

Valida convenciones del código (nombres en español, patterns).

```bash
python .claude/skills/scripts/check_conventions.py UI/components/
```

**Documentación**: [.claude/skills/check-conventions.md](../.claude/skills/check-conventions.md)

### /commit-custom

Genera commits con formato conventional en español.

```bash
python .claude/skills/scripts/commit_custom.py
```

**Documentación**: [.claude/skills/commit-custom.md](../.claude/skills/commit-custom.md)

---

## 🔍 Búsqueda Rápida

### Por Tema

**Web Scraping:**
- [Cómo Funciona](scraper/como-funciona.md)
- [Configuración](scraper/configuracion.md)
- [Troubleshooting](scraper/troubleshooting.md)

**Fuzzy Matching:**
- [Comparación](negocio/comparacion.md)
- [Multi-Período](negocio/multiperiodo.md)

**Periodos Estacionales:**
- [Periodos](negocio/periodos.md)
- [Multi-Período](negocio/multiperiodo.md)

**Eventos:**
- [Event-Driven MVC](arquitectura/event-driven-mvc.md)
- [Flujos Principales](arquitectura/flujos-principales.md)

**Componentes UI:**
- [Componentes](ui/componentes.md)
- [Vistas](ui/vistas.md)
- [Pantallas](ui/pantallas.md)

**Testing:**
- [Testing](desarrollo/testing.md)
- [Debugging](desarrollo/debugging.md)

**Email:**
- [Email](negocio/email.md)
- [Modales](ui/modales.md)

### Por Archivo del Código

| Archivo | Documentación Relevante |
|---------|-------------------------|
| `ScrawlingChinese/crawler.py` | [como-funciona.md](scraper/como-funciona.md), [configuracion.md](scraper/configuracion.md) |
| `Core/comparador.py` | [comparacion.md](negocio/comparacion.md) |
| `Core/comparador_multiperiodo.py` | [multiperiodo.md](negocio/multiperiodo.md) |
| `ExtractorDatos/extractor.py` | [periodos.md](negocio/periodos.md), [modelo-datos.md](arquitectura/modelo-datos.md) |
| `UI/state/event_bus.py` | [event-driven-mvc.md](arquitectura/event-driven-mvc.md) |
| `UI/components/*.py` | [componentes.md](ui/componentes.md) |
| `UI/views/*.py` | [vistas.md](ui/vistas.md) |
| `UI/controllers/*.py` | [controladores.md](ui/controladores.md) |
| `Models/*.py` | [modelo-datos.md](arquitectura/modelo-datos.md) |

---

## 📝 Diagramas

### Mermaid Diagrams en la Documentación

- [Diagrama de Capas](arquitectura/overview.md#diagrama-de-arquitectura)
- [Flujo de Eventos](arquitectura/event-driven-mvc.md#diagrama-de-flujo)
- [Flujo de Carga Excel](arquitectura/flujos-principales.md#flujo-1-carga-inicial)
- [Flujo de Selección](arquitectura/flujos-principales.md#flujo-2-selección-hotel)
- [Flujo Multi-Período](arquitectura/flujos-principales.md#flujo-3-comparación-multi-período)
- [Diagrama de Modelos](arquitectura/modelo-datos.md#diagrama-de-clases)
- [Flujo de Scraping](scraper/como-funciona.md#arquitectura-del-scraper)
- [Flujo de Matching](negocio/comparacion.md#flujo-de-comparación)

---

## 🎯 Tareas Comunes

### Agregar un Nuevo Componente UI

1. Leer [convenciones.md - Pattern BaseComponent](desarrollo/convenciones.md#pattern-basecomponent)
2. Crear archivo en `UI/components/mi_componente.py`
3. Heredar de `BaseComponent`
4. Implementar `_setup_ui()`, `get_value()`, `set_value()`
5. Exportar en `UI/components/__init__.py`
6. Testing standalone: `python .claude/skills/scripts/ui_preview.py MiComponente`
7. Validar convenciones: `python .claude/skills/scripts/check_conventions.py UI/components/mi_componente.py`

### Ajustar Pesos de Fuzzy Matching

1. Leer [comparacion.md - Score Ponderado](negocio/comparacion.md#score-ponderado)
2. Editar `Core/comparador.py:18-22`
3. Testing: `python .claude/skills/scripts/compare_debug.py "nombre excel" "nombre web"`
4. Validar cambios con comparación completa

### Agregar un Nuevo Hotel

1. Leer [multi-sitio.md - Checklist](scraper/multi-sitio.md#checklist-para-agregar-nuevo-sitio)
2. Crear `ScrawlingChinese/utils/site_configs/marriott.py`
3. Crear función `crawl_marriott()` en `crawler.py`
4. Registrar en `CRAWLERS` dict
5. Testing: `python .claude/skills/scripts/test_scraper.py marriott`

### Debugging de Comparación

1. Activar [EventBus debug](desarrollo/debugging.md#eventbus-debug-mode)
2. Ejecutar comparación
3. Ver logs detallados en consola
4. Usar [compare-debug skill](desarrollo/debugging.md#usar-skill-compare-debug)

### Email

El envío abre el cliente de email del SO vía `mailto:` (sin SMTP ni
credenciales). No requiere configuración. Solo el template y la firma son
editables desde el modal de configuración. Ver [email.md](negocio/email.md).

---

## 🐛 Problemas Frecuentes

### "No se pudo extraer datos desde Excel"

Ver: [periodos.md - Extracción](negocio/periodos.md#extracción-desde-excel)

### "Scraper no encuentra habitaciones"

Ver: [troubleshooting.md](scraper/troubleshooting.md) ⭐

### "Fuzzy matching da resultados incorrectos"

Ver: [comparacion.md - Debugging](negocio/comparacion.md#debugging-de-matching)

### "EventBus no dispara eventos"

Ver: [debugging.md - EventBus](desarrollo/debugging.md#problema-eventbus-no-dispara-eventos)

### "Email no se envía"

Ver: [email.md - Troubleshooting](negocio/email.md#troubleshooting)

### "Hay un problema visual raro en CTk (scroll, scaling, esquinas)"

Ver: [troubleshooting-ctk.md](ui/troubleshooting-ctk.md) ⭐

---

## 📚 Recursos Externos

### Librerías Principales

- [Crawl4AI Docs](https://docs.crawl4ai.com) - Web crawling framework
- [Pydantic Docs](https://docs.pydantic.dev) - Validación de datos
- [RapidFuzz Docs](https://maxbachmann.github.io/RapidFuzz/) - Fuzzy matching
- [Tkinter Docs](https://docs.python.org/3/library/tkinter.html) - GUI framework

### APIs

- [Groq API Docs](https://console.groq.com/docs) - LLM provider

---

## 🤝 Contribuir

### Antes de Hacer Commit

1. Ejecutar [checklist de testing](desarrollo/testing.md#checklist-de-testing-pre-commit)
2. Validar convenciones: `python .claude/skills/scripts/check_conventions.py .`
3. Usar skill de commits: `python .claude/skills/scripts/commit_custom.py`

### Estilo de Commits

Ver: [convenciones.md - Commits](desarrollo/convenciones.md#commits-conventional-en-español)

Formato:
```
<tipo>(<scope>): <mensaje corto>

<descripción opcional>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## 📞 Soporte

- **Issues**: Crear issue en GitHub
- **Docs incorrectas**: PR a este repo
- **Nuevas features**: Discutir en issues primero

---

Última actualización: 06 Marzo 2026