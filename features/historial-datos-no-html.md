# Historial: guardar datos, no HTML

## Problema

El historial guardaba `html_resultado` — el HTML ya renderizado con colores bakeados.
Cualquier cambio de estilos en la UI no se propagaba a entradas previas.
`_ResultadoViewerDialog` cargaba ese HTML con un `QTextBrowser` crudo, sin awareness del tema.

## Solución

El historial guarda **solo datos estructurados**. El render lo hace la UI siempre desde cero,
usando `QtVistaResultados` con el tema activo en ese momento.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `UI_qt/views/qt_resultados_modal.py` | Expandir `_guardar_historial()`, eliminar `html_resultado` |
| `UI_qt/widgets/qt_vista_resultados.py` | Agregar `mostrar_resultado_desde_dict(data)` |
| `UI_qt/views/qt_historial_modal.py` | `_ResultadoViewerDialog` usa `QtVistaResultados` + theme |
| `UI_qt/interfaz_qt.py` | Pasar tema actual al abrir historial modal |

## Schema nuevo del historial

```json
{
  "timestamp": "2026-06-23T18:19:00",
  "hotel": "...",
  "edificio": "...",
  "habitacion": "...",
  "fecha_entrada": "...",
  "fecha_salida": "...",
  "adultos": 1,
  "ninos": 0,
  "tiene_discrepancias": true,
  "habitacion_web": "Suite Diplomatic Prestige",
  "habitacion_web_detalles": "1 King bed...",
  "mensaje_match": "Se buscó un combo con 'breakfast'...",
  "periodos": [
    {
      "nombre": "23/06-30/09",
      "fecha_inicio": "2026-06-23",
      "fecha_fin": "2026-09-30",
      "precio_excel": 1475.0,
      "precio_web": 2450.0,
      "coincide": false,
      "diferencia": 975.0,
      "fecha_inicio_real": "2026-06-23",
      "fecha_fin_real": "2026-09-30",
      "url_visitada": "https://...",
      "error_msg": null,
      "error_url": null
    }
  ]
}
```

## Backward compatibility

Entradas viejas (tienen `html_resultado` pero no `fecha_inicio` por periodo)
caen a un fallback: se muestra el HTML guardado con `QTextBrowser`.
No se pierden datos anteriores.

## Pasos de implementación

1. `qt_resultados_modal.py` — expandir `_guardar_historial()`
2. `qt_vista_resultados.py` — agregar `mostrar_resultado_desde_dict()`
3. `qt_historial_modal.py` — refactorizar `_ResultadoViewerDialog` + pasar `theme`
4. `interfaz_qt.py` — pasar tema al abrir historial
