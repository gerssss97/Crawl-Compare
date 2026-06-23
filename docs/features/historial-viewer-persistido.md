# Historial: viewer de resultados persistido

## Qué hace

Agrega un botón "Ver resultado" en cada fila del historial que abre una vista
con el HTML exacto que se mostró en la comparación original. Si hubo discrepancias,
aparece además un botón "Enviar mail".

Los resultados se persisten por TTL configurable (default: 7 días). Un safety cap
interno de 100 entradas evita crecimiento indefinido pero no se expone en la UI.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `Core/services/config_service.py` | +2 métodos: `get/set_historial_ttl_dias` |
| `UI/services/historial_service.py` | Purga por TTL + MAX=100 hardcoded |
| `UI_qt/widgets/qt_vista_resultados.py` | `mostrar_resultado_multiperiodo` retorna el HTML |
| `UI_qt/views/qt_resultados_modal.py` | Captura HTML, guarda `html_resultado` + `tiene_discrepancias` + `habitacion_web` |
| `UI_qt/views/qt_historial_modal.py` | Botón "Ver resultado" + `_ResultadoViewerDialog` |
| `UI_qt/views/qt_config_modal.py` | Tab "Historial" con campo TTL días |
| `UI_qt/interfaz_qt.py` | Callbacks `on_ver` y `on_email` para el historial |

## Estructura de la entrada del historial (extendida)

```json
{
  "timestamp": "2026-06-22T10:30:00",
  "hotel": "...",
  "edificio": "...",
  "habitacion": "...",
  "fecha_entrada": "DD-MM-YYYY",
  "fecha_salida": "DD-MM-YYYY",
  "adultos": 2,
  "ninos": 0,
  "periodos": [
    {"nombre": "...", "precio_excel": 150.0, "precio_web": 180.0, "coincide": false}
  ],
  "html_resultado": "<style>...</style><div>...</div>",
  "tiene_discrepancias": true,
  "habitacion_web": "Habitacion Estandar Doble"
}
```

## UX

- Click en el área de la fila → restaura formulario y cierra el historial (comportamiento existente)
- Click en "Ver resultado" → abre `_ResultadoViewerDialog` SIN cerrar el historial
- `_ResultadoViewerDialog` muestra el HTML con `QTextBrowser` (links clicables)
  - Si `tiene_discrepancias`: botón "Enviar mail" → abre cliente de email
  - Botón "Cerrar"
- Tab "Historial" en configuración: campo TTL días (default 7, rango 1-365)
- Entradas con TTL vencido se purgan en lectura y escritura
