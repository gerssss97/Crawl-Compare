
# TODO — Hoteles (UI / Producto)

## Bug conocido — periodo con Error no muestra precio web

**Síntoma**: cuando un periodo falla al scrapear, la fila muestra `Error` en la columna Excel
y la columna Web queda vacía (sin precio ni estado).

```
Habitación Excel: sgl/dbl junior suite le mirador w/breakfast served at restaurant
Periodo         | Fechas        |        Excel |          Web | Estado
------------------------------------------------------------------------------------------
01/05-30/09     | 01/05-30/09   |     $1250.00 |     $1563.00 | ❌ DIFF
01/10-30/12     | 01/10-30/12   |        Error |
```

**Archivos a revisar**: `UI_qt/widgets/qt_vista_resultados.py` → `mostrar_resultado_multiperiodo`
y `Core/comparador_multiperiodo.py` → cómo se construye `ResultadoPeriodo` cuando hay error.

---

## Feature — advertencia visual de gaps en formulario (perdida en migración CTk→Qt)

`ControladorPrecios` emite `gaps_detected` cuando las fechas tienen cobertura parcial,
pero ningún widget Qt lo escucha actualmente. En CTk se mostraba un modal de advertencia
inmediato mientras el usuario completaba fechas.

**Fix**: suscribirse a `gaps_detected` en `MainWindow` via `EventBridge` y mostrar un banner
inline o label de advertencia bajo el formulario, sin bloquear el flujo.

**Archivos involucrados**: `UI_qt/interfaz_qt.py`, `UI_qt/state/event_bridge.py`

---

## Feature — ocultar periodos vencidos en config

Las fechas de rangos de periodos que ya finalizaron (antes de hoy) deberían poder
ocultarse mediante un checkbox en el modal de config, para no ensuciar la vista de
periodos disponibles.

**Archivo**: `UI_qt/views/qt_config_modal.py` + lógica de filtrado en `ControladorPrecios`
o en el panel `QtPeriodosPanel`.

---

## UI — título "Precio Estimado" no refleja el contenido

El título muestra "precio estimado" pero los precios que se muestran van en un rango
del menor al mayor según los periodos afectados. Cambiar el título o agregar aclaración
de rango (ej. "Rango de precio" o "Precio por periodo").

**Archivo**: `UI_qt/widgets/qt_precio_panel.py`

---

## UI — header (barra superior) con fondo muy oscuro en modo claro

El color de fondo de la barra superior (donde están el título, historial, etc.) está
demasiado oscuro en el tema light. Revisar la variable de color asignada al header en el
QSS de modo claro.

**Archivo**: `UI_qt/styles/qt_qss.py` (o donde se construye el QSS) — selector del header frame.

---

## pantalla negra de aplicacion buildeada persiste

La pantalla negra de la aplicacion cuando la ejecuta el usuario se mantiene visible luego de 
terminado el proceso de apertura de la app. Ademas, muestra todo el log completo de la app al
usuario, no recomendado.

--- 

## desactivar logs de resultados de hoteles obtenidos, solo persistir los errores de la aplicacion

---

## El estilo del dropdown al apretar el input no coincide con el dropdown al apretar la flecha del mismo

---

## Borrar las tabs de scraping y apikeys del modal de configuracion

---

## Tab general del modal de configuracion es poco legible

Esta pestaña tiene poco contenido, por lo cual deja muy vacio el modal. Modificar color de letra del msg de la ubicacion del archivo.
Borrar el msg de explicacion para cambiar la ubicacion del excel que se toma. Agregar dicho boton en este mismo modal, asi el usuario no tiene que salir hasta la interfaz principal.

---

## No tenemos icono de aplicacion!


---
## Historial no agrega boton para abril el modal de la comparacion, ver todos los datos y poder enviar el mail.