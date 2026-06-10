# Handoff — 2026-06-09

> Sesión: Deploy onedir (completado) + diagnóstico de performance de resize → decisión de evaluar migración de framework UI

## Objetivo

Dos temas en la sesión:
1. **Deploy**: aplicar la Opción 2 del plan de instalador (pasar PyInstaller de `--onefile` a `--onedir`, app "portable"). **Completado.**
2. **Performance**: resolver el freeze al hacer resize de la ventana CTk. Se diagnosticó a fondo, se midió todo, y **se decidió NO seguir con workarounds**: la próxima sesión va a evaluar migrar a otro framework de UI de Python, porque el cuello de botella es estructural de CustomTkinter.

---

## Parte 1 — Deploy onedir ✅ COMPLETADO

### Qué se hizo
- `crawl_compare.spec`: `EXE(...)` ahora con `exclude_binaries=True` y sin `a.binaries`/`a.datas` adentro; se agregó `COLLECT(...)` que arma la carpeta `dist/CrawlCompare/` con `.exe` + `_internal/`.
- `build.bat`: variable `EXE_PATH=%DIST_DIR%\CrawlCompare\CrawlCompare.exe`, usada en el smoke test `[4/4]` y el mensaje final.
- Docs actualizados: `build-deploy.md`, `plan-instalador-diferenciado.md` (Fase 1 marcada implementada), `TODO.md` (bug del Excel marcado MITIGADO, no resuelto del todo — ver abajo).

### Clave técnica
En onedir `sys._MEIPASS` apunta a `_internal/` (path estable), así que **cero cambios de código de runtime**. El bug del Excel persistido en `config.json` se mitiga por construcción.

### PENDIENTE de verificar (no se buildeó)
- Falta correr `Deploy\build.bat` desde Anaconda Prompt y confirmar smoke test 9/9 + portabilidad de la carpeta. Todo el cambio es estático hasta ahora.
- **Caso residual del bug del Excel**: si el usuario MUEVE la carpeta `CrawlCompare/`, el path absoluto en `config.json` vuelve a quedar muerto una vez. El fix prolijo (no persistir path del Excel embebido por default) sigue en `docs/features/TODO.md`, prioridad baja.

---

## Parte 2 — Performance de resize: DIAGNÓSTICO CERRADO, decisión de migrar

### Síntoma
Al arrastrar el borde de la ventana, la UI **se congela ~1 segundo**. Pasa en toda la ventana desde el arranque, sin depender de contenido cargado.

### Causa raíz (MEDIDA, no teorizada)
CustomTkinter dibuja las esquinas redondeadas/bordes/fondo de **cada widget** sobre un `CTkCanvas` propio. La ventana tiene **44 canvas**. En cada frame de resize se disparan **~67 eventos `<Configure>`** y cada canvas afectado se rasteriza de nuevo, en un único hilo Tcl/Tk. Resultado: **avg ~1000ms, peor ~2000ms por frame**.

