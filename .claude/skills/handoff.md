# /handoff

Genera o actualiza un archivo `HANDOFF.md` en la raíz del proyecto resumiendo la sesión actual, para que la próxima conversación arranque con contexto completo.

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

## Procedimiento

### 1. Verificar si ya existe HANDOFF.md

Antes de escribir nada, verificar si `HANDOFF.md` existe en la raíz del proyecto. Si existe, leerlo para entender el contexto previo e integrarlo en la actualización.

### 2. Sintetizar desde la conversación

La fuente principal del handoff es **lo que se habló en la sesión actual**, no el git log ni el diff. Reconstruir desde la conversación:

- ¿Qué problema se estaba atacando?
- ¿Qué enfoques se probaron?
- ¿Cuáles funcionaron y cuáles no?
- ¿En qué estado quedó el trabajo?

### 3. Obtener lista de archivos tocados (referencia auxiliar)

Ejecutar solo para completar la tabla de archivos:

```powershell
git status
```

### 4. Generar o actualizar HANDOFF.md

Escribir `HANDOFF.md` en la raíz del proyecto (`C:\Users\German Lucero\ProyectosChino\Crawl-Compare\HANDOFF.md`) con esta estructura exacta:

```markdown
# Handoff — YYYY-MM-DD

> Sesión: <tema inferido o argumento pasado>

## Objetivo
[Qué se estaba intentando lograr en esta sesión — 1 párrafo claro]

## Progreso actual
[Qué se completó, en qué estado quedó el trabajo — puede ser bullets o párrafo]

## Lo que funcionó
- `path/archivo.py:línea` — descripción de qué enfoque funcionó y por qué
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
| `path/archivo.py` | Descripción breve |
| ... | ... |
```

> Si no hubo enfoques fallidos, omitir la sección "Lo que no funcionó".

### 5. Confirmar en el chat

Después de escribir el archivo, informar:
- Ruta del archivo creado/actualizado
- Tema del resumen
- Si se integró contexto de un handoff previo

## Reglas

- **No actualizar memoria** como parte de este skill
- **Siempre verificar si HANDOFF.md ya existe** y leerlo antes de escribir
- **La fuente principal es la conversación**, no el git log ni el diff
- **Ser específico con los paths**: incluir número de línea cuando sea relevante (`UI/interfaz_ctk.py:142`)
- **Todo en español**
- **El argumento es solo una guía de foco**, no limita lo que se documenta
- La fecha en el header es la fecha actual real (leer de contexto del sistema)

## Ver también

- [MEMORY.md](../../.claude/projects/.../memory/MEMORY.md) — memoria persistente (actualizar manualmente si hay info nueva)
