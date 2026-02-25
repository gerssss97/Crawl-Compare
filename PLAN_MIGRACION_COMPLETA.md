# 🔄 PLAN DE MIGRACIÓN - Interfaz Actual → CustomTkinter

## 📋 Estado Actual del Proyecto

### ✅ Completado hasta ahora:
- [x] Sistema de estilos (Colors, Typography, Spacing)
- [x] Componentes base (CTkBaseComponent, CTkCard)
- [x] Componentes de formulario (CTkLabeledComboBox, CTkDateInput, CTkLabeledEntry)
- [x] Demos funcionales

### 🎯 Objetivo:
Migrar la interfaz actual (`UI/interfaz.py` de 926 líneas) a CustomTkinter manteniendo toda la funcionalidad existente.

---

## 📂 Análisis de la Estructura Actual

### Archivo Principal: `UI/interfaz.py`
```
┌─ CrawlCompareGUI (clase principal) ────────────────────────┐
│                                                             │
│  ┌─ __init__ ─────────────────────────────────────────┐   │
│  │  - Inicializa ventana tkinter                       │   │
│  │  - Crea AppState y EventBus                         │   │
│  │  - Crea Controladores                               │   │
│  │  - Configura EventBus listeners                     │   │
│  │  - Llama a _crear_interfaz()                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ _crear_interfaz() ────────────────────────────────┐   │
│  │  Panel Izquierdo (formulario)                       │   │
│  │  - Hotel dropdown                                   │   │
│  │  - Edificio dropdown                                │   │
│  │  - Habitación dropdown                              │   │
│  │  - Fechas entrada/salida                            │   │
│  │  - Huéspedes                                        │   │
│  │  - Botón Ejecutar                                   │   │
│  │                                                      │   │
│  │  Panel Derecho (info)                               │   │
│  │  - PrecioPanel                                      │   │
│  │  - PeriodosPanel                                    │   │
│  │                                                      │   │
│  │  Panel Inferior (resultados)                        │   │
│  │  - VistaResultados                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ Controladores ────────────────────────────────────┐   │
│  │  - ControladorHotel                                 │   │
│  │  - ControladorPrecios                               │   │
│  │  - ControladorValidacion                            │   │
│  │  - ControladorComparacion                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ Event Handlers ───────────────────────────────────┐   │
│  │  - _on_hotel_changed()                              │   │
│  │  - _on_edificio_changed()                           │   │
│  │  - _on_habitacion_changed()                         │   │
│  │  - _on_ejecutar_clicked()                           │   │
│  │  - _on_comparison_started()                         │   │
│  │  - _on_comparison_completed()                       │   │
│  │  - _on_comparison_error()                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 ESTRATEGIA DE MIGRACIÓN

### Enfoque: Migración Gradual en Paralelo

**Ventajas:**
- ✅ No rompes el código actual
- ✅ Podés testear la nueva UI mientras la antigua sigue funcionando
- ✅ Rollback fácil si algo falla
- ✅ Migrás componente por componente

**Implementación:**
1. Crear `UI/interfaz_ctk.py` (nueva versión CustomTkinter)
2. Mantener `UI/interfaz.py` (versión legacy)
3. Toggle en `main.py` para elegir cuál usar
4. Una vez validada la nueva, eliminar la vieja

---

## 📋 PLAN PASO A PASO

### FASE 1: Preparación (15 min)

#### 1.1 Crear Toggle en main.py

```python
# main.py (agregar al inicio)

# ========================================
# CONFIGURACIÓN DE UI
# ========================================
USE_CUSTOMTKINTER = True  # Toggle: True = nueva UI, False = legacy

if USE_CUSTOMTKINTER:
    from UI.interfaz_ctk import CrawlCompareGUI
else:
    from UI.interfaz import CrawlCompareGUI

# ... resto del código sin cambios
```

#### 1.2 Backup de seguridad

```bash
# Crear backup del código actual
cp UI/interfaz.py UI/interfaz_legacy_backup.py
```

**Tiempo estimado:** 15 minutos

---

### FASE 2: Estructura Base de la Nueva Interfaz (1 hora)

#### 2.1 Crear `UI/interfaz_ctk.py`

**Estructura básica:**

```python
"""Interfaz principal de la aplicación - Versión CustomTkinter."""

import customtkinter as ctk
import tkinter as tk
from UI.styles import Colors, Spacing
from UI.state import AppState, EventBus
from UI.controllers import (
    ControladorHotel,
    ControladorPrecios,
    ControladorValidacion,
    ControladorComparacion
)
from UI.components import (
    CTkCard,
    CTkLabeledComboBox,
    CTkDateInput,
    CTkLabeledEntry
)