Esto es **estructural de CTk**, no de nuestro código. El maintainer cerró el issue oficial de resize-lag como **"not planned"** (CTk #2690). El propio draw_engine dice "no much I can do with the limited capabilities tkinter.Canvas offers".

### Lo que se probó y NO funcionó (medido, para NO repetir)
| Enfoque | Resultado | Veredicto |
|---|---|---|
| Sacar `uniform="cols"` del grid (interfaz_ctk.py:162) | 969ms | No sirvió. **Quedó aplicado igual** (era costo innecesario, invisible). |
| `preferred_drawing_method = "polygon_shapes"` | 804ms (-30%) | Insuficiente, sigue siendo freeze. |
| Saltear redibujos redundantes | CTk YA lo hace (`_update_dimensions_event` en ctk_base_class.py:184 solo redibuja si cambió el tamaño) | Nada que cortar. |
| Aplanar CTkFrame transparentes (opción E) | Solo 8 de 44 canvas son aplanables → techo ~730ms | Descartada. |
| Ocultar solo el panel derecho durante drag | 1263ms (PEOR que baseline) | Contraproducente: el `uniform`/weight agranda el panel izq (el más pesado). |

### Lo que SÍ funcionó (medido)
| Enfoque | Resultado |
|---|---|
| Ocultar AMBOS paneles durante drag | 212ms |
| **Placeholder plano (tkinter.Frame, 1 canvas) durante drag** | **67ms/frame** (17x más rápido), restore al soltar ~400ms (un solo frame) |

La opción A' (placeholder plano durante el drag + restaurar al soltar) era la candidata técnica ganadora.

### Por qué NO se implementó A' (lo que destrabó la decisión de migrar)
El usuario rechazó el trade-off visual: durante el arrastre **no se ve el contenido**, se ve un rectángulo plano del color de fondo. Además A' depende inevitablemente de un debounce interno (Tk no tiene evento "fin de drag", solo `<Configure>` durante). Ninguna opción en CTk da las 3 cosas juntas: **ver el contenido + reacomodándose en vivo + sin lag**. Esa combinación es imposible con 44 canvas en single-thread.

**Conclusión del usuario**: si la fluidez de resize importa, conviene evaluar otro framework antes de invertir en workarounds que igual sacrifican algo.

---

## Próximos pasos (próxima sesión)

1. **Verificar el build onedir**: correr `Deploy\build.bat`, confirmar 9/9 + portabilidad. (Tema 1, queda colgado de verificación.)
2. **Explorar migración de framework UI de Python**. Foco: que el resize sea fluido manteniendo estética moderna. Candidatos a evaluar (NO investigados aún esta sesión):
   - **PySide6 / PyQt6** (Qt) — rendering nativo acelerado, resize fluido, el más maduro. Curva de aprendizaje y reescritura grande.
   - **Flet** (Flutter para Python) — moderno, declarativo.
   - **Toga / BeeWare**, **Dear PyGui** (GPU-accelerated, muy fluido), **wxPython**.
   - Criterios a sopesar: fluidez de resize, esfuerzo de migración desde la arquitectura Event-Driven MVC actual (EventBus + controladores son agnósticos a la UI → reutilizables), look & feel, distribución/empaquetado (ya tenemos PyInstaller andando).
3. La lógica de negocio (Core, controladores, EventBus, AppState) **es reutilizable** en cualquier framework — solo se reescribe la capa de vista (`UI/`). Eso baja el costo de migrar.

---

## Archivos clave tocados esta sesión

| Archivo | Cambio |
|---------|--------|
| `Hoteles/Deploy/crawl_compare.spec` | onefile → onedir (`exclude_binaries=True` + `COLLECT`) |
| `Hoteles/Deploy/build.bat` | `EXE_PATH` con nuevo path del smoke test |
| `Hoteles/UI/interfaz_ctk.py:162` | quitado `uniform="cols"` (fix parcial de resize, invisible, quedó aplicado) |
| `docs/deploy/build-deploy.md` | output ahora carpeta + `_internal/`, distribución por `.zip` |
| `docs/features/plan-instalador-diferenciado.md` | Fase 1 marcada IMPLEMENTADA |
| `docs/features/TODO.md` | bug del Excel marcado MITIGADO por onedir |
| `CLAUDE.md` | nueva regla: no mostrar modales al explicar soluciones (solo texto) |
| `.claude/skills/scripts/resize_*.py` | scripts de medición de performance (probe, bisect, drawmethod, subtree, placeholder) — referencia para la evaluación de migración |

> **Nota sobre los scripts de medición**: `resize_placeholder.py`, `resize_subtree.py`, etc. en `.claude/skills/scripts/` quedan como evidencia reproducible. Si en la migración se quiere comparar el nuevo framework contra CTk, el patrón de medición (drag simulado con `geometry()` + cronometrar `update_idletasks()`) sirve de baseline.
