# /commit-custom

Skill para generar commits con formato conventional en español.

## Descripción

Crea commits siguiendo el formato conventional del proyecto, en español, con preview interactivo.

## Uso

### Modo Interactivo (Recomendado)

```bash
/commit-custom
```

Sin parámetros, abre modo interactivo con prompts paso a paso.

### Modo Directo

```bash
/commit-custom feat comparacion "Mejorar fuzzy matching"
/commit-custom fix scraper "Corregir timeout en crawl_alvear"
/commit-custom docs readme "Actualizar guía de setup"
```

## Parámetros

- **tipo** (opcional): `feat`, `fix`, `style`, `refactor`, `test`, `docs`, `chore`
- **scope** (opcional): Área del proyecto (ej: `comparacion`, `scraper`, `ui`)
- **mensaje** (opcional): Mensaje corto del commit (<70 caracteres)

## Flujo Interactivo

```bash
$ python .claude/skills/scripts/commit_custom.py

╔════════════════════════════════════════════════════════════════╗
║                     Crear Commit Custom                        ║
╚════════════════════════════════════════════════════════════════╝

📊 Git Status:
M Core/comparador_multiperiodo.py
M Core/controller.py
A docs/negocio/multiperiodo.md

📝 Git Diff (staged):
@@ -45,7 +45,10 @@ def comparar_multiperiodo(...):
-    # TODO: Implementar
+    for periodo in periodos_aplicables:
+        hotel_web = await dar_hotel_web(force_fresh=True)
+        # ... lógica ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tipo de commit:
  1. feat      - Nueva funcionalidad
  2. fix       - Corrección de bug
  3. style     - Cambios de formato (sin afectar lógica)
  4. refactor  - Refactorización de código
  5. test      - Agregar o modificar tests
  6. docs      - Cambios en documentación
  7. chore     - Tareas de mantenimiento

Seleccione tipo [1-7]: 1

Scope (área del proyecto, Enter para omitir): comparacion

Mensaje corto (<70 caracteres): Implementar sistema multi-período completo

Descripción extendida (opcional, Enter x2 para terminar):
> Se agrega comparación de precios multi-período con scraping secuencial
> y fuzzy matching optimizado (solo en primer periodo).
>
>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Preview del Commit:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
feat(comparacion): Implementar sistema multi-período completo

Se agrega comparación de precios multi-período con scraping secuencial
y fuzzy matching optimizado (solo en primer periodo).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¿Crear este commit? [y/n]: y

✅ Commit creado exitosamente
   Hash: a1b2c3d

🎉 Listo!
```

## Formato de Commit

```
<tipo>(<scope>): <mensaje corto>

<descripción extendida multilínea>

```

### Tipos Disponibles

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(ui): Agregar modal de configuración` |
| `fix` | Corrección de bug | `fix(scraper): Corregir timeout en navegación` |
| `style` | Formato (sin lógica) | `style(comparador): Formatear con black` |
| `refactor` | Refactorización | `refactor(extractor): Simplificar parsing de fechas` |
| `test` | Tests | `test(multiperiodo): Agregar test de inferencia` |
| `docs` | Documentación | `docs(readme): Actualizar guía de setup` |
| `chore` | Mantenimiento | `chore: Actualizar dependencias` |

### Scopes Comunes

- `comparacion` - Core/comparador.py, fuzzy matching
- `scraper` - ScrawlingChinese/
- `ui` - UI/, componentes, vistas
- `extractor` - ExtractorDatos/
- `models` - Models/
- `email` - Sistema de email
- `periodos` - Lógica de periodos
- `multiperiodo` - Sistema multi-período

## Ejemplos

### Ejemplo 1: Feature Nueva

```bash
# Modo directo
/commit-custom feat ui "Agregar modal de preview de email"

# Resultado:
feat(ui): Agregar modal de preview de email

```

### Ejemplo 2: Bug Fix con Descripción

```bash
# Modo interactivo
/commit-custom

Tipo: 2 (fix)
Scope: scraper
Mensaje: Corregir timeout en crawl_alvear
Descripción:
> Se aumenta timeout de 60s a 90s para sitios lentos.
> Se agrega retry automático con backoff exponencial.
>
>

# Resultado:
fix(scraper): Corregir timeout en crawl_alvear

Se aumenta timeout de 60s a 90s para sitios lentos.
Se agrega retry automático con backoff exponencial.

```

### Ejemplo 3: Documentación

```bash
/commit-custom docs readme "Agregar sección de troubleshooting"

# Resultado:
docs(readme): Agregar sección de troubleshooting

```

## Características

- ✅ Preview del commit antes de crear
- ✅ Validación de longitud de mensaje (<70 caracteres)
- ✅ Co-Authored-By automático
- ✅ Muestra git status y diff staged
- ✅ Formato conventional en español
- ✅ Descripción multilínea opcional
- ✅ Confirmación antes de crear

## Uso desde Claude Code

Cuando el usuario te pida:
- "crear un commit"
- "commitear estos cambios"
- "hacer commit de esto"
- "generar commit message"

Ejecuta este skill para crear el commit con formato correcto.

## Implementación

Ver [scripts/commit_custom.py](scripts/commit_custom.py)