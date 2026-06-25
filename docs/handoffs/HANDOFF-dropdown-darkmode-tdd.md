# Handoff — Dropdown Dark Mode + TDD — 2026-06-23

> Sesión: Debug de dropdown en dark mode + decisión de adoptar pytest-qt como infraestructura de testing
> Tema: UI/Qt — componente QtLabeledCombo, theming dual-mode, testing

## Objetivo

Corregir dos bugs visuales del `QtLabeledCombo` en dark mode:
1. Las opciones del popup no se ven (texto casi blanco sobre fondo blanco)
2. El popup aparece cuadrado en lugar de redondeado como en light mode

## Progreso actual

El fix de código está aplicado pero **no verificado visualmente con certeza**. El screenshot automatizado muestra que los items son legibles en dark mode, pero no se puede confirmar si el fondo del popup es exactamente `#1E293B` (dark surface) o si hay algún issue residual.

Además, el usuario observó que **dark mode en general no tiene la misma calidad visual que light mode** — hay diferencias de pulido más allá del dropdown.

La infraestructura de pytest-qt todavía **no está instalada ni configurada**.

## Lo que funcionó

- `Hoteles/UI_qt/widgets/qt_labeled_combo.py` — Eliminar `_SURFACE`, `_BORDER`, `_R` hardcodeados a LIGHT. En `_configure_completer_popup`: reemplazar `popup.setStyleSheet(...)` con `popup.setAttribute(WA_TranslucentBackground)` + `popup.setObjectName("completerPopup")`. Esto elimina el override hardcodeado que pisaba el global stylesheet.
- `Hoteles/UI_qt/styles/stylesheet.py:99-118` — Agregar reglas `QListView#completerPopup` con colores del tema activo (`p.surface`, `p.text_primary`, etc.) + `border-radius` para esquinas redondeadas.
- `docs/ui/troubleshooting-qt.md` — Bug registrado con causa raíz, intento fallido y solución.

## Lo que no funcionó

- **Primer intento — `QComboBox QAbstractItemView::item` en stylesheet global**: agregamos `::item`, `::item:hover`, `::item:selected` al bloque `QComboBox QAbstractItemView`. No tuvo efecto porque el completer popup es un `QListView` top-level que NO es hijo de `QComboBox` en la jerarquía de widgets. El selector CSS no matchea.

- **Verificación con screenshot automático**: el script de captura (`visual-bug-fix` skill) tiene limitaciones para bugs Tipo B (requieren interacción). El popup es una ventana flotante separada que puede quedar fuera del bounding box capturado. El screenshot final mostró items legibles pero no fue concluyente sobre colores exactos. **Playwright no aplica** — solo funciona con browsers/Electron, no con Qt nativo.

## Causa raíz del bug (para referencia futura)

`_configure_completer_popup` en `qt_labeled_combo.py` llamaba `popup.setStyleSheet(...)` con constantes hardcodeadas a `LIGHT`:
```python
_BORDER = LIGHT.border   # siempre "#CBD5E1"
_SURFACE = LIGHT.surface # siempre "#FFFFFF"
```
Un stylesheet de widget tiene **mayor especificidad que el stylesheet de aplicación**. Resultado: el popup siempre usaba colores de light mode, sin importar el tema activo. Encima no seteaba `color`, entonces heredaba `#F1F5F9` (texto dark mode) sobre fondo blanco → invisible.

## Próximos pasos

1. **Verificar el fix visualmente** — Correr la app en dark mode manualmente, abrir el dropdown de Hotel, confirmar que el fondo es oscuro y el texto visible. Si el fondo todavía aparece blanco, el siguiente paso de debug es agregar `print(popup.styleSheet())` en `_configure_completer_popup` después de que la app aplique el stylesheet global.

2. **Instalar pytest-qt y escribir tests TDD** — El usuario adoptó pytest-qt como infraestructura de testing para widgets Qt. La secuencia:
   ```bash
   conda activate crawler
   pip install pytest-qt
   ```
   Luego crear `Hoteles/Tests/pytest/test_labeled_combo.py` con:
   - `test_completer_popup_tiene_objectname_correcto` — verifica `objectName() == "completerPopup"`
   - `test_completer_popup_tiene_translucent_background` — verifica `WA_TranslucentBackground`
   - `test_completer_popup_stylesheet_dark_mode` — verifica que el QSS global contiene `#completerPopup` con surface dark
   - Actualizar `docs/desarrollo/testing.md` con pytest-qt como infraestructura activa

3. **Auditar dark mode completo** — El usuario observó que dark mode no está a la misma altura visual que light mode. Hay que recorrer todos los componentes en dark mode y listar discrepancias. Candidatos probables:
   - Colores de borders y separadores
   - Contraste de `text_secondary` y `text_muted` sobre fondos dark
   - Estados hover/focus en botones
   - Modales (`QtResultadosModal`, `QtHistorialModal`) — pueden tener fondos hardcodeados

4. **Limpiar scripts temporales** — Borrar `.claude/skills/scripts/qt_interact_combo_dark.py` una vez que el fix esté verificado.

## Archivos clave tocados

| Archivo | Cambio |
|---------|--------|
| `Hoteles/UI_qt/widgets/qt_labeled_combo.py` | Eliminados `LIGHT`, `_R`, `_BORDER`, `_SURFACE`. `_configure_completer_popup` ahora setea `WA_TranslucentBackground` + `objectName("completerPopup")` sin hardcodear colores |
| `Hoteles/UI_qt/styles/stylesheet.py:99-118` | Nuevas reglas `QListView#completerPopup` con tokens del tema activo + `border-radius` |
| `docs/ui/troubleshooting-qt.md` | Bug registrado: "Completer popup: opciones invisibles + cuadrado en dark mode" con causa raíz, intento fallido y solución |
| `.claude/skills/scripts/qt_interact_combo_dark.py` | Script temporal de interacción para capturar el popup. Borrar después de verificar el fix |
