# Mockups - Crawl-Compare

Mockups de diseño para la nueva interfaz del sistema Crawl-Compare.

## 📱 Archivos Disponibles

### 1. `mockup_pantalla_principal.html`
**Estado:** Pantalla inicial vacía (sin hotel seleccionado)
- Formulario de búsqueda vacío
- Panel derecho sin datos
- Botón deshabilitado hasta completar campos

### 2. `mockup_pantalla_principal_v2.html`
**Estado:** Igual que anterior pero **incluye campo "Edificio"**
- Se muestra el campo Edificio entre Hotel y Habitación
- Campo habilitado y visualizable solo si el hotel lo requiere

### 3. `mockup_con_seleccion.html`
**Estado:** Con habitación seleccionada
- Hotel y habitación elegidos
- Panel de precio mostrando tarifa
- Panel de periodos con información detallada
- Botón habilitado

### 4. `mockup_resultados.html`
**Estado:** Resultados de comparación
- Tabla comparativa multi-periodo
- Resumen de coincidencias y discrepancias
- Detalles de habitación web
- Botón para enviar email

### 5. `mockup_email.html`
**Estado:** Pantalla de redacción de email
- Editor de texto con toolbar
- Contenido pre-generado editable
- Vista previa de destinatarios
- Botones de acción (guardar/enviar)

## 🎨 Paleta de Colores

```css
/* Primarios */
Primary Blue:    #2563EB
Primary Hover:   #1D4ED8
Primary Light:   #DBEAFE

/* Semánticos */
Success Green:   #10B981
Success Light:   #D1FAE5

Warning Orange:  #F59E0B
Warning Light:   #FEF3C7

Error Red:       #EF4444
Error Light:     #FEE2E2

/* Neutrales */
Background:      #F8FAFC
Surface:         #FFFFFF
Border:          #E2E8F0

Text Primary:    #1E293B
Text Secondary:  #64748B
Text Disabled:   #94A3B8
```

## 🔤 Tipografía

**Font Family:** Inter (Google Fonts)

**Tamaños:**
- H1 (Títulos): 18px
- H2 (Secciones): 16px
- Body (Texto): 14px
- Small (Labels): 12px
- Precio: 28px (bold)

## 📐 Espaciados

**Border Radius:** 8px (sutilmente redondeado)
**Padding Cards:** 24px
**Gap Elements:** 16-24px
**Panel Split:** 55% / 45%

## 🚀 Cómo Usar

1. Abrir cada archivo `.html` en un navegador web
2. Revisar diseño, colores, espaciados
3. Probar interacciones (hover effects)
4. Dar feedback para ajustes

## 📝 Notas

- Los mockups son HTML estático (no funcionales)
- Representan el look & feel final con CustomTkinter
- Los íconos son emojis (placeholder para íconos reales)
- La tipografía Inter será cargada desde Google Fonts en versión final

## ✅ Estado

**Aprobado:** ✅
**Listo para implementación:** Pendiente

---

Última actualización: 25 de Febrero, 2026