class CrawlCompareGUI:
    """Interfaz principal - Versión CustomTkinter."""
    
    def __init__(self, root):
        """Inicializa la interfaz.
        
        Args:
            root: Ventana raíz de tkinter/customtkinter
        """
        self.root = root
        
        # Configurar ventana principal
        self._configurar_ventana()
        
        # Inicializar estado y eventos
        self.event_bus = EventBus()
        self.estado_app = AppState(self.event_bus)
        
        # Inicializar controladores (sin cambios)
        self._inicializar_controladores()
        
        # Configurar listeners del EventBus (sin cambios)
        self._configurar_event_listeners()
        
        # Crear interfaz
        self._crear_interfaz()
        
        # Cargar datos iniciales (sin cambios)
        self._cargar_datos_iniciales()
    
    def _configurar_ventana(self):
        """Configura la ventana principal."""
        # Configurar CustomTkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Configurar ventana
        self.root.title("Crawl-Compare - Comparador de Precios")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=Colors.BACKGROUND)
    
    def _inicializar_controladores(self):
        """Inicializa todos los controladores (SIN CAMBIOS)."""
        # Exactamente igual que en interfaz.py
        self.controlador_hotel = ControladorHotel(
            self.estado_app,
            self.event_bus
        )
        
        self.controlador_precios = ControladorPrecios(
            self.estado_app,
            self.event_bus
        )
        
        self.controlador_validacion = ControladorValidacion(
            self.estado_app
        )
        
        self.controlador_comparacion = ControladorComparacion(
            self.estado_app,
            self.event_bus,
            self.controlador_validacion
        )
    
    def _configurar_event_listeners(self):
        """Configura los listeners del EventBus (SIN CAMBIOS)."""
        # Exactamente igual que en interfaz.py
        self.event_bus.subscribe('comparison_started', self._on_comparison_started)
        self.event_bus.subscribe('comparison_completed', self._on_comparison_completed)
        self.event_bus.subscribe('comparison_error', self._on_comparison_error)
    
    def _crear_interfaz(self):
        """Crea la interfaz completa."""
        # Header
        self._crear_header()
        
        # Contenedor principal con layout 55/45
        self._crear_contenedor_principal()
        
        # Panel izquierdo (formulario)
        self._crear_panel_izquierdo()
        
        # Panel derecho (info)
        self._crear_panel_derecho()
        
        # Panel inferior (resultados)
        self._crear_panel_resultados()
    
    def _crear_header(self):
        """Crea el header de la aplicación."""
        self.header = ctk.CTkFrame(
            self.root,
            fg_color=Colors.HEADER_BG,
            corner_radius=0,
            height=60
        )
        self.header.pack(fill='x', side='top')
        self.header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            self.header,
            text="Crawl-Compare - Comparador de Precios",
            font=("Inter", 18, "bold"),
            text_color=Colors.HEADER_TEXT
        )
        title.pack(side='left', padx=24, pady=16)
    
    def _crear_contenedor_principal(self):
        """Crea el contenedor principal con grid 55/45."""
        # TODO: Implementar
        pass
    
    def _crear_panel_izquierdo(self):
        """Crea el panel de formulario (izquierda)."""
        # TODO: Implementar usando CTkCard, CTkLabeledComboBox, etc.
        pass
    
    def _crear_panel_derecho(self):
        """Crea el panel de info (derecha)."""
        # TODO: Implementar usando PrecioPanel, PeriodosPanel
        pass
    
    def _crear_panel_resultados(self):
        """Crea el panel de resultados (abajo)."""
        # TODO: Implementar usando VistaResultados
        pass
    
    def _cargar_datos_iniciales(self):
        """Carga los datos iniciales del Excel (SIN CAMBIOS)."""
        # Exactamente igual que en interfaz.py
        pass
    
    # ========================================
    # EVENT HANDLERS (SIN CAMBIOS)
    # ========================================
    
    def _on_comparison_started(self):
        """Maneja el inicio de la comparación."""
        # Exactamente igual que en interfaz.py
        pass
    
    def _on_comparison_completed(self, resultado):
        """Maneja la finalización exitosa de la comparación."""
        # Exactamente igual que en interfaz.py
        pass
    
    def _on_comparison_error(self, error_msg):
        """Maneja errores en la comparación."""
        # Exactamente igual que en interfaz.py
        pass
