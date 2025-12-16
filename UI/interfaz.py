import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime
import threading
import subprocess
import sys

from Models.hotelWeb import *
from Core.controller import *

# Importar infraestructura de estado y estilos
from UI.state.event_bus import EventBus
from UI.state.app_state import AppState
from UI.styles.fonts import FontManager

# Importar componentes
from UI.components import DateInputWidget, LabeledComboBox, PeriodosPanel, PrecioPanel, EntradaEtiquetada

# Importar vistas
from UI.views import VistaResultados

# Importar controladores
from UI.controllers import ControladorHotel, ControladorValidacion, ControladorComparacion, ControladorPrecios

# Importar validadores
from UI.utils.validadores_fecha import (
    validar_dia, validar_mes, validar_ano,
    parsear_fecha_dd_mm_aaaa, validar_fecha_mayor_o_igual, validar_fecha_mayor
)


class InterfazApp:

    def validar_dia(self, valor):
        """DEPRECATED: Usar validadores_fecha.validar_dia() en su lugar."""
        return validar_dia(valor)

    def validar_mes(self, valor):
        """DEPRECATED: Usar validadores_fecha.validar_mes() en su lugar."""
        return validar_mes(valor)

    def validar_ano(self, valor):
        """DEPRECATED: Usar validadores_fecha.validar_ano() en su lugar."""
        return validar_ano(valor)
    
    def validar_fecha(self):
        """DEPRECATED: Usar ControladorValidacion.validar_fecha() en su lugar.

        Valida que las fechas completas sean correctas y existan en el calendario.
        """
        campos = [
            ("entrada", self.fecha_entrada_completa.get()),
            ("salida", self.fecha_salida_completa.get())
        ]
        fecha_actual = datetime.now()

        for nombre, fecha_str in campos:
            fecha_dt = parsear_fecha_dd_mm_aaaa(fecha_str)

            if fecha_dt is None:
                messagebox.showerror("Error", f"La fecha de {nombre} debe tener el formato DD-MM-AAAA y ser válida.")
                return False

            if not validar_fecha_mayor_o_igual(fecha_str, fecha_actual):
                messagebox.showerror("Error", f"La fecha de {nombre} debe ser mayor o igual al actual.")
                return False

        return True

    def validar_orden_fechas(self):
        """DEPRECATED: Usar ControladorValidacion.validar_orden_fechas() en su lugar.

        Valida que la fecha de salida sea posterior a la fecha de entrada.
        """
        fecha_entrada_str = self.fecha_entrada_completa.get()
        fecha_salida_str = self.fecha_salida_completa.get()

        # Validar que ambas fechas tengan formato válido
        if parsear_fecha_dd_mm_aaaa(fecha_entrada_str) is None:
            return False
        if parsear_fecha_dd_mm_aaaa(fecha_salida_str) is None:
            return False

        # Validar que fecha salida > fecha entrada
        if not validar_fecha_mayor(fecha_salida_str, fecha_entrada_str):
            messagebox.showerror("Error", "La fecha de salida debe ser posterior a la fecha de entrada.")
            return False

        return True

    def actualizar_fecha_entrada(self, *args):
            # Concatenamos los valores solo si los campos tienen valores válidos
            dia = self.fecha_dia_entrada.get().zfill(2)  # rellenar con 0 si es necesario
            mes = self.fecha_mes_entrada.get().zfill(2)
            ano = self.fecha_ano_entrada.get()
            if dia and mes and ano:
                self.fecha_entrada_completa.set(f"{dia}-{mes}-{ano}")
            else:
                self.fecha_entrada_completa.set("")

    def actualizar_fecha_salida(self, *args):
            # Concatenamos los valores solo si los campos tienen valores válidos
            dia = self.fecha_dia_salida.get().zfill(2)  # rellenar con 0 si es necesario
            mes = self.fecha_mes_salida.get().zfill(2)
            ano = self.fecha_ano_salida.get()
            if dia and mes and ano:
                self.fecha_salida_completa.set(f"{dia}-{mes}-{ano}")
            else:
                self.fecha_salida_completa.set("")

    def __init__(self, root):

        self.root = root
        self.root.title("Comparador de precios ")
        self.root.geometry("1200x700")  # Ancho aumentado para mostrar paneles completos

        # ===== FASE 1: Infraestructura Base =====
        # Sistema de eventos para comunicación desacoplada
        self.event_bus = EventBus()
        # self.event_bus.enable_debug()  # Descomentar para debugging

        # Estado centralizado de la aplicación
        self.state = AppState(self.event_bus)

        # Gestor de fuentes centralizado
        self.fonts = FontManager(self.root)

        # ===== Compatibilidad con código existente =====
        # Variables que apuntan al estado centralizado
        self.seleccion_hotel = self.state.hotel
        self.seleccion_edificio = self.state.edificio
        self.seleccion_habitacion_excel = self.state.habitacion

        self.fecha_dia_entrada = self.state.fecha_dia_entrada
        self.fecha_mes_entrada = self.state.fecha_mes_entrada
        self.fecha_ano_entrada = self.state.fecha_ano_entrada
        self.fecha_entrada_completa = self.state.fecha_entrada_completa

        self.fecha_dia_salida = self.state.fecha_dia_salida
        self.fecha_mes_salida = self.state.fecha_mes_salida
        self.fecha_ano_salida = self.state.fecha_ano_salida
        self.fecha_salida_completa = self.state.fecha_salida_completa

        self.adultos = self.state.adultos
        self.niños = self.state.ninos
        self.precio_var = self.state.precio
        self.periodos_var = self.state.periodos_var

        # Fuentes que apuntan al FontManager
        self.fuente_normal = self.fonts.normal
        self.fuente_negrita = self.fonts.negrita
        self.fuente_grande_negrita = self.fonts.grande_negrita
        self.fuente_resultado = self.fonts.resultado
        self.fuente_periodos_titulo = self.fonts.periodos_titulo
        self.fuente_periodos_contenido = self.fonts.periodos_contenido
        self.fuente_precio = self.fonts.precio
        self.fuente_combobox = self.fonts.combobox
        self.fuente_combo = self.fonts.combo
        self.fuente_boton = self.fonts.boton

        # Configurar estilo para combobox con letra más grande
        style = ttk.Style()
        style.configure('Custom.TCombobox', font=self.fuente_combo)
        self.root.option_add('*TCombobox*Listbox*Font', self.fuente_combobox)


        self.vcmd_dia = (self.root.register(self.validar_dia), "%P")
        self.vcmd_mes = (self.root.register(self.validar_mes), "%P")
        self.vcmd_ano = (self.root.register(self.validar_ano), "%P")

        # ===== FASE 4: Inicializar Controladores =====
        self.controlador_validacion = ControladorValidacion(self.state)
        self.controlador_hotel = ControladorHotel(self.state, self.event_bus)
        self.controlador_comparacion = ControladorComparacion(
            self.state,
            self.event_bus,
            self.controlador_validacion
        )
        self.controlador_precios = ControladorPrecios(self.state, self.event_bus)

        # Suscribir a eventos de comparación
        self.event_bus.on('comparison_started', self._on_comparison_started)
        self.event_bus.on('comparison_completed', self._on_comparison_completed)
        self.event_bus.on('comparison_error', self._on_comparison_error)
        self.event_bus.on('precios_actualizados', self._on_precios_actualizados)

        # FRAME principal unificado - con estilo mejorado
        self.principal_container = tk.Frame(self.root, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        self.principal_container.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=4, pady=4)

        self.principal_frame = tk.Frame(self.principal_container, bg='#F5F5F5')
        self.principal_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.principal_frame.columnconfigure(0, weight=1)
        self.principal_container.columnconfigure(0, weight=1)
        self.principal_container.rowconfigure(0, weight=1)

        # Hotel
        tk.Label(self.principal_frame, text="Selección hotel:", font=self.fuente_negrita, bg='#F5F5F5').grid(row=0, column=0, sticky='w', pady=(0, 4))
        self.hotel_cb = ttk.Combobox(self.principal_frame, textvariable=self.seleccion_hotel, state="readonly", style='Custom.TCombobox', font=self.fuente_combobox)
        self.hotel_cb.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.hotel_cb.bind("<<ComboboxSelected>>", self.on_hotel_cambiado)

        # Los demás campos se agregan dinámicamente
        self.fila_dinamica_inicio = 2
        self.crear_campos_estaticos()
        
        # ===== FASE 2: Componentes Panel Derecho =====
        # FRAME precio de la habitación (col 2)
        self.precio_frame = ttk.Frame(self.root)
        self.precio_frame.grid(row=0, column=2, rowspan=3, sticky='nsew', padx=4, pady=2)

        # Componente PrecioPanel
        self.precio_panel = PrecioPanel(
            self.precio_frame,
            textvariable=self.state.precio,
            fonts=self.fonts
        )
        self.precio_panel.grid(row=0, column=0, sticky='ew')

        # Componente PeriodosPanel
        self.periodos_panel = PeriodosPanel(self.precio_frame, fonts=self.fonts)
        self.periodos_panel.grid(row=1, column=0, sticky='nsew')

        # Configurar expansión del frame
        self.precio_frame.rowconfigure(1, weight=1)

        # ===== Mantener compatibilidad con código existente =====
        self.periodos_text = self.periodos_panel._text  # Para código que accede directamente

        # Tags ya configurados en PeriodosPanel, no es necesario reconfigurar
        
        self.cargar_hoteles_excel()

        # Configurar columnas con peso y tamaño mínimo para responsividad
        self.root.grid_columnconfigure(0, weight=3, minsize=400)  # Panel izquierdo - más peso y ancho mínimo
        self.root.grid_columnconfigure(1, weight=0)  # Columna vacía sin peso
        self.root.grid_columnconfigure(2, weight=1, minsize=350)  # Panel derecho - ancho mínimo para mostrar contenido

        # Configurar filas
        self.root.grid_rowconfigure(0, weight=1)
    
    def mostrar_email_btn(self):
        self.boton_ejecutar = ttk.Button(self.precio_frame, text="Envio de email", command=self.crear_pantalla_mail)
        self.boton_ejecutar.grid(row=2, column=0, sticky="ew")
        
    
    def crear_campos_estaticos(self, incluir_edificio=False):

        # Limpiar widgets dinámicos anteriores si existen
        if hasattr(self, 'widgets_dinamicos'):
            for widget in self.widgets_dinamicos:
                widget.destroy()
            self.widgets_dinamicos = []
        else:
            self.widgets_dinamicos = []

        # Usar el frame principal ya creado
        i = self.fila_dinamica_inicio  # fila relativa dentro del principal_frame

        # Campo opcional: Edificio
        if incluir_edificio:
            self.label_edificio = tk.Label(self.principal_frame, text="Edificio:", font=self.fuente_negrita, bg='#F5F5F5')
            self.var_edificio_cb = ttk.Combobox(self.principal_frame, textvariable=self.seleccion_edificio, state="readonly", style='Custom.TCombobox', font=self.fuente_combobox)
            self.var_edificio_cb.bind("<<ComboboxSelected>>", self.on_edificio_cambiado)
            self.label_edificio.grid(row=i, column=0, sticky='w', pady=(0, 4))
            self.widgets_dinamicos.extend([self.label_edificio, self.var_edificio_cb])
            i += 1
            self.var_edificio_cb.grid(row=i, column=0, sticky='ew', pady=(0, 10))
            i += 1

        # Selección habitación Excel
        self.label_habit_excel = tk.Label(self.principal_frame, text="Selección habitación Excel:", font=self.fuente_negrita, bg='#F5F5F5')
        self.habit_excel_cb = ttk.Combobox(self.principal_frame, textvariable=self.seleccion_habitacion_excel, state="readonly", style='Custom.TCombobox', font=self.fuente_combobox)
        self.habit_excel_cb.bind("<<ComboboxSelected>>", self.on_habitacion_excel_cambiada)
        self.label_habit_excel.grid(row=i, column=0, sticky='w', pady=(0, 4))
        self.widgets_dinamicos.extend([self.label_habit_excel, self.habit_excel_cb])
        i += 1
        self.habit_excel_cb.grid(row=i, column=0, sticky='ew', pady=(0, 10))
        i += 1

        self.label_fecha_entrada = tk.Label(self.principal_frame, text="Fecha de entrada:", font=self.fuente_normal, bg='#F5F5F5')
        self.label_fecha_entrada.grid(row=i, column=0, sticky='w', pady=(4, 4))
        self.widgets_dinamicos.append(self.label_fecha_entrada)

        #Fecha entrada
        self.fecha_dia_entrada.trace_add("write", self.actualizar_fecha_entrada)
        self.fecha_mes_entrada.trace_add("write", self.actualizar_fecha_entrada)
        self.fecha_ano_entrada.trace_add("write", self.actualizar_fecha_entrada)

        # Frame con 2 columnas: label a la izquierda y campos a la derecha
        fecha_entrada_container = tk.Frame(self.principal_frame, bg='#F5F5F5')
        fecha_entrada_container.grid(row=i, column=0, sticky='ew', pady=(0, 8))
        self.widgets_dinamicos.append(fecha_entrada_container)

        tk.Label(fecha_entrada_container, text="Fecha de inicio:", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=0, sticky='w', padx=(0, 8))

        self.fechas_entrada_frame = tk.Frame(fecha_entrada_container, bg='#F5F5F5')
        self.fechas_entrada_frame.grid(row=0, column=1, sticky="w")

        tk.Label(self.fechas_entrada_frame, text="DD", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=0, padx=(0,2))
        self.entry_dia_entrada = ttk.Entry(self.fechas_entrada_frame, width=3, textvariable=self.fecha_dia_entrada, validatecommand=self.vcmd_dia, validate='key')
        self.entry_dia_entrada.grid(row=0, column=1, padx=2, pady=2)

        tk.Label(self.fechas_entrada_frame, text="-", bg='#F5F5F5').grid(row=0, column=2, padx=2)

        tk.Label(self.fechas_entrada_frame, text="MM", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=3, padx=2)
        self.entry_mes_entrada = ttk.Entry(self.fechas_entrada_frame, width=3, textvariable=self.fecha_mes_entrada, validatecommand=self.vcmd_mes, validate='key')
        self.entry_mes_entrada.grid(row=0, column=4, padx=2)

        tk.Label(self.fechas_entrada_frame, text="-", bg='#F5F5F5').grid(row=0, column=5, padx=2)

        tk.Label(self.fechas_entrada_frame, text="AAAA", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=6, padx=2)
        self.entry_ano_entrada = ttk.Entry(self.fechas_entrada_frame, width=5, textvariable=self.fecha_ano_entrada, validatecommand=self.vcmd_ano, validate='key')
        self.entry_ano_entrada.grid(row=0, column=7, padx=2)

        # Fecha entrada VIEJA unificado todo en un campo
        # self.label_fecha_entrada = ttk.Label(self.principal_frame, text="Fecha de entrada (DD-MM-AAAA):")
        # self.entry_fecha_entrada = ttk.Entry(self.principal_frame, textvariable=self.fecha_entrada, validate='key', validatecommand=self.vcmd)
        # self.label_fecha_entrada.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        # self.entry_fecha_entrada.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        self.label_fecha_salida = tk.Label(self.principal_frame, text="Fecha de salida:", font=self.fuente_normal, bg='#F5F5F5')
        self.label_fecha_salida.grid(row=i, column=0, sticky='w', pady=(0, 4))
        self.widgets_dinamicos.append(self.label_fecha_salida)

        self.fecha_dia_salida.trace_add("write", self.actualizar_fecha_salida)
        self.fecha_mes_salida.trace_add("write", self.actualizar_fecha_salida)
        self.fecha_ano_salida.trace_add("write", self.actualizar_fecha_salida)

        # Frame con 2 columnas: label a la izquierda y campos a la derecha
        fecha_salida_container = tk.Frame(self.principal_frame, bg='#F5F5F5')
        fecha_salida_container.grid(row=i, column=0, sticky='ew', pady=(0, 8))
        self.widgets_dinamicos.append(fecha_salida_container)

        tk.Label(fecha_salida_container, text="Fecha de salida:", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=0, sticky='w', padx=(0, 8))

        #Frame de fechas
        self.fechas_salida_frame = tk.Frame(fecha_salida_container, bg='#F5F5F5')
        self.fechas_salida_frame.grid(row=0, column=1, sticky="w")

        tk.Label(self.fechas_salida_frame, text="DD", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=0, padx=(0,2))
        self.entry_dia_salida = ttk.Entry(self.fechas_salida_frame, width=3, textvariable=self.fecha_dia_salida, validatecommand=self.vcmd_dia, validate='key')
        self.entry_dia_salida.grid(row=0, column=1, padx=2, pady=2)

        tk.Label(self.fechas_salida_frame, text="-", bg='#F5F5F5').grid(row=0, column=2, padx=2)

        tk.Label(self.fechas_salida_frame, text="MM", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=3, padx=2)
        self.entry_mes_salida = ttk.Entry(self.fechas_salida_frame, width=3, textvariable=self.fecha_mes_salida, validatecommand=self.vcmd_mes, validate='key')
        self.entry_mes_salida.grid(row=0, column=4, padx=2)

        tk.Label(self.fechas_salida_frame, text="-", bg='#F5F5F5').grid(row=0, column=5, padx=2)

        tk.Label(self.fechas_salida_frame, text="AAAA", bg='#F5F5F5', font=self.fuente_normal).grid(row=0, column=6, padx=2)
        self.entry_ano_salida = ttk.Entry(self.fechas_salida_frame, width=5, textvariable=self.fecha_ano_salida, validatecommand=self.vcmd_ano, validate='key')
        self.entry_ano_salida.grid(row=0, column=7, padx=2)

        # Fecha salida
        # self.label_fecha_salida = ttk.Label(self.principal_frame, text="Fecha de salida (DD-MM-AAAA):")
        # self.entry_fecha_salida = ttk.Entry(self.principal_frame, textvariable=self.fecha_salida, validate='key', validatecommand=self.vcmd)
        # self.label_fecha_salida.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        # self.entry_fecha_salida.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Adultos
        self.label_adultos = tk.Label(self.principal_frame, text="Cantidad de adultos:", font=self.fuente_normal, bg='#F5F5F5')
        self.label_adultos.grid(row=i, column=0, sticky='w', pady=(4, 4))
        self.widgets_dinamicos.append(self.label_adultos)
        i += 1
        self.entry_adultos = ttk.Entry(self.principal_frame, textvariable=self.adultos, font=self.fuente_normal, width=5)
        self.entry_adultos.grid(row=i, column=0, sticky='w', pady=(0, 8))
        self.widgets_dinamicos.append(self.entry_adultos)
        i += 1

        # Niños
        self.label_niños = tk.Label(self.principal_frame, text="Cantidad de niños:", font=self.fuente_normal, bg='#F5F5F5')
        self.label_niños.grid(row=i, column=0, sticky='w', pady=(0, 4))
        self.widgets_dinamicos.append(self.label_niños)
        i += 1
        self.entry_niños = ttk.Entry(self.principal_frame, textvariable=self.niños, font=self.fuente_normal, width=5)
        self.entry_niños.grid(row=i, column=0, sticky='w', pady=(0, 8))
        self.entry_niños.bind("<Return>", lambda event: self.ejecutar_comparacion_wrapper())
        self.widgets_dinamicos.append(self.entry_niños)
        i += 1

        # Botón ejecutar comparacion
        style = ttk.Style()
        style.configure('Boton.TButton', font=self.fuente_boton)
        self.boton_ejecutar = ttk.Button(self.principal_frame, text="Ejecutar comparación", command=self.ejecutar_comparacion_wrapper, style='Boton.TButton')
        self.boton_ejecutar.grid(row=i, column=0, sticky='ew', pady=(10, 10))
        self.widgets_dinamicos.append(self.boton_ejecutar)
        i += 1

        # ===== FASE 3: Componente VistaResultados =====
        self.vista_resultados = VistaResultados(self.principal_frame, fonts=self.fonts, bg='#F5F5F5')
        self.vista_resultados.grid(row=i, column=0, sticky='nsew', pady=(0, 0))
        self.widgets_dinamicos.append(self.vista_resultados)

        # Mantener compatibilidad con código existente
        self.resultado = self.vista_resultados.obtener_widget_text()



        # self.principal_frame.rowconfigure(i, weight=1)
    def crear_pantalla_mail(self):
        self.geometria_anterior = self.root.geometry()

        self.principal_container.grid_forget()
        self.precio_frame.grid_forget()
        
        self.mail_frame = ttk.Frame(self.root)
        self.mail_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.mail_frame.columnconfigure(1, weight=2, uniform='col')
        self.root.geometry(self.geometria_anterior)

        lbl_email = ttk.Label(self.mail_frame, text="Contenido del Email:")
        lbl_email.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    
        self.email_textbox = tk.Text(self.mail_frame, wrap="word", height=15, width=50, font= self.fuente_resultado)
        self.email_textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        texto_predeterminado = generar_texto_email(
            self.seleccion_hotel.get(),
            self.seleccion_habitacion_excel.get(),
            self.precio_var.get(),
            self.habitacion_web.combos[0].precio
        )
        self.email_textbox.insert(tk.END, texto_predeterminado)

        enviar_btn = ttk.Button(self.mail_frame, text="Enviar Email", command=self.enviar_email)
        enviar_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def enviar_email(self):
        remitente = "gerlucero1997@gmail.com"
        destinatario = "gerlucero1977@gmail.com"
        texto_final = self.email_textbox.get("1.0", tk.END).strip()

        if not texto_final:
            messagebox.showerror("Error", "El contenido del email no puede estar vacío.")
            return

        enviar_email_discrepancia(
            hotel=self.seleccion_hotel.get(),
            habitacion_excel=self.seleccion_habitacion_excel.get(),
            precio_excel=self.precio_var.get(),
            precio_web=self.habitacion_web.combos[0].precio,
            remitente=remitente,
            destinatario=destinatario,
            texto_override=texto_final 
        )
        messagebox.showinfo("Éxito", "El correo se envió correctamente.")
        
    def cargar_hoteles_excel(self):
        self.hoteles_excel = dar_hoteles_excel()

        # IMPORTANTE: También guardar en AppState para que ControladorHotel pueda accederlos
        self.state.hoteles_excel = self.hoteles_excel

        hoteles = [hoteles_excel.nombre for hoteles_excel in self.hoteles_excel]
        for i in range(len(hoteles)):
            hoteles[i]= hoteles[i].replace("(A)","").strip()
        self.hotel_cb['values'] = hoteles
        if self.hoteles_excel:
            self.seleccion_hotel.set(hoteles[0])
            self.on_hotel_cambiado(None)
        else:
            self.seleccion_hotel.set("")
    
    def obtener_grupo_periodo_edificio(self, hotel_excel, tipo):
        """Obtiene el nombre del grupo de periodo para un edificio basado en sus habitaciones"""
        if not tipo.habitaciones:
            return None

        # Tomar los periodo_ids de la primera habitación del edificio
        primera_habitacion = tipo.habitaciones[0]
        if not primera_habitacion.periodo_ids:
            return None

        # Buscar el grupo al que pertenece el primer periodo
        primer_periodo_id = next(iter(primera_habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None

    def obtener_grupo_periodo_habitacion(self, hotel_excel, habitacion):
        """Obtiene el nombre del grupo de periodo para una habitación"""
        if not habitacion.periodo_ids:
            return None

        # Buscar el grupo al que pertenece el primer periodo
        primer_periodo_id = next(iter(habitacion.periodo_ids))
        for grupo in hotel_excel.periodos_group:
            for periodo in grupo.periodos:
                if periodo.id == primer_periodo_id:
                    return grupo.nombre

        return None

    def cargar_edificios_excel(self, hotel):
        """NUEVO: Usa el ControladorHotel para cargar edificios sin sufijos"""
        # Extraer nombre del hotel sin "(a)" y capitalizar
        hotel_nombre = hotel.replace(" (a)", "").replace(" (A)", "").strip()
        # Capitalizar primera letra de cada palabra para que coincida con el Excel
        hotel_nombre = ' '.join(word.capitalize() for word in hotel_nombre.split())

        # Usar el controlador para cargar edificios
        edificios = self.controlador_hotel.cargar_edificios(hotel_nombre)

        self.var_edificio_cb['values'] = edificios
        self.seleccion_edificio.set("")

    def cargar_habitaciones_excel(self, hotel, tipo=None):
        """NUEVO: Usa el ControladorHotel para cargar habitaciones unificadas"""
        # Extraer nombre del hotel sin "(a)" y capitalizar
        hotel_nombre = hotel.replace(" (a)", "").replace(" (A)", "").strip()
        # Capitalizar primera letra de cada palabra para que coincida con el Excel
        hotel_nombre = ' '.join(word.capitalize() for word in hotel_nombre.split())

        # Usar el controlador para cargar habitaciones unificadas
        nombres_habitaciones = self.controlador_hotel.cargar_habitaciones(hotel_nombre, tipo)

        # Actualizar combobox con nombres únicos (sin duplicados)
        self.habit_excel_cb['values'] = nombres_habitaciones

        # Limpiar selección y periodos
        self.seleccion_habitacion_excel.set("")
        self.limpiar_periodos()

    def on_hotel_cambiado(self, event):
        hotel = self.seleccion_hotel.get().lower()
        hotel = hotel + " (a)"
        print(f"Hotel cambiado a: {hotel}")

        # Limpiar periodos al cambiar de hotel
        self.limpiar_periodos()

        hotel_encontrado = False
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                hotel_encontrado = True
                if hotel_excel.tipos:
                    self.crear_campos_estaticos(incluir_edificio=True)
                    self.cargar_edificios_excel(hotel)
                else:
                    self.crear_campos_estaticos(incluir_edificio=False)
                    self.cargar_habitaciones_excel(hotel)
                break

        if not hotel_encontrado:
            print("no se encontro el hotel")

    def on_edificio_cambiado(self, event):
        edificio = self.seleccion_edificio.get()
        hotel = self.seleccion_hotel.get().lower()
        hotel = hotel + " (a)"

        # Limpiar periodos al cambiar de edificio
        self.limpiar_periodos()

        self.cargar_habitaciones_excel(hotel, edificio)
    
    def on_habitacion_excel_cambiada(self, event):
        seleccionado = self.seleccion_habitacion_excel.get()
        print(f"\n[DEBUG] on_habitacion_excel_cambiada disparado - Seleccionado: '{seleccionado}'")

        try:
            # Usar el índice actual del combobox
            idx = self.habit_excel_cb.current()
            print(f"[DEBUG] Índice del combobox (current): {idx}")

            if idx == -1:
                return

            # NUEVO: Obtener habitación unificada
            habitacion_unificada = self.state.habitaciones_unificadas[idx]
            print(f"[DEBUG] Habitación unificada: {habitacion_unificada.nombre}")
            print(f"[DEBUG] - Variantes: {len(habitacion_unificada.variantes)}")

            # Emitir evento con habitación unificada
            self.event_bus.emit('habitacion_unificada_changed', habitacion_unificada)

            # Ya no mostramos precio aquí - lo maneja ControladorPrecios

            # Actualizar visualización de periodos con TODAS las variantes
            print(f"[DEBUG] Actualizando periodos con {len(habitacion_unificada.variantes)} variante(s)...")
            self.actualizar_periodos_habitacion(habitacion_unificada)
            print(f"[DEBUG] Periodos actualizados correctamente")

        except Exception as e:
            self.limpiar_periodos()
            print(f"[ERROR] Exception - Error inesperado: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    def actualizar_periodos_habitacion(self, habitacion):
        """Actualiza el widget de periodos con la información de la habitación seleccionada.

        Args:
            habitacion: HabitacionUnificada o HabitacionExcel con periodo_ids
        """
        # Obtener el hotel actual
        hotel_nombre = self.seleccion_hotel.get().lower() + " (a)"
        hotel_actual = None
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel_nombre:
                hotel_actual = hotel_excel
                break

        if not hotel_actual:
            self.periodos_panel.limpiar()
            return

        # ===== FASE 2: Usar componente PeriodosPanel =====
        self.periodos_panel.actualizar_periodos(habitacion, hotel_actual)

    def limpiar_periodos(self):
        """Limpia el widget de periodos"""
        # ===== FASE 2: Usar componente PeriodosPanel =====
        self.periodos_panel.limpiar()


    def ejecutar_comparacion_wrapper(self):
        """Wrapper para ejecutar comparación - ahora usa el controlador."""
        # ===== FASE 4: Usar ControladorComparacion =====
        self.controlador_comparacion.ejecutar_comparacion_async()

    def run_async(self):
        """DEPRECATED - Ahora usa controlador"""
        asyncio.run(self.ejecutar_comparacion())
        
    async def ejecutar_comparacion(self):
        try:
        # Validaciones iniciales
            if not self.validar_fecha() or not self.validar_orden_fechas():
                print("no paso validaciones")
                return         

            campos_a_validar = {
                "Fecha de entrada": self.fecha_entrada_completa.get(),
                "Fecha de salida": self.fecha_salida_completa.get(),
                "Número de adultos": self.adultos.get(),
                "Número de niños": self.niños.get(),
                "Habitacion Excel": self.seleccion_habitacion_excel.get(),
                "Precio": self.precio_var.get()
            }
            for nombre_campo, valor_campo in campos_a_validar.items():
                if valor_campo in ("", None,""):
                    messagebox.showerror("Error",f"El campo '{nombre_campo}' no puede estar vacío. Por favor, revísalo.")
                    print(f"El campo '{nombre_campo}' está vacío o es None.")
                    return # Detiene la ejecución una vez que encuentra el primer error
                if nombre_campo in ["Número de adultos"]:
                    if valor_campo <= 0:
                        messagebox.showerror("Error",f"El campo '{nombre_campo}' debe ser un número entero no negativo.")
                        return          

            self.resultado.insert(tk.END, f"Ejecutando scraping con:\n")
            for nombre, valor in campos_a_validar.items():
                self.resultado.insert(tk.END, f"  - {nombre}: {valor}\n")

            hotel_web = await dar_hotel_web(self.fecha_entrada_completa.get(),self.fecha_salida_completa.get(),self.adultos.get(),self.niños.get())
            if not hotel_web or not hotel_web.habitacion:
                self.resultado.insert(tk.END, "Error: No se pudieron obtener datos del hotel web\n")
                return
        
            precio = normalizar_precio_str(self.precio_var.get())
            coincide = await comparar_habitaciones(self.seleccion_habitacion_excel.get(),precio)
            self.habitacion_web =  dar_habitacion_web()
            mensaje_match = dar_mensaje()
            
            texto_habitacion = imprimir_habitacion_web(self.habitacion_web)
            self.resultado.insert(tk.END, f"Habitacion web ", ("bold",)) 
            self.resultado.insert(tk.END, f"de mayor coincidencia:\n {texto_habitacion}\n") 
            if mensaje_match:
                self.resultado.insert(tk.END, f"{mensaje_match}\n", ("bold",))

            if  coincide: 
                self.resultado.insert(tk.END, "Se encontro diferencia de precio.\n")
                self.mostrar_email_btn()
            else:
                self.resultado.insert(tk.END, "Las habitaciones coinciden en precio y nombre.\n")
        
        except ValueError as ve:
            self.resultado.insert(tk.END, f"Error de validación: ", ("bold",))
            self.resultado.insert(tk.END, f"{str(ve)}\n")
        except Exception as e:
            self.resultado.insert(tk.END, f"Error inesperado: ", ("bold",))
            self.resultado.insert(tk.END, f"{str(e)}\n")

    # ===== FASE 4: Event Handlers de Controladores =====
    def _on_comparison_started(self, data=None):
        """Handler cuando inicia la comparación."""
        self.resultado.delete('1.0', tk.END)
        self.resultado.insert(tk.END, "Iniciando comparación...\n")

    def _on_comparison_completed(self, resultado_data):
        """Handler cuando completa la comparación.

        Args:
            resultado_data (dict): Datos del resultado {mensaje, coincide, habitacion_web}
        """
        self.resultado.delete('1.0', tk.END)
        mensaje = resultado_data['mensaje']
        coincide = resultado_data['coincide']

        # Insertar mensaje
        lineas = mensaje.split('\n')
        for linea in lineas:
            if 'Habitación web' in linea:
                self.resultado.insert(tk.END, linea + '\n', ("bold",))
            elif 'encontró diferencia' in linea or 'coinciden' in linea:
                self.resultado.insert(tk.END, linea + '\n', ("bold",))
            else:
                self.resultado.insert(tk.END, linea + '\n')

        # Mostrar botón email si hay diferencia
        if coincide:
            self.mostrar_email_btn()

    def _on_comparison_error(self, error_msg):
        """Handler cuando hay error en la comparación.

        Args:
            error_msg (str): Mensaje de error
        """
        if "Validación fallida" in error_msg:
            # Las validaciones ya mostraron su propio messagebox
            return

        self.resultado.insert(tk.END, f"Error: ", ("bold",))
        self.resultado.insert(tk.END, f"{error_msg}\n")

    def _on_precios_actualizados(self, data):
        """Handler cuando se actualizan los precios desde ControladorPrecios.

        Args:
            data (dict): Datos del evento con 'tipo' y contenido según el tipo
        """
        tipo = data.get('tipo')

        if tipo == 'sin_fechas':
            self.precio_panel._mostrar_mensaje(data['mensaje'])

        elif tipo == 'sin_periodos':
            self.precio_panel._mostrar_mensaje(data['mensaje'])

        elif tipo == 'precios_calculados':
            precios = data['precios']
            self.precio_panel.mostrar_precios_multiples(precios)


def run_interfaz():
    from pathlib import Path

    # Obtener ruta absoluta del proyecto root
    project_root = Path(__file__).parent.parent

    # TESTEO del extractor de datos
    # try:
    #     # Ejecutar como módulo desde el directorio raíz del proyecto
    #     subprocess.run(
    #         [sys.executable, "-m", "Tests.testExtractor2"],
    #         cwd=str(project_root),
    #         check=True
    #     )
    #     print("\n" + "="*60)
    #     print("testExtractor2.py ejecutado exitosamente")
    #     print("="*60 + "\n")
    # except subprocess.CalledProcessError as e:
    #     print(f"\nError al ejecutar testExtractor2.py: {e}\n")
    # except FileNotFoundError:
    #     print(f"\nNo se encontró Tests/testExtractor2.py, continuando con la interfaz...\n")

    # Iniciar interfaz
    root = tk.Tk()
    app = InterfazApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_interfaz()
        #PARA VER EN DISTINTOS COLORES 
        # for col in range(2):
        #     color = 'lightblue' if col == 0 else 'lightgreen'
        #     ttk.Label(self.campos_frame, text=f'Col {col}', background=color).grid(row=0, column=col, sticky='nsew')