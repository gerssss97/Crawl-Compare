# TODO — Features pendientes / bugs a tratar

## Bugs

### Excel embebido se persiste en config.json con ruta de `_MEIPASS` — MITIGADO por `--onedir` (2026-06-09)

> **Estado**: el síntoma "se repite en cada arranque" quedó **resuelto al migrar a `--onedir`**
> (Fase 1 de [plan-instalador-diferenciado.md](plan-instalador-diferenciado.md)). Ahora `_MEIPASS`
> apunta a `_internal/` adyacente al `.exe`, un path **estable** entre ejecuciones, así que el
> path guardado en `config.json` sigue siendo válido al reabrir.
>
> **Caso residual NO cubierto**: si el usuario **mueve la carpeta** `CrawlCompare/` a otro lado,
> el path absoluto guardado vuelve a quedar muerto (una sola vez, hasta que el resolver lo limpie).
> El "Fix propuesto" de abajo (no persistir paths del Excel embebido por default) sigue siendo la
> solución prolija definitiva si se quiere cubrir ese caso. Prioridad baja.

**Síntoma** (histórico, modelo `--onefile`): en cada arranque del `.exe` aparecía en el log:
```
[excel_resolver] Último Excel (..._MEI87562\Data\Extracto_prueba2.xlsx) ya no existe. Limpiando config.
```

**Causa**: cuando el usuario abre el `.exe` por primera vez, `excel_resolver` carga el Excel embebido (que vive dentro de `_MEIPASS`, la carpeta temporal de PyInstaller) y `config_service` lo guarda en `config.json` como "último Excel usado". En la siguiente ejecución, PyInstaller crea **otra `_MEI<random>`** distinta, así que el path guardado apunta a una carpeta que ya no existe. El resolver detecta el problema y limpia la config, pero el ciclo se repite cada vez.

**Fix propuesto**: en `Core/services/config_service.py`, antes de persistir la ruta del Excel, validar que no contenga `_MEI` ni `\Temp\`. Si lo contiene, **no guardar** — es un Excel embebido por default, no uno elegido por el usuario. Alternativa más prolija: marcar el Excel embebido con una flag `is_embedded=True` y nunca persistirlo.

**Archivos involucrados**:
- `Hoteles/Core/services/config_service.py`
- `Hoteles/Core/excel_resolver.py`

**Prioridad**: baja (no rompe nada, solo ensucia el log y obliga al usuario a re-elegir Excel cada vez si no hay uno persistido válido).

---
