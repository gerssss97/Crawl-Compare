# visual-bug-fix

Protocolo completo de debugging visual. Toma screenshot automático, clasifica el bug según si requiere o no interacción con la app, y decide si Claude simula esa interacción o la deja al usuario.

## Cuándo auto-activar (OBLIGATORIO — no esperar que el usuario lo pida)

Activar ANTES de cualquier análisis cuando el usuario:
- Reporta algo visual: "se ve mal", "quedó raro", "está cortado", "no aparece", "quedó grande/chico", "se superpone", "el icono no está"
- Pregunta "¿cómo se ve?", "¿podés ver la app?", "¿quedó bien?"
- Acaba de recibir un fix visual y hay que verificar el resultado

---

## Paso 1 — Screenshot inmediato

Ejecutar el script desde la raíz del proyecto:

```powershell
conda run -n crawler python .claude/skills/scripts/screenshot.py
```

Leer el resultado:

```
Read: C:\Users\German\Gerssss\IA\Hoteles\.claude\skills\scripts\app_qt_screenshot.png
```

> Exit code 255 es normal — `conda run` devuelve ese código al terminar una app Qt con `app.quit()`. Confirmar éxito buscando `SCREENSHOT_OK` en stdout.

---

## Paso 2 — Clasificar el bug

Con el screenshot en mano, clasificar según lo que se necesita para ver el bug:

### Tipo A — Estático

Visible en el estado inicial de la app, sin tocar nada.

**Ejemplos**: layout roto, colores incorrectos, texto cortado, icono faltante, padding mal, overflow, widget mal posicionado.

**Acción**: fix directo + screenshot de verificación post-fix. No preguntar nada al usuario.

---

### Tipo B — Dinámico simulable

El bug aparece después de una interacción reproducible programáticamente:
- Click en un botón conocido
- Abrir un modal o diálogo
- Seleccionar una opción en un dropdown/combobox
- Cambiar de tab
- Ingresar texto en un campo

**Acción**: preguntar en el chat (NO con AskUserQuestion, texto plano):

> "Para ver el bug necesito [navegar a / hacer click en / abrir] [X]. Puedo simular eso con un script Qt que [descripción concreta de la secuencia]. ¿Lo ejecuto yo, o preferís reproducirlo vos y pasarme un screenshot?"

Solo si el usuario confirma, generar el script basado en el template y ejecutarlo.

---

### Tipo C — Dinámico no simulable

El bug depende de estado que no se puede reproducir programáticamente:
- Resultados de scraping en vivo
- Estado de un proceso en curso (barra de progreso, loader)
- Datos externos que cambian en tiempo real
- Errores intermitentes

**Acción**: describir al usuario exactamente qué pasos reproducir y pedirle un screenshot manual.

---

## Paso 3 — Scripts de interacción (solo Tipo B)

Template base: [`.claude/skills/scripts/qt_interact_template.py`](.claude/skills/scripts/qt_interact_template.py)

### API de widgets Qt disponibles

```python
from PySide6.QtWidgets import QPushButton, QComboBox, QTabWidget, QWidget
from PySide6.QtCore import QTimer

# Botón por texto exacto
btn = next((b for b in win.findChildren(QPushButton) if b.text() == "Texto"), None)
if btn:
    btn.click()

# Todos los QComboBox (en orden de aparición en el layout)
combos = win.findChildren(QComboBox)
combos[0].setCurrentIndex(2)

# Cambiar tab activa
tabs = win.findChildren(QTabWidget)
if tabs:
    tabs[0].setCurrentIndex(1)

# Por objectName si el widget tiene uno asignado
widget = win.findChild(QWidget, "nombre_asignado")

# Para acciones que necesitan que Qt procese eventos primero
QTimer.singleShot(500, lambda: btn.click())
```

### Reglas del script ad-hoc

1. Guardar en `.claude/skills/scripts/qt_interact_{descripcion_corta}.py` (borrar después de resolver el bug)
2. Screenshot en cada paso significativo con nombre secuencial: `step_01_inicial.png`, `step_02_modal.png`
3. Tiempos mínimos: 0.5s entre clicks, 1.5s después de abrir modales, 3s para render inicial
4. Terminar siempre con `app.quit()` dentro del thread
5. Ejecutar con: `conda run -n crawler python .claude/skills/scripts/qt_interact_{descripcion}.py`

---

## Paso 4 — Fix + Verificación

Después de aplicar cualquier fix:

1. Ejecutar `screenshot.py` de nuevo
2. Leer el screenshot
3. Comparar con el estado pre-fix
4. Si el bug no desapareció → puede ser que el fix no tomó efecto, o que el bug sea Tipo B/C → reclasificar
5. Solo declarar resuelto cuando el screenshot lo confirma visualmente

---

## Notas técnicas

- **Screenshot negro o muy oscuro**: aumentar `time.sleep` en el thread de captura a 5-6 segundos
- **La instancia capturada es nueva**: no es la que el usuario tiene abierta. El estado siempre parte desde el arranque de `MainWindow`
- **`findChildren` es recursivo**: atraviesa toda la jerarquía de widgets sin importar la profundidad de anidamiento
- **`win.raise_()` + `win.activateWindow()`**: necesario para que la ventana quede al frente antes de capturar

## Ver también

- [Hoteles/UI_qt/interfaz_qt.py](../../Hoteles/UI_qt/interfaz_qt.py) - Clase `MainWindow`
- [docs/ui/componentes.md](../../docs/ui/componentes.md) - Catálogo de componentes Qt
- [docs/ui/troubleshooting-ctk.md](../../docs/ui/troubleshooting-ctk.md) - Troubleshooting visual histórico
