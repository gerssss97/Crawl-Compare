# 🚀 PLAN DE MIGRACIÓN A CUSTOMTKINTER

## 📋 Índice
1. [Preparación Inicial](#fase-0-preparación-inicial)
2. [Sistema de Estilos](#fase-1-sistema-de-estilos)
3. [Componentes Base](#fase-2-componentes-base)
4. [Vistas Principales](#fase-3-vistas-principales)
5. [Integración Final](#fase-4-integración-final)
6. [Testing y Refinamiento](#fase-5-testing)

---

## FASE 0: Preparación Inicial

### ✅ Tareas Previas
- [x] Mockups de diseño aprobados
- [ ] Instalar CustomTkinter
- [ ] Crear branch de migración
- [ ] Backup del código actual

### 📦 Instalación

```bash
# Activar entorno conda
conda activate deep-seek-crawler

# Instalar CustomTkinter
pip install customtkinter

# Verificar instalación
python -c "import customtkinter; print(customtkinter.__version__)"
```

**Versión esperada:** >= 5.2.0

---

## FASE 1: Sistema de Estilos Centralizado

### Objetivo
Crear un sistema de colores, tipografías y constantes de diseño basado en los mockups.

### Archivos a Crear/Modificar

#### 1.1 `UI/styles/colors.py` (NUEVO)
```python
"""Paleta de colores del sistema - Basada en mockups aprobados."""

class Colors:
    # Primarios
    PRIMARY = "#2563EB"           # Azul eléctrico
    PRIMARY_HOVER = "#1D4ED8"     # Azul hover
    PRIMARY_LIGHT = "#DBEAFE"     # Azul claro
    
    # Semánticos
    SUCCESS = "#10B981"           # Verde
    SUCCESS_LIGHT = "#D1FAE5"     # Verde claro
    
    WARNING = "#F59E0B"           # Naranja
    WARNING_LIGHT = "#FEF3C7"     # Naranja claro
    
    ERROR = "#EF4444"             # Rojo
    ERROR_LIGHT = "#FEE2E2"       # Rojo claro
    
    # Neutrales
    BACKGROUND = "#F8FAFC"        # Fondo app
    SURFACE = "#FFFFFF"           # Cards/Paneles
    BORDER = "#E2E8F0"            # Bordes
    
    TEXT_PRIMARY = "#1E293B"      # Texto principal
    TEXT_SECONDARY = "#64748B"    # Texto secundario
    TEXT_DISABLED = "#94A3B8"     # Texto disabled
    
    HEADER_BG = "#1E293B"         # Fondo header
    HEADER_TEXT = "#FFFFFF"       # Texto header
```

**Estimación:** 15 minutos

---

#### 1.2 `UI/styles/typography.py` (NUEVO)
```python
"""Configuración tipográfica centralizada."""

class Typography:
    # Familia de fuente
    FAMILY = "Inter"
    FALLBACK = ("Segoe UI", "Arial", "sans-serif")
    
    # Tamaños (en pixeles)
    H1 = 18       # Títulos principales
    H2 = 16       # Títulos secciones
    BODY = 14     # Texto normal
    SMALL = 12    # Labels, hints
    PRECIO = 28   # Precios destacados
    
    # Pesos
    NORMAL = "normal"
    MEDIUM = "medium"
    BOLD = "bold"
```

**Estimación:** 10 minutos

---

#### 1.3 `UI/styles/spacing.py` (NUEVO)
```python
"""Sistema de espaciado consistente."""

class Spacing:
    # Espaciados base
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    
    # Padding para elementos
    CARD_PADDING = 24
    PANEL_PADDING = 32
    BUTTON_PADDING = (14, 24)  # (vertical, horizontal)
    
    # Gaps
    FORM_GAP = 20
    ELEMENT_GAP = 16
    
    # Border Radius
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12
```

**Estimación:** 10 minutos

---

#### 1.4 `UI/styles/__init__.py` (MODIFICAR)
```python
"""Exportar todos los estilos centralizados."""

from .colors import Colors
from .typography import Typography
from .spacing import Spacing
from .fonts import FontManager

__all__ = ['Colors', 'Typography', 'Spacing', 'FontManager']
```

**Estimación:** 5 minutos

**Total Fase 1:** ~40 minutos

---

## FASE 2: Componentes Base con CustomTkinter

### Objetivo
Migrar componentes reutilizables de tkinter → CustomTkinter

### Prioridad de Migración

#### 2.1 `UI/components/ctk_base_component.py` (NUEVO)
```python
"""Componente base para CustomTkinter - reemplaza base_component.py"""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing

class CTkBaseComponent(ctk.CTkFrame):
    """Clase base para todos los componentes CustomTkinter."""
    
    def __init__(self, parent, **kwargs):
        # Configurar defaults con nuestros estilos
        kwargs.setdefault('fg_color', Colors.SURFACE)
        kwargs.setdefault('corner_radius', Spacing.RADIUS_MD)
        
        super().__init__(parent, **kwargs)
        self._setup_ui()
    
    def _setup_ui(self):
        """Sobreescribir en subclases."""
        pass
```

**Estimación:** 20 minutos

---

#### 2.2 `UI/components/ctk_card.py` (NUEVO)
```python
"""Card component - Contenedor visual para agrupar elementos."""

import customtkinter as ctk
from UI.styles import Colors, Spacing
from .ctk_base_component import CTkBaseComponent

class CTkCard(CTkBaseComponent):
    """Card con título y contenido."""
    
    def __init__(self, parent, title=None, icon=None, **kwargs):
        self.title_text = title
        self.icon = icon
        super().__init__(parent, **kwargs)
    
    def _setup_ui(self):
        self.configure(
            border_width=1,
            border_color=Colors.BORDER
        )
        
        if self.title_text:
            title_frame = ctk.CTkFrame(
                self,
                fg_color="transparent"
            )
            title_frame.pack(fill='x', padx=Spacing.CARD_PADDING, 
                           pady=(Spacing.CARD_PADDING, Spacing.SM))
            
            title_label = ctk.CTkLabel(
                title_frame,
                text=f"{self.icon} {self.title_text}" if self.icon else self.title_text,
                font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
                text_color=Colors.TEXT_SECONDARY
            )
            title_label.pack(side='left')
        
        # Frame de contenido
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(
            fill='both',
            expand=True,
            padx=Spacing.CARD_PADDING,
            pady=(0, Spacing.CARD_PADDING)
        )
```

**Estimación:** 30 minutos

---

#### 2.3 `UI/components/ctk_labeled_combobox.py` (MIGRACIÓN)
```python
"""ComboBox con label - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent

class CTkLabeledComboBox(CTkBaseComponent):
    """ComboBox con label arriba."""
    
    def __init__(self, parent, label, icon=None, textvariable=None, 
                 values=None, state="normal", **kwargs):
        self.label_text = label
        self.icon = icon
        self.textvariable = textvariable
        self.values = values or []
        self.state = state
        super().__init__(parent, fg_color="transparent", **kwargs)
    
    def _setup_ui(self):
        # Label
        label_text = f"{self.icon} {self.label_text}" if self.icon else self.label_text
        label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(Typography.FAMILY, Typography.BODY, Typography.MEDIUM),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        )
        label.pack(fill='x', pady=(0, Spacing.SM))
        
        # ComboBox
        self.combobox = ctk.CTkComboBox(
            self,
            values=self.values,
            variable=self.textvariable,
            state=self.state,
            font=(Typography.FAMILY, Typography.BODY),
            dropdown_font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_HOVER,
            dropdown_fg_color=Colors.SURFACE,
            dropdown_hover_color=Colors.PRIMARY_LIGHT,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Spacing.RADIUS_MD
        )
        self.combobox.pack(fill='x')
    
    def set_values(self, values):
        """Actualizar valores del combobox."""
        self.combobox.configure(values=values)
    
    def set_state(self, state):
        """Cambiar estado (normal/disabled)."""
        self.combobox.configure(state=state)
```

**Estimación:** 40 minutos

---

#### 2.4 `UI/components/ctk_date_input.py` (MIGRACIÓN)
```python
"""Input de fecha DD-MM-AAAA - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_base_component import CTkBaseComponent

class CTkDateInput(CTkBaseComponent):
    """Componente de entrada de fecha con 3 campos."""
    
    def __init__(self, parent, label, icon=None, 
                 day_var=None, month_var=None, year_var=None, **kwargs):
        self.label_text = label
        self.icon = icon
        self.day_var = day_var
        self.month_var = month_var
        self.year_var = year_var
        super().__init__(parent, fg_color="transparent", **kwargs)
    
    def _setup_ui(self):
        # Label
        label_text = f"{self.icon} {self.label_text}" if self.icon else self.label_text
        label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(Typography.FAMILY, Typography.BODY, Typography.MEDIUM),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        )
        label.pack(fill='x', pady=(0, Spacing.SM))
        
        # Frame para los 3 inputs
        inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        inputs_frame.pack(fill='x')
        
        # DD
        self.day_entry = ctk.CTkEntry(
            inputs_frame,
            width=70,
            placeholder_text="DD",
            textvariable=self.day_var,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_DISABLED,
            corner_radius=Spacing.RADIUS_MD
        )
        self.day_entry.pack(side='left', padx=(0, Spacing.SM))
        
        # MM
        self.month_entry = ctk.CTkEntry(
            inputs_frame,
            width=90,
            placeholder_text="MM",
            textvariable=self.month_var,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_DISABLED,
            corner_radius=Spacing.RADIUS_MD
        )
        self.month_entry.pack(side='left', padx=(0, Spacing.SM))
        
        # AAAA
        self.year_entry = ctk.CTkEntry(
            inputs_frame,
            width=100,
            placeholder_text="AAAA",
            textvariable=self.year_var,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_DISABLED,
            corner_radius=Spacing.RADIUS_MD
        )
        self.year_entry.pack(side='left')
```

**Estimación:** 45 minutos

---

#### 2.5 `UI/components/ctk_precio_panel.py` (MIGRACIÓN)
```python
"""Panel de precio - versión CustomTkinter con diseño mejorado."""

import customtkinter as ctk
from UI.styles import Colors, Typography, Spacing
from .ctk_card import CTkCard

class CTkPrecioPanel(CTkCard):
    """Panel que muestra precios con diseño visual atractivo."""
    
    def __init__(self, parent, textvariable=None, **kwargs):
        self.precio_var = textvariable
        super().__init__(parent, title="PRECIO POR NOCHE", icon="💰", **kwargs)
        
        # Suscribirse a cambios del precio
        if self.precio_var:
            self.precio_var.trace_add('write', self._on_precio_changed)
    
    def _setup_ui(self):
        super()._setup_ui()
        
        # Mensaje inicial
        self._mostrar_mensaje("(ninguna seleccionada)")
    
    def _mostrar_mensaje(self, mensaje):
        """Mostrar mensaje cuando no hay precio."""
        # Limpiar contenido anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        label = ctk.CTkLabel(
            self.content_frame,
            text=mensaje,
            font=(Typography.FAMILY, Typography.BODY),
            text_color=Colors.TEXT_DISABLED
        )
        label.pack(expand=True)
    
    def mostrar_precios_multiples(self, precios_data):
        """Mostrar múltiples precios por periodo."""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if not precios_data:
            self._mostrar_mensaje("(Ingrese fechas para ver precios)")
            return
        
        # Crear scrollable frame si hay muchos períodos
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill='both', expand=True)
        
        for item in precios_data:
            periodo = item['periodo']
            precio = item['precio']
            nombre_grupo = item['nombre_grupo']
            
            # Frame por periodo con gradiente azul
            periodo_frame = ctk.CTkFrame(
                scroll_frame,
                fg_color=Colors.PRIMARY_LIGHT,
                corner_radius=Spacing.RADIUS_MD,
                border_width=1,
                border_color=Colors.BORDER
            )
            periodo_frame.pack(fill='x', pady=Spacing.SM)
            
            # Nombre del grupo
            ctk.CTkLabel(
                periodo_frame,
                text=f"Periodo: {nombre_grupo}",
                font=(Typography.FAMILY, Typography.SMALL, Typography.BOLD),
                text_color=Colors.TEXT_PRIMARY,
                anchor='w'
            ).pack(fill='x', padx=Spacing.SM, pady=(Spacing.SM, 2))
            
            # Fechas
            fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
            fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
            fecha_str = f"📅 {fecha_inicio_str} - {fecha_fin_str}"
            
            ctk.CTkLabel(
                periodo_frame,
                text=fecha_str,
                font=(Typography.FAMILY, Typography.SMALL),
                text_color=Colors.TEXT_SECONDARY,
                anchor='w'
            ).pack(fill='x', padx=Spacing.SM, pady=2)
            
            # Precio
            if isinstance(precio, (int, float)):
                precio_texto = f"💵 ${precio:.2f}"
                precio_fg = Colors.SUCCESS_LIGHT
                precio_color = Colors.SUCCESS
            else:
                precio_texto = f"💵 {precio}"
                precio_fg = Colors.SURFACE
                precio_color = Colors.TEXT_SECONDARY
            
            precio_label = ctk.CTkLabel(
                periodo_frame,
                text=precio_texto,
                font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
                text_color=precio_color,
                anchor='w'
            )
            precio_label.pack(fill='x', padx=Spacing.SM, pady=(2, Spacing.SM))
    
    def _on_precio_changed(self, *args):
        """Callback cuando cambia el precio."""
        # Implementar lógica de actualización si es necesario
        pass
```

**Estimación:** 60 minutos

**Total Fase 2:** ~3 horas

---

## FASE 3: Vistas Principales

### 3.1 `UI/views/ctk_vista_principal.py` (NUEVO)
```python
"""Vista principal con layout 55/45 - versión CustomTkinter."""

import customtkinter as ctk
from UI.styles import Colors, Spacing
from UI.components import (
    CTkCard,
    CTkLabeledComboBox,
    CTkDateInput,
    CTkPrecioPanel
)

class CTkVistaPrincipal(ctk.CTkFrame):
    """Vista principal de la aplicación."""
    
    def __init__(self, parent, state, event_bus, **kwargs):
        self.state = state
        self.event_bus = event_bus
        
        super().__init__(parent, fg_color=Colors.BACKGROUND, **kwargs)
        self._setup_ui()
    
    def _setup_ui(self):
        # Configurar grid con proporción 55/45
        self.grid_columnconfigure(0, weight=55, minsize=400)
        self.grid_columnconfigure(1, weight=45, minsize=350)
        self.grid_rowconfigure(0, weight=1)
        
        # Panel izquierdo (formulario)
        self.panel_izquierdo = ctk.CTkFrame(
            self,
            fg_color=Colors.SURFACE,
            corner_radius=0
        )
        self.panel_izquierdo.grid(row=0, column=0, sticky='nsew')
        
        # Panel derecho (info)
        self.panel_derecho = ctk.CTkFrame(
            self,
            fg_color=Colors.BACKGROUND,
            corner_radius=0
        )
        self.panel_derecho.grid(row=0, column=1, sticky='nsew')
        
        self._crear_panel_izquierdo()
        self._crear_panel_derecho()
    
    def _crear_panel_izquierdo(self):
        # Contenedor con padding
        container = ctk.CTkFrame(
            self.panel_izquierdo,
            fg_color="transparent"
        )
        container.pack(fill='both', expand=True, padx=Spacing.XL, pady=Spacing.XL)
        
        # Card: Selección de Reserva
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
            textvariable=self.state.hotel
        )
        self.hotel_combo.pack(fill='x', pady=(0, Spacing.FORM_GAP))
        
        # Edificio (condicional)
        self.edificio_combo = CTkLabeledComboBox(
            card_reserva.content_frame,
            label="Edificio",
            icon="🏢",
            textvariable=self.state.edificio,
            state="disabled"
        )
        # No lo empaquetamos por defecto
        
        # Habitación
        self.habitacion_combo = CTkLabeledComboBox(
            card_reserva.content_frame,
            label="Habitación",
            icon="🛏️",
            textvariable=self.state.habitacion,
            state="disabled"
        )
        self.habitacion_combo.pack(fill='x')
        
        # Card: Fechas y Huéspedes
        card_fechas = CTkCard(
            container,
            title="FECHAS Y HUÉSPEDES",
            icon="📅"
        )
        card_fechas.pack(fill='x', pady=(0, Spacing.LG))
        
        # Fecha entrada
        self.fecha_entrada = CTkDateInput(
            card_fechas.content_frame,
            label="Fecha de entrada",
            icon="📅",
            day_var=self.state.fecha_dia_entrada,
            month_var=self.state.fecha_mes_entrada,
            year_var=self.state.fecha_ano_entrada
        )
        self.fecha_entrada.pack(fill='x', pady=(0, Spacing.FORM_GAP))
        
        # Fecha salida
        self.fecha_salida = CTkDateInput(
            card_fechas.content_frame,
            label="Fecha de salida",
            icon="📅",
            day_var=self.state.fecha_dia_salida,
            month_var=self.state.fecha_mes_salida,
            year_var=self.state.fecha_ano_salida
        )
        self.fecha_salida.pack(fill='x', pady=(0, Spacing.FORM_GAP))
        
        # Huéspedes
        huespedes_frame = ctk.CTkFrame(
            card_fechas.content_frame,
            fg_color="transparent"
        )
        huespedes_frame.pack(fill='x')
        
        # Label principal
        ctk.CTkLabel(
            huespedes_frame,
            text="👥 Huéspedes",
            font=(Typography.FAMILY, Typography.BODY, Typography.MEDIUM),
            text_color=Colors.TEXT_PRIMARY,
            anchor='w'
        ).pack(fill='x', pady=(0, Spacing.SM))
        
        # Frame de inputs
        inputs_huesp = ctk.CTkFrame(huespedes_frame, fg_color="transparent")
        inputs_huesp.pack(fill='x')
        inputs_huesp.grid_columnconfigure(0, weight=1)
        inputs_huesp.grid_columnconfigure(1, weight=1)
        
        # Adultos
        adultos_frame = ctk.CTkFrame(inputs_huesp, fg_color="transparent")
        adultos_frame.grid(row=0, column=0, sticky='ew', padx=(0, Spacing.SM))
        
        ctk.CTkLabel(
            adultos_frame,
            text="Adultos",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY
        ).pack(anchor='w', pady=(0, Spacing.XS))
        
        ctk.CTkEntry(
            adultos_frame,
            textvariable=self.state.adultos,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD
        ).pack(fill='x')
        
        # Niños
        ninos_frame = ctk.CTkFrame(inputs_huesp, fg_color="transparent")
        ninos_frame.grid(row=0, column=1, sticky='ew')
        
        ctk.CTkLabel(
            ninos_frame,
            text="Niños",
            font=(Typography.FAMILY, Typography.SMALL),
            text_color=Colors.TEXT_SECONDARY
        ).pack(anchor='w', pady=(0, Spacing.XS))
        
        ctk.CTkEntry(
            ninos_frame,
            textvariable=self.state.ninos,
            font=(Typography.FAMILY, Typography.BODY),
            fg_color=Colors.SURFACE,
            border_color=Colors.BORDER,
            corner_radius=Spacing.RADIUS_MD
        ).pack(fill='x')
        
        # Botón Ejecutar
        self.btn_ejecutar = ctk.CTkButton(
            container,
            text="▶ Ejecutar Comparación",
            font=(Typography.FAMILY, Typography.BODY, Typography.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.HEADER_TEXT,
            corner_radius=Spacing.RADIUS_MD,
            height=48,
            command=self._on_ejecutar_clicked
        )
        self.btn_ejecutar.pack(fill='x')
    
    def _crear_panel_derecho(self):
        # Contenedor con padding
        container = ctk.CTkFrame(
            self.panel_derecho,
            fg_color="transparent"
        )
        container.pack(fill='both', expand=True, padx=Spacing.XL, pady=Spacing.XL)
        
        # Panel de precio
        self.precio_panel = CTkPrecioPanel(
            container,
            textvariable=self.state.precio
        )
        self.precio_panel.pack(fill='x', pady=(0, Spacing.LG))
        
        # Panel de periodos (TODO: implementar)
        # self.periodos_panel = CTkPeriodosPanel(container)
        # self.periodos_panel.pack(fill='both', expand=True)
    
    def _on_ejecutar_clicked(self):
        """Handler del botón ejecutar."""
        self.event_bus.emit('ejecutar_comparacion')
```

**Estimación:** 2 horas

**Total Fase 3:** ~4 horas (incluyendo otras vistas)

---

## FASE 4: Integración Final

### 4.1 Modificar `UI/interfaz.py`

Agregar modo de compatibilidad para elegir entre tkinter y CustomTkinter:

```python
# Configuración global
USE_CUSTOMTKINTER = True  # Toggle para activar nueva UI

if USE_CUSTOMTKINTER:
    import customtkinter as ctk
    from UI.views.ctk_vista_principal import CTkVistaPrincipal
else:
    import tkinter as tk
    # Código legacy...
```

**Estimación:** 1 hora

---

## FASE 5: Testing y Refinamiento

### Checklist de Testing

- [ ] Todos los componentes renderizan correctamente
- [ ] Colores coinciden con mockups
- [ ] Espaciados son consistentes
- [ ] Hover effects funcionan
- [ ] Botones responden a clicks
- [ ] Validaciones de formulario funcionan
- [ ] EventBus y AppState siguen funcionando
- [ ] Comparación ejecuta correctamente
- [ ] Vista de resultados se muestra bien
- [ ] Vista de email funciona

**Estimación:** 3 horas

---

## 📊 RESUMEN DE TIEMPOS

| Fase | Descripción | Tiempo Estimado |
|------|-------------|-----------------|
| 0 | Preparación | 30 min |
| 1 | Sistema de estilos | 40 min |
| 2 | Componentes base | 3 horas |
| 3 | Vistas principales | 4 horas |
| 4 | Integración | 1 hora |
| 5 | Testing | 3 horas |
| **TOTAL** | **~12 horas** | **1.5 días de trabajo** |

---

## 🎯 ORDEN SUGERIDO DE IMPLEMENTACIÓN

### Día 1 (Sesión 1 - 4 horas)
1. ✅ Instalar CustomTkinter
2. ✅ Crear sistema de estilos (Fase 1)
3. ✅ Componente base y Card (Fase 2.1, 2.2)
4. ✅ LabeledComboBox (Fase 2.3)

### Día 1 (Sesión 2 - 4 horas)
5. ✅ DateInput (Fase 2.4)
6. ✅ PrecioPanel (Fase 2.5)
7. ✅ Inicio de VistaPrincipal (Fase 3)

### Día 2 (Sesión 1 - 4 horas)
8. ✅ Completar VistaPrincipal
9. ✅ Integración básica (Fase 4)
10. ✅ Testing inicial (Fase 5)

---

## 🚨 PUNTOS CRÍTICOS

### ⚠️ Cosas a NO Romper
- `EventBus` - Mantener intacto
- `AppState` - Mantener intacto
- `Controladores` - Mantener intactos
- Lógica de negocio en `Core/` - Mantener intacta

### ✅ Qué Estamos Cambiando
- **Solo la capa visual** (archivos en `UI/`)
- De `tkinter` → `customtkinter`
- De componentes monolíticos → componentes modulares

---

## 📝 NOTAS FINALES

- **Branch de trabajo:** `feature/customtkinter-migration`
- **Testing continuo:** Probar después de cada componente
- **Commits frecuentes:** Commit después de cada fase
- **Rollback disponible:** Mantener código legacy comentado

---

**Última actualización:** 25 de Febrero, 2026
**Estado:** ✅ Plan Aprobado - Listo para implementar