```

**Tiempo estimado:** 1 hora

---

### FASE 3: Panel Izquierdo (Formulario) (2 horas)

#### 3.1 Implementar `_crear_panel_izquierdo()`

**Mapeo de componentes:**

| Componente Actual (tkinter) | Nuevo Componente (CTk) |
|------------------------------|------------------------|
| `LabeledComboBox` (Hotel) | `CTkLabeledComboBox` |
| `LabeledComboBox` (Edificio) | `CTkLabeledComboBox` |
| `LabeledComboBox` (Habitación) | `CTkLabeledComboBox` |
| `DateInputWidget` (Entrada) | `CTkDateInput` |
| `DateInputWidget` (Salida) | `CTkDateInput` |
| Entries de huéspedes | `CTkLabeledEntry` |
| `ttk.Button` (Ejecutar) | `ctk.CTkButton` |

**Código de ejemplo:**

```python
def _crear_panel_izquierdo(self):
    """Crea el panel de formulario."""
    # Contenedor con padding
    container = ctk.CTkFrame(
        self.panel_izquierdo,
        fg_color="transparent"
    )
    container.pack(fill='both', expand=True, padx=Spacing.XL, pady=Spacing.XL)
    
    # Card 1: Selección de Reserva
    card_reserva = CTkCard(
        container,
        title="SELECCIÓN DE RESERVA",
        icon="🏨"
    )
    card_reserva.pack(fill='x', pady=(0, Spacing.LG))
    
    # Hotel
    self.hotel_combo = CTkLabeledComboBox(
        card_reserva.content_frame,
        label="Hotel",
        icon="🏨",
        textvariable=self.estado_app.hotel
    )
    self.hotel_combo.pack(fill='x', pady=(0, Spacing.FORM_GAP))
    
    # ... resto de componentes
