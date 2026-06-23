---
name: handoff
description: Use when the user ends a session, says "hacé el handoff", "dejá el resumen", "cerrá la sesión", or when there's work in progress and the conversation context will be lost.
---

# handoff

Genera un archivo de handoff que resume la sesión actual, para que la próxima conversación arranque con contexto completo. El archivo se guarda en `docs/handoffs/` dentro del proyecto actual.

## Cuándo usar

- Al final de una sesión de trabajo
- Cuando el usuario dice "hacé el handoff", "dejá el resumen", "cerrá la sesión"
- Cuando se va a cortar el contexto y hay trabajo en curso

## Uso

```
/handoff
/handoff "foco en fixes del dropdown"
/handoff "migración CTk fase 5"
```

El argumento opcional guía el foco del resumen. Sin argumento, Claude infiere el tema principal de la sesión.

## Comportamiento: crear vs. actualizar

**Por defecto, cada pedido genera un handoff NUEVO.** No hay que verificar si ya existe uno previo: simplemente se crea otro archivo con nombre basado en el tema de la sesión.

**Única excepción — sesión retomada:** si en la sesión actual el usuario abrió, mencionó o pegó un handoff existente (es decir, esta sesión es continuación de un handoff previo), entonces al pedir un nuevo handoff la información se **agrega a ese archivo previo** en vez de crear uno nuevo. La señal de "sesión retomada" es que ese handoff aparece en la conversación actual como punto de partida.

## Procedimiento

### 1. Decidir si crear o actualizar

- ¿En esta sesión se retomó desde un handoff previo (el usuario lo abrió/mencionó/pegó al inicio)?
  - **Sí** → actualizar ESE archivo: leerlo y agregar el progreso nuevo, manteniendo el historial.
  - **No** → crear un archivo NUEVO (caso por defecto).

### 2. Determinar el nombre del archivo

El nombre incluye un título-resumen del tema, de **máximo 3 palabras**, en kebab-case:

```
docs/handoffs/HANDOFF-<tema-kebab-case>.md
```

Ejemplos: `docs/handoffs/HANDOFF-dropdown-fixes.md`, `docs/handoffs/HANDOFF-migracion-ctk.md`, `docs/handoffs/HANDOFF-endpoint-cuotas.md`

El tema sale del argumento pasado o, si no hay, se infiere de la conversación. Si se está actualizando un handoff retomado, se conserva el nombre original.

### 3. Sintetizar desde la conversación

La fuente principal del handoff es **lo que se habló en la sesión actual**, no el git log ni el diff. Reconstruir desde la conversación:

- ¿Qué problema se estaba atacando?
- ¿Qué enfoques se probaron?
- ¿Cuáles funcionaron y cuáles no?
- ¿En qué estado quedó el trabajo?

### 4. Obtener lista de archivos tocados (referencia auxiliar)

Si el proyecto es un repo git, ejecutar para completar la tabla de archivos:

```bash
git status
```

Si NO es un repo git (o el comando falla), omitir este paso y armar la tabla de archivos desde lo que se tocó según la conversación.

### 5. Generar o actualizar el handoff

Asegurar que exista la carpeta `docs/handoffs/` en la raíz del proyecto actual y escribir ahí el archivo con esta estructura:

```markdown
# Handoff — <Título Resumen> — YYYY-MM-DD

> Sesión: <descripción breve de la sesión>
> Tema: <área del proyecto afectada — ej: UI/Qt, scraper, deploy, config, historial>

## Objetivo
[Qué se estaba intentando lograr en esta sesión — 1 párrafo claro]

## Progreso actual
[Qué se completó, en qué estado quedó el trabajo — puede ser bullets o párrafo]

## Lo que funcionó
- `path/archivo.ext:línea` — descripción de qué enfoque funcionó y por qué
- ...

## Lo que no funcionó
- Descripción del enfoque fallido — por qué no funcionó, para no repetirlo
- ...

## Próximos pasos
1. Acción concreta para continuar
2. ...

## Archivos clave tocados

| Archivo | Cambio |
|---------|--------|
| `path/archivo.ext` | Descripción breve |
| ... | ... |
```

> Si no hubo enfoques fallidos, omitir la sección "Lo que no funcionó".

**Si se está actualizando un handoff retomado:** no sobrescribir el contenido previo. Agregar una nueva sección de continuación al final, con su propio subtítulo de fecha, para preservar el historial de la conversación previa.

### 6. Confirmar en el chat

Después de escribir el archivo, informar:
- Ruta del archivo creado/actualizado
- Tema del resumen
- Si se creó nuevo o se actualizó un handoff retomado

## Reglas

- **No actualizar memoria** como parte de este skill
- **Por defecto, crear un handoff nuevo por cada pedido** — NO verificar si existe uno previo como paso default
- **Excepción única:** si la sesión se retomó de un handoff previo, agregar la info a ese archivo en vez de crear uno nuevo
- **La fuente principal es la conversación**, no el git log ni el diff
- **El destino es dinámico:** la carpeta `docs/handoffs/` en la raíz del proyecto actual (working directory de la sesión), nunca una ruta hardcodeada
- **Ser específico con los paths**: incluir número de línea cuando sea relevante (`src/componente.tsx:142`)
- **El nombre del archivo incluye un título-resumen de máximo 3 palabras** en kebab-case
- **Todo en español**
- **El argumento es solo una guía de foco**, no limita lo que se documenta
- La fecha en el header es la fecha actual real (leer del contexto del sistema)
- El campo `Tema:` describe el área del proyecto afectada, no el nombre del archivo ni el argumento literal
