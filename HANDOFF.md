# Handoff — 2026-06-14

> Sesión: migración CustomTkinter → PySide6. **Fases 0-6 completas + modales + estética.**
> La app Qt está **funcionalmente completa**. Faltan: empaquetado (Fase 7) y limpieza (Fase 8).

## Contexto

Se migra la capa de vista de CustomTkinter a PySide6 porque el freeze de resize de CTk es estructural (rasterización software single-thread). Plan maestro: [docs/features/plan-migracion-gui.md](docs/features/plan-migracion-gui.md). Gotchas de Qt: [docs/ui/troubleshooting-qt.md](docs/ui/troubleshooting-qt.md).

**Entorno**: conda env `crawler` (Python 3.12.11). PySide6 6.11.0 instalado por **conda-forge** (NO pip: choca con ICU). Correr la app:
```
"C:/Users/German Lucero/anaconda3/envs/crawler/python.exe" Hoteles/UI_qt/interfaz_qt.py
```
(en cmd: sin el `&`; en PowerShell: con `&` adelante por las comillas).

## Lo hecho (Fases 0-6 + modales + estética) ✅

| Fase | Estado | Qué |
|---|---|---|
| 0 — Spike resize | ✅ | GATE superado: 18ms/frame vs ~1000ms CTk (~55x). |
| 1 — Núcleo desacoplado | ✅ | `ObservableVar` (Signal Qt con API de tk.Variable), `AppState` v2 sin Tkinter. Controladores reutilizados SIN tocar. |
| 2 — Shell + estilo | ✅ | `MainWindow` + QSS dual-mode (`theme.py`) + toggle tema en vivo. |
| 3 — Formulario | ✅ | Combos, fechas (QDateEdit calendario+manual+validación cruzada), huéspedes. |
| 4 — Paneles resultado | ✅ | Precio multiperiodo (desglose por tramos) + Períodos (rango directo). |
| 5+6 — Modales + threading | ✅ | `EventBridge` (EventBus→Qt Signals thread-safe), `QtResultadosModal` (paralelas), progreso, scraping real validado sin congelar. |
| 5 — Modales secundarios | ✅ | `QtHistorialModal`, `QtConfigModal`. |
| Iconos + estética | ✅ | QIcon+PNG (Feather), fondos de modales temados, HTML temado, file dialog nativo, períodos simplificados. |

**Estructura nueva** (toda en `Hoteles/UI_qt/`):
- `interfaz_qt.py` — `MainWindow` (orquestador, reemplaza interfaz_ctk.py).
- `state/` — `observable.py`, `app_state.py`, `event_bridge.py` (EventBus se reusa de `UI/`).
- `widgets/` — combos, fechas, forms, paneles precio/periodos, vista resultados, progress.
- `views/` — modales (resultados, historial, config).
- `styles/` — `theme.py` (QSS+paletas), `qt_icons.py` (QIcon/PNG), `icons_gen.py` (chevrons QPainter→PNG), `_generated/` (PNG cacheados, gitignored).

**Decisión clave de threading**: NO se usó el Patrón C (QThread/worker) del plan. Se dejó el `threading.Thread` del `ControladorComparacion` intacto + `EventBridge` del lado UI. Cero cambios al Core.

## Bugs resueltos en el camino (todos en troubleshooting-qt.md)

1. **ICU**: pip choca con conda → instalar por conda-forge.
2. **Labels con rectángulo negro**: no pintar `background-color` en `QWidget` base; `QLabel { background: transparent }`.
3. **Bootstrap sys.path**: al tope del archivo, guardado por `if __package__ in (None,"")`.
4. **SVG en QSS no renderiza** (plugin qsvg ausente en el env) → PNG por path / QPainter.
5. **Día calendario no se resaltaba** → `QTextCharFormat` (no QSS).
6. **UnicodeEncodeError (`→`)** en prints del Core sobre cp1252 → `sys.stdout.reconfigure(utf-8)` en bootstrap.
7. **Fondo negro en modales (light)** → reglas QSS para QDialog/QTextBrowser/etc.
8. **File dialog nativo no abría** → era por lanzar en background; normal anda.

## Pendiente (próximas sesiones)

### Fase 7 — Empaquetado (PyInstaller) ⏳
- Adaptar `Hoteles/Deploy/crawl_compare.spec` / `build_manifest.py` de CTk a PySide6.
- **Excluir módulos Qt no usados** (QtWebEngine, Qt3D, QtCharts, QtQuick, QtMultimedia, QtBluetooth...) para no inflar el .exe (PySide6-addons pesa ~168MB).
- Incluir assets: PNG de iconos (`UI/assets/icons/`), y asegurar que los chevrons de `_generated/` se generen en runtime (o pre-generarlos en el build).
- **Cuidado con la ICU/plugins de Qt**: el .exe debe llevar las DLLs de Qt correctas (las de conda-forge). Verificar que arranque el .exe portable y compare OK (smoke test). El plugin qsvg no se usa, no hace falta incluirlo.

### Fase 8 — Toggle + limpieza ⏳
- `main.py`: activar `UI_FRAMEWORK = "pyside6"` para arrancar la versión Qt.
- Una vez validado el .exe Qt: borrar `interfaz_ctk.py`, componentes `ctk_*`, dependencia `customtkinter`, y `icons_gen.py`/CTk icons si quedan sin uso.
- Renombrar `UI_qt/` → `UI/` (o mantener) y actualizar `docs/` (tree-directory, componentes, convenciones).

### Pulido estético adicional (opcional)
- El usuario fue puliendo sobre la marcha. La dirección visual (dual mode) está aprobada; mockup en Figma "Scrawler" (`B2s0j02LH07YYTdCTxTu6t`).

## Orden recomendado
Empaquetado (Fase 7) ANTES de borrar nada (Fase 8), así la CTk queda de respaldo si el .exe Qt falla.

---

## (Histórico) Sesión 2026-06-09 — origen de esta migración
Deploy onedir completado + diagnóstico de resize de CTk (~1000ms/frame, estructural, no arreglable con workarounds). Se decidió migrar de framework. Esa decisión derivó en todo lo de arriba.
