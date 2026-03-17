# test-scraper

Testing rápido del scraper con tiempos de ejecución y preparado para multi-sitio.

## Uso

```bash
python .claude/skills/scripts/test_scraper.py [hotel] [fecha_entrada] [fecha_salida] [adultos] [ninos]
```

**Parámetros** (todos opcionales):
- `hotel`: Nombre del hotel (default: "alvear")
- `fecha_entrada`: DD-MM-YYYY (default: mañana)
- `fecha_salida`: DD-MM-YYYY (default: pasado mañana)
- `adultos`: int (default: 2)
- `ninos`: int (default: 0)

**Ejemplos**:
```bash
# Test con defaults (mañana → pasado mañana, 2 adultos)
python .claude/skills/scripts/test_scraper.py

# Test con fechas específicas
python .claude/skills/scripts/test_scraper.py alvear 01-02-2026 05-02-2026 2 1

# Test multi-sitio (futuro)
python .claude/skills/scripts/test_scraper.py marriott
```

## Comportamiento

1. Parsea argumentos con defaults inteligentes
2. Convierte fechas DD-MM-YYYY → YYYY-MM-DD (formato para scraper)
3. Muestra configuración del test
4. Ejecuta scraping con timer
5. Muestra:
   - Tiempo de ejecución (segundos con 2 decimales)
   - Número de habitaciones extraídas
   - Primeras 3 habitaciones (nombre + precio más barato)
   - Errores si los hay
6. Guarda resultado temporal en `c:\Users\German\Gerssss\IA\Nueva carpeta\tmp\test-scraper-{timestamp}.json`

## Output esperado

```
🔍 Test Scraper - Hotel: alvear
📅 Fechas: 01-02-2026 → 05-02-2026
👥 Huéspedes: 2 adultos, 0 niños

⏱️  Ejecutando scraping...
✅ Completado en 4.23s

📊 Resultados:
   - 12 habitaciones extraídas

   1. Superior King Room
      💵 Precio más barato: $150.00 USD

   2. Deluxe Double Room
      💵 Precio más barato: $180.00 USD

   3. Suite
      💵 Precio más barato: $350.00 USD

💾 Resultado guardado en: c:\Users\German\Gerssss\IA\Nueva carpeta\tmp\test-scraper-20260131-120530.json

---
🌐 Multi-sitio: Para testear otros hoteles, agregar configuración en ScrawlingChinese/config.py
```

## Notas de Implementación

- **Timer**: `time.time()` antes y después del scraping
- **Parseo de fechas**: `datetime.strptime("%d-%m-%Y")` → `date.strftime("%Y-%m-%d")`
- **Defaults inteligentes**: `fecha_entrada = date.today() + timedelta(days=1)`
- **Guardado JSON**: `json.dump(resultado.model_dump(), f, ensure_ascii=False)`
- **Preparado multi-sitio**: Dict `CRAWLERS = {"alvear": crawl_alvear}` para futura expansión

## Dependencias

- `sys` - Argumentos de línea de comandos
- `asyncio` - Ejecutar crawler asíncrono
- `time` - Timer
- `datetime` - Parsing de fechas
- `json` - Guardado de resultados
- `pathlib` - Crear directorio tmp/

## Errores Comunes

### Error: "GROQ_API_KEY not found"
**Solución**: Verificar que `.env` existe en `Hoteles/` con `GROQ_API_KEY=gsk_...`

### Error: "Invalid date format"
**Solución**: Usar formato DD-MM-YYYY (ej: 01-02-2026, no 1-2-2026 ni 2026-02-01)

### Error: "No se extrajo ninguna habitación"
**Solución**: Ver [docs/scraper/troubleshooting.md](../../docs/scraper/troubleshooting.md)

---

Ver también:
- [docs/scraper/como-funciona.md](../../docs/scraper/como-funciona.md) - Cómo funciona el scraper
- [docs/scraper/troubleshooting.md](../../docs/scraper/troubleshooting.md) - Troubleshooting completo