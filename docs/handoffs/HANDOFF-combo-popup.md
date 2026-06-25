# Handoff — Combo Popup — 2026-06-25

> Sesión: refactor arquitectural de `QtLabeledCombo` — transparencia de fondo, click-to-open, altura del popup
> Tema: UI/Qt — widget `QtLabeledCombo` y su popup del completer

## Objetivo

Resolver los problemas visuales y de comportamiento del `QtLabeledCombo`:
- Fondo transparente en los ítems del completer popup (main window sangraba a través)
- El popup no se abría al clickear el input
- Hueco vacío al final del popup al filtrar con pocos resultados
- Alinear con la decisión arquitectural: flechita → native dropdown redondeado, click/tipeo → completer popup

## Progreso actual

- ✅ Native dropdown (flechita): restaurado `super().showPopup()`, rounded corners via `_configure_popup()`, `setMaxVisibleItems(DROPDOWN_MAX_VISIBLE)`
- ✅ `_RoundedCombo` simplificado: sin override de completer, sin `_open_completer` attribute
- ✅ Fix transparencia: `popup.viewport().setObjectName("completerPopupViewport")` + regla QSS `QWidget#completerPopupViewport { background-color: {p.surface}; }`
- ✅ Fix GC del event filter: `self._click_filter = _LineEditClickFilter(...)` guardado en `self`
- ✅ Fix hueco: `popup.setMaximumHeight(32 * DROPDOWN_MAX_VISIBLE)` como techo estático en `_configure_completer_popup()`
- ⚠️ Los tres fixes anteriores **no fueron verificados** — la sesión terminó antes de probarlos

## Lo que funcionó

- `popup.viewport().setObjectName("completerPopupViewport")` + regla `QWidget#completerPopupViewport` en el QSS global — permite que el fondo del viewport del popup sea theme-aware sin hardcodear colores. Funciona porque el viewport es un `QWidget` hijo y la regla QSS lo alcanza por objectName.
- Guardar el event filter en `self._click_filter` — sin esto Python garbage-collectea el filtro antes de que dispare cualquier evento (no hay referencia Python que lo mantenga vivo; `installEventFilter` guarda solo una referencia C++).
- `setMaximumHeight` estático como techo: Qt recalcula el alto real del popup por ítems visibles, nuestra responsabilidad es solo el cap máximo.

## Lo que no funcionó

- `QListView#completerPopup::indicator { width: 0; image: none; }` — se pensó que las barritas `|` en los ítems eran el `::indicator` de Qt. No era eso: eran los bordes del card del main window sangrando por el fondo transparente del popup.
- `popup.viewport().setAutoFillBackground(False)` — dejaba los píxeles del viewport con alpha=0, haciendo que el desktop se viera a través (exactamente el problema opuesto al deseado).
- `setMaximumHeight(row_h * n + 8)` dinámico basado en `sizeHintForRow(0)`: si el size hint se calcula antes de que el QSS esté aplicado, devuelve 0 y el popup queda con altura mínima. Además usaba el total de ítems del modelo (no los ítems filtrados actuales), dejando hueco cuando había pocos resultados.

## Próximos pasos

1. **Verificar los tres fixes** corriendo la app (`conda activate crawler && python Hoteles/main.py`):
   - Click en el input → ¿abre el popup con todas las opciones?
   - Items del popup → ¿fondo sólido (no transparente)?
   - Tipear "F" (2 matches) y luego "Fo" (1 match) → ¿el popup se ajusta sin hueco?
   - Flechita → ¿native dropdown redondeado con max 4 ítems?
   - Toggle dark mode → ¿fondo correcto del popup en ambos temas?

2. **Si la transparencia persiste**: el `QWidget#completerPopupViewport` QSS podría no estar aplicándose. Alternativa: `popup.viewport().setStyleSheet(f"background-color: {surface_color};")` directo, actualizándolo en el toggle de tema.

3. **Si el hueco persiste**: 32px × 4 = 128px puede ser un techo demasiado grande si el row height real es mayor. Podría usarse `QTimer.singleShot(0, lambda: ajustar_alto())` después de `complete()` para leer el alto real una vez que el popup está pintado.

4. **Si click no abre**: agregar un `print` en `_open_completer_popup` para confirmar que se llama. Si no llega, el event filter sigue sin funcionar.

## Archivos clave tocados

| Archivo | Cambio |
|---------|--------|
| `Hoteles/UI_qt/widgets/qt_labeled_combo.py` | Refactor: native `showPopup()`, `_LineEditClickFilter` simplificado con GC fix, `_configure_completer_popup` con cap estático, `_open_completer_popup` sin cálculo de altura |
| `Hoteles/UI_qt/styles/stylesheet.py` | Agregado `QWidget#completerPopupViewport`, `QComboBox QAbstractItemView::indicator`, `QListView#completerPopup::indicator`, ajuste padding/min-height en items del completer |
