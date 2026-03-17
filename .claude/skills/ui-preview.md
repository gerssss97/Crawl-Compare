# ui-preview

Preview de componentes UI individuales en ventanas standalone sin ejecutar toda la aplicación.

## Uso

```bash
python .claude/skills/scripts/ui_preview.py [componente] [--datos]
```

**Parámetros**:
- `componente`: Nombre del componente o vista a previsualizar (ver lista abajo)
- `--datos`: JSON opcional con datos de prueba

## Componentes Disponibles

### Widgets Básicos
```bash
# DateInputWidget - Selector de fechas
python .claude/skills/scripts/ui_preview.py fecha

# LabeledComboBox - Combobox con label
python .claude/skills/scripts/ui_preview.py combo

# EntradaEtiquetada - Campo de texto con etiqueta
python .claude/skills/scripts/ui_preview.py entrada

# PrecioPanel - Panel de visualización de precio
python .claude/skills/scripts/ui_preview.py precio

# PeriodosPanel - Panel de visualización de periodos
python .claude/skills/scripts/ui_preview.py periodos
```

### Vistas
```bash
# FormularioSeleccionHotel - Formulario completo de selección
python .claude/skills/scripts/ui_preview.py formulario

# FormularioReserva - Formulario de reserva
python .claude/skills/scripts/ui_preview.py formulario-reserva

# VistaResultados - Vista completa de resultados
python .claude/skills/scripts/ui_preview.py resultados
```

## Ejemplos

### Preview básico
```bash
# DateInputWidget con defaults
python .claude/skills/scripts/ui_preview.py fecha
```

### Preview con datos
```bash
# Combobox con opciones personalizadas
python .claude/skills/scripts/ui_preview.py combo --datos='{"opciones": ["Hotel A", "Hotel B", "Hotel C"], "default": "Hotel A"}'

# Vista resultados con múltiples periodos
python .claude/skills/scripts/ui_preview.py resultados --datos='{"periodos": 3, "discrepancias": 2}'
```

### Preview interactivo
```bash
# Formulario completo con datos de prueba
python .claude/skills/scripts/ui_preview.py formulario
```

## Output Esperado

```
🎨 UI Preview - Componente: FormularioSeleccionHotel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Cargando componente...
✅ Componente cargado

🔧 Configuración:
   - Tipo: Componente compuesto
   - Hereda de: BaseComponent
   - Métodos disponibles: _setup_ui, get_value, set_value, reset

🎯 Datos de prueba:
   - Hoteles: 5
   - Habitaciones: 12
   - Periodos: 8

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🪟 Abriendo ventana preview...

[Se abre ventana Tkinter con el componente]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Tips:
   - Interactúa con el componente para probarlo
   - Cierra la ventana cuando termines
   - Los cambios NO se guardan (es solo preview)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Comportamiento

1. **Parser de argumentos**: Lee componente y datos opcionales
2. **Carga dinámica**: Importa el módulo del componente especificado
3. **Datos de prueba**: Genera datos fake o usa los provistos en --datos
4. **Ventana standalone**: Crea Tk() root y empaqueta el componente
5. **Inspector de métodos**: Muestra info del componente (herencia, métodos)
6. **Mainloop**: Ejecuta `root.mainloop()` para interacción
7. **Cleanup**: Destruye ventana al cerrar

## Estructura del Script

```python
COMPONENTES = {
    # Widgets básicos
    'fecha': ('UI.components.date_input', 'DateInputWidget'),
    'combo': ('UI.components.labeled_combobox', 'LabeledComboBox'),
    'entrada': ('UI.components.entrada_etiquetada', 'EntradaEtiquetada'),
    'precio': ('UI.components.precio_panel', 'PrecioPanel'),
    'periodos': ('UI.components.periodos_panel', 'PeriodosPanel'),

    # Vistas
    'formulario': ('UI.views.formulario_seleccion_hotel', 'FormularioSeleccionHotel'),
    'formulario-reserva': ('UI.views.formulario_reserva', 'FormularioReserva'),
    'resultados': ('UI.views.vista_resultados', 'VistaResultados'),
}

def generar_datos_prueba(componente_nombre):
    """Genera datos de prueba según el tipo de componente"""
    # Excel fake, EventBus mock, etc.
    pass

def previsualizar_componente(nombre, datos=None):
    """Crea ventana standalone con el componente"""
    # Importación dinámica
    # Setup de ventana
    # Instanciación de componente
    # Mainloop
    pass
```

## Casos de Uso

### 1. Desarrollo de nuevo componente
```bash
# Testear componente sin ejecutar app completa
python .claude/skills/scripts/ui_preview.py mi-nuevo-widget
```

### 2. Debug visual
```bash
# Verificar layout de formulario
python .claude/skills/scripts/ui_preview.py formulario

# Testear vista con muchos periodos
python .claude/skills/scripts/ui_preview.py resultados --datos='{"periodos": 12}'
```

### 3. Testing de componentes
```bash
# Testear panel de precio
python .claude/skills/scripts/ui_preview.py precio

# Testear panel de periodos
python .claude/skills/scripts/ui_preview.py periodos
```

### 4. Documentación visual
```bash
# Capturar screenshots para docs
python .claude/skills/scripts/ui_preview.py fecha
# → Tomar screenshot manualmente
```

## Notas de Implementación

- **Importación dinámica**: `importlib.import_module()` para cargar componentes
- **Mock de dependencias**: EventBus y AppState simulados si es necesario
- **Datos fake**: Usar Faker o datos hardcoded según componente
- **Ventana standalone**: `tk.Tk()` como root (NO Toplevel)
- **Cleanup automático**: `root.protocol("WM_DELETE_WINDOW", cleanup_handler)`
- **Hot reload**: Opcional - recargar módulo si cambia (watchdog)

## Dependencias

- `tkinter` - UI
- `sys` - Argumentos CLI
- `json` - Parser de --datos
- `importlib` - Carga dinámica de módulos
- `pathlib` - Resolución de paths

## Errores Comunes

### Error: "Componente no encontrado"
**Solución**: Verificar nombre del componente. Ejecutar `python .claude/skills/scripts/ui_preview.py --list` para ver opciones disponibles.

### Error: "ModuleNotFoundError"
**Solución**: Agregar path raíz al PYTHONPATH o ejecutar desde directorio raíz.

### Error: "EventBus required"
**Solución**: El componente requiere EventBus real. Ejecutar con `--mock-eventbus` para usar mock.

## Extensiones Futuras

- `--list`: Listar todos los componentes disponibles
- `--inspect`: Mostrar info del componente sin abrir ventana
- `--watch`: Hot reload automático al detectar cambios
- `--screenshot`: Capturar screenshot automáticamente
- `--interactive`: REPL para ejecutar métodos del componente

---

Ver también:
- [docs/ui/componentes.md](../../docs/ui/componentes.md) - Catálogo de componentes
- [docs/desarrollo/convenciones.md](../../docs/desarrollo/convenciones.md) - BaseComponent pattern
- [docs/desarrollo/testing.md](../../docs/desarrollo/testing.md) - Testing de UI
