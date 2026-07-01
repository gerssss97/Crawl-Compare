# Bug: gestor_datos.py siempre llama crawl_alvear

**Estado:** ✅ Resuelto  
**Descubierto:** 2026-06-30 durante implementación de taxes-y-desacople-precio-web

---

## Síntoma

Al comparar **Faena**, el scraping va contra la URL del Alvear en lugar de la del Faena.

## Causa Raíz

`GestorService.obtener_hotel_web()` en [gestor_datos.py:101](../../Hoteles/Core/gestor_datos.py#L101) hardcodea `crawl_alvear`:

```python
self.__hotel_web = await crawl_alvear(fecha_ingreso_iso, fecha_egreso_iso, ...)
```

El `comparar_multiperiodo` llama `dar_hotel_web` → `GestorService.get().obtener_hotel_web()` → esa línea. No importa qué hotel esté seleccionado: siempre raspa Alvear.

## Dónde debería estar el dispatch

`crawler.py` ya tiene el mecanismo correcto:

```python
CRAWLERS = {
    "alvear": crawl_alvear,
    "faena":  crawl_faena,
}

def get_crawler(hotel_nombre: str):
    return CRAWLERS[hotel_nombre]
```

## Fix propuesto

`GestorService` necesita saber qué hotel está cargado. Dos opciones:

**Opción A (más simple):** Pasar `hotel_nombre` como parámetro a `obtener_hotel_web` y despachar dinámicamente:

```python
# gestor_datos.py
async def obtener_hotel_web(self, hotel_nombre: str, fecha_ingreso, ...):
    crawl_fn = get_crawler(hotel_nombre)
    self.__hotel_web = await crawl_fn(fecha_ingreso_iso, fecha_egreso_iso, ...)
```

Y propagarlo desde `dar_hotel_web` en `controller.py`, que a su vez lo recibe de `comparar_multiperiodo`.

**Opción B:** `GestorService` guarda el hotel seleccionado al cargar el Excel y lo usa internamente.

## Impacto actual

- Comparación de **Alvear**: funciona (coincide por accidente)
- Comparación de **Faena**: scraping devuelve habitaciones del Alvear → comparación incorrecta
- El bug existía antes de esta sesión; la feature de taxes/desacople asumió que el dispatch ya era correcto

## Relacionado

- [docs/features/taxes-y-desacople-precio-web.md](../../docs/features/taxes-y-desacople-precio-web.md) — feature implementada que depende de que este fix esté hecho para funcionar correctamente en Faena
- `crawler.py:76` — `get_crawler()` ya disponible para el dispatch dinámico
