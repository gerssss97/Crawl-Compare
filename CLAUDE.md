# CLAUDE.md

Guía principal de Claude Code para el proyecto **Crawl-Compare** (Comparador de Precios de Hoteles)

---

## Reglas para Claude Code

### Estilo de Comunicación

**Tono casual**: Usar tono argentino informal ("che", "mirá", "fijate"). La frase "uy che" no es válida.

**Explicar el "por qué" y el "cómo"**:
- Siempre explicar las **razones** detrás de las decisiones, no solo cómo hacerlas
- Mencionar **todos los archivos relacionados** con el cambio
- Explicar las **implicaciones** y **trade-offs**

```
❌ "Voy a agregar un nuevo método set_value() al componente"

✅ "Voy a agregar set_value() al componente porque:
   - Sigue el BaseComponent pattern (base_component.py:15-20)
   - Permite que el controlador actualice el componente desde eventos
   - Se relaciona con precio_panel.py y periodos_panel.py que ya lo usan"
```

### Motivar al Usuario a Codear

**"necesito que hagas..."** → implementar directamente, pedir permiso como siempre.

**"necesito que hagamos..." / "necesito hacer..."** → NO implementar. Motivarlo con:
- Ideas y sugerencias de cómo abordarlo
- Pistas sobre qué archivos modificar
- Ejemplos de código que pueda adaptar
- Contexto y archivos relacionados

### Otras Directrices

- **Antes de leer código**, consultá `docs/` según el módulo. Solo si aún necesitás más detalle, leé el archivo.
- **Antes de buscar un archivo**, consultá [docs/arquitectura/tree-directory.md](docs/arquitectura/tree-directory.md). Actualizarlo si se agregan/mueven archivos.
- Para código legacy, preferir migrar a la arquitectura event-driven.
- Siempre considerar el BaseComponent pattern y el EventBus.
- Si consultás un doc o usás un skill, **informarlo en el chat**.
- **Para listas de opciones UI**: usar SIEMPRE `CTkCustomDropdown` (o `CTkLabeledComboBox`). NUNCA `ctk.CTkOptionMenu` ni `ctk.CTkComboBox`. Ver [docs/desarrollo/convenciones.md — Componentes UI](docs/desarrollo/convenciones.md#componentes-ui--reglas-de-uso).
- **Ante cualquier problema visual de CTk** (scroll raro, sizing incorrecto, esquinas borrosas, overflow): consultar primero [docs/ui/troubleshooting-ctk.md](docs/ui/troubleshooting-ctk.md).

---

## Proyecto

**Qué hace**: Compara precios de habitaciones entre datos Excel (`Hoteles/Data/Extracto.xls`) y scraping en vivo (Crawl4AI + DeepSeek-R1). Detecta discrepancias y notifica por email.

**Arquitectura**: Event-Driven MVC — `UI → EventBus → Controllers → Core → EventBus → UI`

**Flujo**: selección hotel/habitación → ControladorPrecios calcula precio → "Ejecutar Comparación" → scraping por periodo → fuzzy matching → VistaResultados

**Interfaz activa**: `interfaz_ctk.py` (CustomTkinter). Legacy: `interfaz.py` (Tkinter). Toggle en `main.py`.

**Variables de entorno** (en `Hoteles/.env`):
```
GROQ_API_KEY=gsk_...           # Obligatorio para scraping
GMTP_KEY=...                   # Opcional para emails
SCRAPING_DELAY_SECONDS=2
```

---

## Documentación

> Consultá esto antes de leer código fuente.

| Tema | Doc |
|------|-----|
| Tree directory completo | [docs/arquitectura/tree-directory.md](docs/arquitectura/tree-directory.md) |
| Arquitectura y flujos | [docs/arquitectura/](docs/arquitectura/) |
| EventBus y estado | [docs/arquitectura/event-driven-mvc.md](docs/arquitectura/event-driven-mvc.md) |
| Modelos de datos | [docs/arquitectura/modelo-datos.md](docs/arquitectura/modelo-datos.md) |
| Convenciones de código | [docs/desarrollo/convenciones.md](docs/desarrollo/convenciones.md) |
| Setup y dependencias | [docs/desarrollo/setup.md](docs/desarrollo/setup.md) |
| Debugging | [docs/desarrollo/debugging.md](docs/desarrollo/debugging.md) |
| Testing | [docs/desarrollo/testing.md](docs/desarrollo/testing.md) |
| Scraper (Crawl4AI) | [docs/scraper/](docs/scraper/) |
| Troubleshooting scraper | [docs/scraper/troubleshooting.md](docs/scraper/troubleshooting.md) |
| Componentes UI | [docs/ui/componentes.md](docs/ui/componentes.md) |
| Troubleshooting CTk (UI) | [docs/ui/troubleshooting-ctk.md](docs/ui/troubleshooting-ctk.md) |
| Controladores UI | [docs/ui/controladores.md](docs/ui/controladores.md) |
| Multi-periodo | [docs/negocio/multiperiodo.md](docs/negocio/multiperiodo.md) |
| Email | [docs/negocio/email.md](docs/negocio/email.md) |
| Skills custom | [.claude/skills/](.claude/skills/) |
| Índice completo docs | [docs/README.md](docs/README.md) |
