# /compare-debug

Skill para debugging detallado del fuzzy matching entre habitaciones de Excel y Web.

## Descripción

Muestra los 4 scores individuales de fuzzy matching (ratio, partial, token_sort, token_set), el score ponderado final, y detecta si la habitación incluye desayuno. Útil para entender por qué el sistema elige cierto match y ajustar pesos si es necesario.

## Uso

```bash
/compare-debug <habitacion_excel> <hab_web1> [hab_web2] [hab_web3] ...
```

## Parámetros

- **habitacion_excel** (requerido): Nombre de la habitación desde Excel (ej: "dbl superior w/breakfast")
- **hab_web1...habN** (requerido, 1+): Nombres de habitaciones web para comparar

## Output

Tabla ASCII con:
- Nombre de cada habitación web
- 4 scores individuales (0-100)
- Score ponderado final
- Detección de breakfast (✅/❌)
- Mejor match resaltado con color

## Ejemplo

```bash
/compare-debug "dbl superior w/breakfast" "Double Superior Room" "Superior Double with Breakfast" "Deluxe Double"
```

Output esperado:
```
🔍 Fuzzy Matching Debug
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Habitación Excel (limpia): "dbl superior breakfast"
Habitación Excel (original): "dbl superior w/breakfast"
Incluye breakfast: ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Habitación Web                      Ratio  Partial  Sort   Set    Final  BF
────────────────────────────────────────────────────────────────────────────
Superior Double with Breakfast      72.00  85.00    78.00  80.00  79.25  ✅  ← MEJOR MATCH
Double Superior Room                65.00  78.00    70.00  72.00  71.50  ❌
Deluxe Double                       45.00  52.00    48.00  50.00  49.25  ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pesos utilizados:
  • ratio:       20%
  • partial:     30%
  • token_sort:  25%
  • token_set:   25%

💡 Tip: Si el mejor match no es el esperado, considera ajustar los pesos
        en Core/comparador.py:18-22
```

## Uso desde Claude Code

Cuando el usuario te pida:
- "debuggear el matching de esta habitación"
- "mostrame los scores de fuzzy matching"
- "por qué eligió ese match?"
- "comparar estos nombres de habitaciones"

Ejecuta este skill con la habitación de Excel y las candidatas web.

## Implementación

Ver [scripts/compare_debug.py](scripts/compare_debug.py)