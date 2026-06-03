# Feature: Template de email editable con bloque for-periodo

## Estado: IMPLEMENTADO ✅

---

## Contexto

El body del email se generaba 100% hardcodeado en `controller.py`. Ahora el usuario puede escribir su propio template con variables interpoladas `{variable}` y un bloque repetible `{% for periodo %}...{% end %}` que itera sobre todos los periodos del resultado. La tab "Email" del modal de config fue implementada.

---

## Sintaxis del template

```
Estimado equipo de reservas,

Hotel: {hotel}
Habitación Excel: {habitacion_excel}
Habitación Web:   {habitacion_web}

{% for periodo %}
- Periodo {periodo_id} ({fecha_inicio_periodo} al {fecha_fin_periodo})
  Fechas buscadas: {fecha_inicio_busqueda} al {fecha_fin_busqueda}
  Precio Excel: {precio_excel}
  Precio Web:   {precio_web}
  Diferencia:   {diferencia}
  Estado:       {estado}
{% end %}

Saludos,
{firma}
```

### Variables globales (fuera o dentro del bloque)
| Token | Valor |
|---|---|
| `{hotel}` | Nombre del hotel |
| `{habitacion_excel}` | Nombre habitación Excel |
| `{habitacion_web}` | Nombre habitación web matcheada |
| `{firma}` | Texto de firma configurable |

### Variables de periodo (SOLO dentro del bloque `{% for periodo %}...{% end %}`)
| Token | Fuente |
|---|---|
| `{periodo_id}` | `periodo.id` |
| `{fecha_inicio_periodo}` | `periodo.fecha_inicio` (DD/MM/AAAA) |
| `{fecha_fin_periodo}` | `periodo.fecha_fin` (DD/MM/AAAA) |
| `{fecha_inicio_busqueda}` | `res_periodo.fecha_inicio_real` (DD/MM/AAAA) |
| `{fecha_fin_busqueda}` | `res_periodo.fecha_fin_real` (DD/MM/AAAA) |
| `{precio_excel}` | `res_periodo.precio_excel` formateado |
| `{precio_web}` | `res_periodo.precio_web` formateado |
| `{diferencia}` | `res_periodo.diferencia` formateado |
| `{estado}` | "OK" / "DIFF" / "ERROR" |

---

## Reglas de validación al guardar (en config_modal.py)

1. **Error bloqueante**: variable de-periodo usada FUERA del bloque `{% for periodo %}...{% end %}`
2. **Error bloqueante**: bloque mal formado — `{% for periodo %}` sin `{% end %}`, o `{% end %}` sin `{% for periodo %}`, o tags anidados
3. **Error bloqueante**: variable desconocida `{xyz}` en cualquier parte del template
4. **Warning no bloqueante** (aviso informativo, no impide guardar): template sin bloque `{% for periodo %}` — válido, el usuario eligió no mostrar detalle de periodos

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `Hoteles/Core/services/config_service.py` | +4 métodos: `get/set_email_template`, `get/set_email_firma` |
| `Hoteles/Core/controller.py` | +`_renderizar_template()`, `generar_texto_email_multiperiodo` acepta `template` y `firma` |
| `Hoteles/UI/views/config_modal.py` | Tab "Email" implementada completa (firma, chips, editor, validación, guardar/restaurar) |
| `Hoteles/UI/views/modal_email.py` | (eliminado) `_generar_texto_default` consultaba `ConfigService` y pasaba `template`/`firma` al controller. Esa lógica vive ahora en `ResultadosModal._abrir_email()` ([resultados_modal.py](../../Hoteles/UI/views/resultados_modal.py)) |

### Detalles de implementación

**`config_service.py`** — `None` como sentinel: si no hay template guardado, `get_email_template()` retorna `None` y el controller cae al hardcodeado.

**`controller.py`** — `_renderizar_template` hace split por `{% for periodo %}` y `{% end %}`, itera `resultado.periodos`, y usa `re.sub` con callable para sustituir tokens. Fallback automático al hardcodeado si `template is None`.

**`config_modal.py`** — Chips en dos filas (Globales / Solo en for). Font monospace `Courier New 12` en el editor para que el template sea más legible. Validación en `_validar_template()` cubre los 3 errores bloqueantes.

**Consumo del template** — originalmente en `ModalEmail._generar_texto_default` (modal eliminado). Hoy lo consume `ResultadosModal._abrir_email()`: instancia `ConfigService()` y pasa `get_email_template()` / `get_email_firma()` a `generar_texto_email_multiperiodo(...)`, cuyo resultado va a `MailtoSender`.

---

## Verificación end-to-end

1. Sin template guardado → el cuerpo del email usa el texto hardcodeado de siempre (fallback intacto)
2. Guardar template con `{hotel}` y bloque `{% for periodo %}` con `{precio_web}` → `config.json` tiene `"email_template"`
3. Click "Enviar Email" → el `mailto:` lleva el texto interpolado con valores reales
4. Intentar guardar `{precio_web}` FUERA del bloque → error bloqueante, no se guarda
5. Intentar guardar `{prcio_web}` (typo) → error bloqueante "variable desconocida"
6. Intentar guardar `{% for periodo %}` sin `{% end %}` → error bloqueante "bloque mal formado"
7. Template sin bloque ni variables de-periodo → se guarda con aviso informativo
8. Click en chip "Precio Web" → `{precio_web}` se inserta en la posición del cursor
9. Restaurar predeterminado → `config.json` sin `"email_template"`, el cuerpo vuelve al hardcodeado
10. Firma "Equipo Soporte" + `{firma}` en template → email pre-relleno muestra "Equipo Soporte"
