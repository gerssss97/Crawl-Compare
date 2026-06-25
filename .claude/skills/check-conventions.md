# /check-conventions

Skill para validar que el código siga las convenciones del proyecto.

## Descripción

Analiza archivos Python y verifica el cumplimiento de las convenciones establecidas en [docs/desarrollo/convenciones.md](../../docs/desarrollo/convenciones.md):

1. ✅ Nombres en español (archivos, variables, funciones)
2. ✅ BaseComponent pattern (herencia + métodos requeridos)
3. ✅ Controlador pattern (constructor con estado_app y event_bus)
4. ✅ Docstrings presentes

## Uso

```bash
/check-conventions [path]
```

## Parámetros

- **path** (opcional): Directorio o archivo a analizar. Default: `UI_qt/`

## Output

Reporte con:
- Lista de archivos procesados con status ✅/⚠️/❌
- Detalles de violaciones encontradas
- Sugerencias de corrección
- Tabla resumen al final

## Ejemplo

```bash
/check-conventions UI_qt/widgets/
```

Output esperado:
```
🔍 Validando Convenciones del Proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Escaneando: UI_qt/widgets/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ qt_labeled_combo.py
   ✓ Docstrings presentes

⚠️  qt_precio_panel.py
   ⚠️  Falta docstring en método: set_value()

❌ bad_example.py
   ❌ Nombre contiene inglés: "bad_example"
      → Sugerencia: renombrar a "mal_ejemplo.py"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Resumen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Archivos analizados:  3
✅ Sin problemas:     1 (33%)
⚠️  Con warnings:     1 (33%)
❌ Con errores:       1 (33%)

💡 Tip: Consulta docs/desarrollo/convenciones.md para detalles de cada convención
```

## Validaciones Específicas

### 1. Nombres en Español

Detecta palabras en inglés comunes:
- ❌ `user_manager.py` → ✅ `gestor_usuarios.py`
- ❌ `hotel_controller.py` → ✅ `controlador_hotel.py`
- ❌ `data_extractor.py` → ✅ `extractor_datos.py`

Excepciones permitidas: `test`, `config`, `utils`, `base`

### 2. BaseComponent Pattern

Para clases que heredan de `BaseComponent`, verifica:
- ✅ Método `_setup_ui(self)` presente
- ✅ Método `get_value(self)` presente
- ✅ Método `set_value(self, value)` presente
- ✅ Método `reset(self)` presente (opcional pero recomendado)

### 3. Controlador Pattern

Para clases con "Controlador" en el nombre, verifica:
- ✅ Constructor `__init__(self, estado_app, event_bus)` presente
- ✅ Almacena `self.estado_app` y `self.event_bus`
- ✅ Se suscribe a eventos con `event_bus.on()`

### 4. Docstrings

Verifica presencia de docstrings en:
- Módulos (archivo completo)
- Clases
- Métodos públicos (no privados con `_`)

## Uso desde Claude Code

Cuando el usuario te pida:
- "verifica las convenciones del código"
- "checkea si sigo los patrones correctos"
- "valida este componente nuevo"
- "hay algo mal con mi código?"

Ejecuta este skill con el path relevante (default `UI_qt/`, o el path específico que corresponda).

## Implementación

Ver [scripts/check_conventions.py](scripts/check_conventions.py)