```

**Handlers a migrar (SIN CAMBIOS):**
- `_on_hotel_changed()`
- `_on_edificio_changed()`
- `_on_habitacion_changed()`
- `_on_ejecutar_clicked()`

**Tiempo estimado:** 2 horas

---

### FASE 4: Panel Derecho (Info) (2 horas)

#### 4.1 Migrar PrecioPanel a CustomTkinter

**Opción A:** Crear `CTkPrecioPanel` nuevo desde cero
**Opción B:** Adaptar el actual `PrecioPanel` para usar CTk

**Recomendación:** Opción A (más limpio)

**Archivo:** `UI/components/ctk_precio_panel.py`

```python
"""Panel de precio - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_card import CTkCard


class CTkPrecioPanel(CTkCard):
    """Panel que muestra precios por periodo."""
    
    def __init__(self, parent, textvariable=None, **kwargs):
        self.precio_var = textvariable
        super().__init__(parent, title="PRECIO POR NOCHE", icon="💰", **kwargs)
        
        if self.precio_var:
            self.precio_var.trace_add('write', self._on_precio_changed)
    
    def mostrar_precios_multiples(self, precios_data):
        """Muestra múltiples precios por periodo."""
        # Implementar según PrecioPanel actual
        pass
```

#### 4.2 Migrar PeriodosPanel a CustomTkinter

Similar al PrecioPanel.

**Tiempo estimado:** 2 horas

---

### FASE 5: Panel de Resultados (1 hora)

#### 5.1 Adaptar VistaResultados

**Opción A:** Mantener VistaResultados como está (usa tk.Text que es compatible)
**Opción B:** Crear CTkVistaResultados con CTkTextbox

**Recomendación:** Opción A inicialmente (menos trabajo)

El `tk.Text` widget funciona bien con CustomTkinter, solo necesitás cambiar el estilo del frame contenedor.

**Tiempo estimado:** 1 hora

---

### FASE 6: Testing y Ajustes (2 horas)

#### 6.1 Checklist de Testing

- [ ] Carga de datos del Excel funciona
- [ ] Dropdowns se poblan correctamente
- [ ] Cascada Hotel → Edificio → Habitación funciona
- [ ] Validación de fechas funciona
- [ ] Botón Ejecutar lanza comparación
- [ ] Panel de precio se actualiza
- [ ] Panel de periodos se actualiza
- [ ] Resultados se muestran correctamente
- [ ] Eventos del EventBus funcionan
- [ ] No hay errores en consola

#### 6.2 Ajustes Visuales

- [ ] Colores coinciden con mockups
- [ ] Espaciados son consistentes
- [ ] Hover effects funcionan
- [ ] Bordes y radius correctos
- [ ] Tipografía consistente

**Tiempo estimado:** 2 horas

---

## 📊 CRONOGRAMA DETALLADO

| Fase | Tarea | Tiempo | Acumulado |
|------|-------|--------|-----------|
| 1 | Preparación | 15 min | 15 min |
| 2 | Estructura base | 1 hora | 1h 15min |
| 3 | Panel izquierdo | 2 horas | 3h 15min |
| 4 | Panel derecho | 2 horas | 5h 15min |
| 5 | Panel resultados | 1 hora | 6h 15min |
| 6 | Testing y ajustes | 2 horas | **8h 15min** |

**Total:** ~8 horas (1 día de trabajo)

---

## 🎯 ORDEN SUGERIDO DE IMPLEMENTACIÓN

### Sesión 1 (3-4 horas)
1. ✅ Fase 1: Preparación + Toggle
2. ✅ Fase 2: Estructura base de interfaz_ctk.py
3. ✅ Fase 3: Panel izquierdo completo
4. ✅ Testing parcial del formulario

### Sesión 2 (3-4 horas)
5. ✅ Fase 4: Panel derecho (precio + periodos)
6. ✅ Fase 5: Panel de resultados
7. ✅ Fase 6: Testing completo y ajustes

---

## 🚨 PUNTOS CRÍTICOS A NO ROMPER

### ❌ NO Tocar:
- `AppState` - Mantener intacto
- `EventBus` - Mantener intacto
- Controladores - Mantener intactos
- Lógica de negocio en `Core/` - Mantener intacta
- Validadores - Mantener intactos

### ✅ Solo Cambiar:
- **Capa visual** (`_crear_interfaz()` y métodos relacionados)
- **Componentes UI** (usar versiones CTk)
- **Estilos visuales** (colores, fuentes, espaciados)

---

## 📝 ARCHIVOS A CREAR/MODIFICAR

### Nuevos Archivos:
- `UI/interfaz_ctk.py` (nuevo)
- `UI/components/ctk_precio_panel.py` (nuevo)
- `UI/components/ctk_periodos_panel.py` (nuevo)

### Archivos a Modificar:
- `main.py` (agregar toggle)
- `UI/components/__init__.py` (exportar nuevos componentes)

### Archivos a Mantener:
- `UI/interfaz.py` (legacy, no tocar hasta validar nueva UI)
- Todos los controladores
- AppState y EventBus
- Core/

---

## 🔄 ESTRATEGIA DE ROLLBACK

Si algo falla:

```python
# En main.py, cambiar:
USE_CUSTOMTKINTER = False  # Volver a la UI legacy

# Y listo, todo vuelve a funcionar como antes
```

---

## 📚 RECURSOS ÚTILES

### Documentación:
- CustomTkinter Docs: https://customtkinter.tomschimansky.com/
- Tus mockups en: `MockUps/`
- Plan completo en: `PLAN_MIGRACION_CUSTOMTKINTER.md`

### Scripts de Ayuda:
- `test_estilos.py` - Verificar sistema de estilos
- `demo_card.py` - Ver CTkCard
- `demo_formulario.py` - Ver formulario completo

---

## ✅ CHECKLIST FINAL

Antes de considerar la migración completa:

- [ ] Toggle en main.py funciona
- [ ] Nueva UI carga sin errores
- [ ] Todos los componentes se ven correctamente
- [ ] Funcionalidad completa migrada
- [ ] Testing exhaustivo pasado
- [ ] No hay regresiones en funcionalidad
- [ ] Diseño coincide con mockups
- [ ] Rendimiento es aceptable
- [ ] Código está comentado y documentado

Una vez todo ✅:
- [ ] Eliminar `UI/interfaz.py` (legacy)
- [ ] Renombrar `UI/interfaz_ctk.py` → `UI/interfaz.py`
- [ ] Remover toggle de main.py
- [ ] Commit final

---

## 🎓 CONCLUSIÓN

Esta migración es **no disruptiva** porque:
1. ✅ Trabajás en paralelo (nueva UI no afecta la vieja)
2. ✅ Toggle permite cambiar entre versiones
3. ✅ No tocás la lógica de negocio
4. ✅ Rollback es inmediato

**Tiempo total estimado:** 8 horas
**Complejidad:** Media
**Riesgo:** Bajo (gracias a estrategia de migración paralela)

---

**Última actualización:** 25 de Febrero, 2026
**Estado:** ✅ Plan completo - Listo para ejecutar
**Componentes base ya creados:** ✅ (CTkCard, CTkLabeledComboBox, CTkDateInput, CTkLabeledEntry)
