import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime
import threading
import subprocess
import sys

from Models.hotelWeb import *
from Core.controller import *


class InterfazApp:

    def validar_dia(self, valor):
        if valor == "":
            return True
        if valor.isdigit():
            n = int(valor)
            return 1 <= n <= 31
        return False
       
    def validar_mes(self, valor):
        if valor == "":
            return True 
        if valor.isdigit():
            n = int(valor)
            return 1 <= n <= 12

    def validar_ano(self, valor):
        if valor == "":
            return True
        if valor.isdigit():
            return  1 <= len(valor) <= 4
    
    def validar_fecha(self):
    #Valida que las fechas completas sean correctas y existan en el calendario
        campos = [
            ("entrada", self.fecha_entrada_completa.get()), 
            ("salida", self.fecha_salida_completa.get())
        ]
        for nombre, fecha in campos:
            try:
                fecha_dt = datetime.strptime(fecha, "%d-%m-%Y")
                fecha_actual = datetime.now()
                if fecha_actual > fecha_dt:
                    messagebox.showerror("Error", f"La fecha de {nombre} debe ser mayor o igual al actual.")
                    return False  
            except ValueError:
                messagebox.showerror("Error", f"La fecha de {nombre} debe tener el formato DD-MM-AAAA y ser válida.")
                return False
        return True

    def validar_orden_fechas(self):
        #Valida que la fecha de salida sea posterior a la fecha de entrada
        try:
            fecha_entrada = datetime.strptime(self.fecha_entrada_completa.get(), "%d-%m-%Y")
            fecha_salida = datetime.strptime(self.fecha_salida_completa.get(), "%d-%m-%Y")
        except ValueError:
            return False 
        if fecha_salida <= fecha_entrada:
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
        self.root.geometry("900x700")
        # Campos de entrada
        self.seleccion_hotel = tk.StringVar()
        self.seleccion_edificio = tk.StringVar()
        self.seleccion_habitacion_excel = tk.StringVar()
        
        self.fecha_dia_entrada = tk.StringVar()
        self.fecha_mes_entrada = tk.StringVar()
        self.fecha_ano_entrada = tk.StringVar()
        self.fecha_entrada_completa = tk.StringVar()
        
        self.fecha_dia_salida = tk.StringVar()
        self.fecha_mes_salida = tk.StringVar()
        self.fecha_ano_salida = tk.StringVar()
        self.fecha_salida_completa = tk.StringVar()

        self.adultos = tk.IntVar(value=1)
        self.niños = tk.IntVar()
        self.precio_var = tk.StringVar(value="(ninguna seleccionada)")
        self.periodos_var = tk.StringVar(value="")

        self.fuente_normal = font.Font(family="Helvetica", size=12)
        self.fuente_negrita = font.Font(family="Helvetica", size=12, weight="bold")
        self.fuente_grande_negrita = font.Font(family="Helvetica", size=16, weight="bold")
        self.fuente_resultado = font.Font(family="Helvetica", size=12, weight="normal")
        self.fuente_periodos_titulo = font.Font(family="Helvetica", size=11, weight="bold")
        self.fuente_periodos_contenido = font.Font(family="Helvetica", size=11)
        self.fuente_precio = font.Font(family="Helvetica", size=14, weight="bold")
        self.fuente_combobox = font.Font(family="Helvetica", size=12)
        self.fuente_combo = font.Font(family="Helvetica", size=20)
        self.fuente_boton = font.Font(family="Helvetica", size=13, weight="bold")
        # Configurar estilo para combobox con letra más grande
        style = ttk.Style()
        style.configure('Custom.TCombobox', font=self.fuente_combo)
        self.root.option_add('*TCombobox*Listbox*Font', self.fuente_combobox)


        self.vcmd_dia = (self.root.register(self.validar_dia), "%P")
        self.vcmd_mes = (self.root.register(self.validar_mes), "%P")
        self.vcmd_ano = (self.root.register(self.validar_ano), "%P")

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
        
        # FRAME precio de la habitación (col 2)
        self.precio_frame = ttk.Frame(self.root)
        self.precio_frame.grid(row=0, column=2, rowspan=3, sticky='nsew', padx=4, pady=2)

        ttk.Label(self.precio_frame, text="Precio de la habitación", font=self.fuente_negrita).grid(row=0, column=0, sticky='w', pady=(0,5), padx=(0,10))

        # Frame contenedor del precio con estilo discreto
        precio_container = tk.Frame(self.precio_frame, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        precio_container.grid(row=1, column=0, sticky='ew', pady=(0,15), padx=(0,10))

        self.label_precio = tk.Label(
            precio_container,
            textvariable=self.precio_var,
            font=self.fuente_precio,
            bg='#F5F5F5',
            fg='#2C3E50',
            padx=12,
            pady=8,
            anchor='w'
        )
        self.label_precio.pack(fill='both', expand=True)

        # Sección de periodos
        ttk.Label(self.precio_frame, text="Periodos de la habitación", font=self.fuente_negrita).grid(row=2, column=0, sticky='w', pady=(10,5), padx=(0,10))

        # Frame para el texto de periodos con borde discreto
        periodos_container = tk.Frame(self.precio_frame, relief=tk.SOLID, borderwidth=1, bg='#F5F5F5')
        periodos_container.grid(row=3, column=0, sticky='nsew', pady=(0,10), padx=(0,10))

        self.periodos_text = tk.Text(
            periodos_container,
            height=15,
            width=38,
            wrap="word",
            font=self.fuente_periodos_contenido,
            bg='#FAFAFA',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor='arrow'
        )
        self.periodos_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar para periodos
        periodos_scrollbar = ttk.Scrollbar(periodos_container, orient="vertical", command=self.periodos_text.yview)
        periodos_scrollbar.grid(row=0, column=1, sticky="ns")
        self.periodos_text.configure(yscrollcommand=periodos_scrollbar.set)

        # Configurar el Text como readonly
        self.periodos_text.config(state='disabled')

        # Configurar tags para el formato discreto
        self.periodos_text.tag_configure("advertencia", foreground="#C0392B", font=self.fuente_negrita)
        self.periodos_text.tag_configure("grupo", foreground="#34495E", font=self.fuente_periodos_titulo, spacing1=6, spacing3=3)
        self.periodos_text.tag_configure("periodo", foreground="#555555", font=self.fuente_periodos_contenido, lmargin1=20, lmargin2=20)

        # Configurar expansión del container
        periodos_container.rowconfigure(0, weight=1)
        periodos_container.columnconfigure(0, weight=1)
        
        self.cargar_hoteles_excel()
        
        # Permite que las columnas se expandan
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1)
    
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

        # Entry de solo lectura que representa la fecha completa
        entry_completa = ttk.Entry(self.fechas_entrada_frame, textvariable=self.fecha_entrada_completa, state='readonly', width=12)
        entry_completa.grid(row=0, column=8, padx=(10,0))

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

        entry_completa = ttk.Entry(self.fechas_salida_frame, textvariable=self.fecha_salida_completa, state='readonly', width=12)
        entry_completa.grid(row=0, column=8, padx=(10,0))

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

        frame_resultado = tk.Frame(self.principal_frame, bg='#F5F5F5')
        frame_resultado.grid(row=i, column=0, sticky='nsew', pady=(0, 0))
        self.widgets_dinamicos.append(frame_resultado)

        frame_resultado.rowconfigure(0, weight=1)
        frame_resultado.columnconfigure(0, weight=1)

        self.resultado = tk.Text(frame_resultado, height=20, width=80, font=self.fuente_resultado, wrap="word")
        self.resultado.grid(row=0, column=0, sticky="nsew")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(frame_resultado, orient="vertical", command=self.resultado.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Vincular Text con Scrollbar
        self.resultado.configure(yscrollcommand=scrollbar.set)
        # # Resultado
        # self.resultado = tk.Text(self.principal_frame, height=15, width=80, font=self.fuente_resultado)
        # self.resultado.grid(row=i, column=0, columnspan=2, sticky='nsew', padx=4, pady=2)

        # Configurar tags
        self.resultado.tag_configure("bold", font=self.fuente_negrita)
        self.resultado.tag_configure("grande y negra", font=self.fuente_grande_negrita)



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
        edificios = []
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                # Para cada tipo (edificio), obtener el nombre del grupo de periodo
                for tipo in hotel_excel.tipos:
                    nombre_edificio = tipo.nombre

                    # Buscar el grupo de periodo de las habitaciones de este edificio
                    nombre_grupo = self.obtener_grupo_periodo_edificio(hotel_excel, tipo)

                    if nombre_grupo and nombre_grupo.upper() != "SIN NOMBRE DE GRUPO":
                        edificios.append(f"{nombre_edificio} - {nombre_grupo}")
                    else:
                        edificios.append(nombre_edificio)

        self.var_edificio_cb['values'] = edificios
        self.seleccion_edificio.set("")

    def cargar_habitaciones_excel(self, hotel, tipo=None):
        hotel_excel = None
        if tipo is None:
            for hotelExcel in self.hoteles_excel:
                if hotelExcel.nombre.lower() == hotel:
                    self.habitaciones_excel = hotelExcel.habitaciones_directas
                    hotel_excel = hotelExcel
        else:
            # Extraer el nombre base del edificio (sin el sufijo del grupo de periodo)
            nombre_tipo_base = tipo.split(' - ')[0] if ' - ' in tipo else tipo

            for hotelExcel in self.hoteles_excel:
                if hotelExcel.nombre.lower() == hotel:
                    for tipos in hotelExcel.tipos:
                        if tipos.nombre == nombre_tipo_base:
                            self.habitaciones_excel = tipos.habitaciones
                            hotel_excel = hotelExcel
                            break

        # Crear los nombres con el grupo de periodo si corresponde
        nombres_habitaciones = []
        if hotel_excel:
            for habitacion in self.habitaciones_excel:
                nombre_grupo = self.obtener_grupo_periodo_habitacion(hotel_excel, habitacion)
                if nombre_grupo and nombre_grupo.upper() != "SIN NOMBRE DE GRUPO":
                    nombres_habitaciones.append(f"{habitacion.nombre} - {nombre_grupo}")
                else:
                    nombres_habitaciones.append(habitacion.nombre)
        else:
            nombres_habitaciones = [hab.nombre for hab in self.habitaciones_excel]

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
            # Usar el índice actual del combobox en lugar de buscar el valor
            # esto soluciona el problema de habitaciones con el mismo nombre
            idx = self.habit_excel_cb.current()
            print(f"[DEBUG] Índice del combobox (current): {idx}")
            habitacion = self.habitaciones_excel[idx]

            # Manejar precio que puede ser float o string
            if habitacion.precio is not None:
                if isinstance(habitacion.precio, (int, float)):
                    precio_texto = f"${habitacion.precio:.2f}"
                else:
                    # Es un string (ej: "closing agreement")
                    precio_texto = str(habitacion.precio)
            elif habitacion.precio_string:
                precio_texto = habitacion.precio_string
            else:
                precio_texto = "Sin precio"

            self.precio_var.set(precio_texto)
            print(f"[DEBUG] Habitación: row={habitacion.row_idx}")
            print(f"[DEBUG] - precio (tipo={type(habitacion.precio).__name__}): {habitacion.precio}")
            print(f"[DEBUG] - precio_string: {habitacion.precio_string}")
            print(f"[DEBUG] - precio_texto mostrado: {precio_texto}")
            print(f"[DEBUG] - periodo_ids: {habitacion.periodo_ids}")

            # Actualizar visualización de periodos
            print(f"[DEBUG] Actualizando periodos...")
            self.actualizar_periodos_habitacion(habitacion)
            print(f"[DEBUG] Periodos actualizados correctamente")
        except ValueError as e:
            self.precio_var.set("")
            self.limpiar_periodos()
            print(f"[ERROR] ValueError - La selección '{seleccionado}' no es válida: {e}")
        except Exception as e:
            self.precio_var.set("")
            self.limpiar_periodos()
            print(f"[ERROR] Exception - Error inesperado: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    def actualizar_periodos_habitacion(self, habitacion):
        """Actualiza el widget de periodos con la información de la habitación seleccionada"""
        # Obtener el hotel actual
        hotel_nombre = self.seleccion_hotel.get().lower() + " (a)"
        hotel_actual = None
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel_nombre:
                hotel_actual = hotel_excel
                break

        if not hotel_actual:
            self.limpiar_periodos()
            return

        # Actualizar el widget Text
        self.periodos_text.config(state='normal')
        self.periodos_text.delete('1.0', tk.END)

        # Verificar si hay periodos
        if not habitacion.periodo_ids:
            self.periodos_text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self.periodos_text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self.periodos_text.config(state='disabled')
            return

        # Agrupar los periodos por nombre de grupo
        from collections import OrderedDict
        grupos_periodos = OrderedDict()

        for pid in habitacion.periodo_ids:
            periodo = hotel_actual.periodo_por_id(pid)
            if periodo:
                # Buscar a qué grupo pertenece este periodo
                nombre_grupo = None
                for grupo in hotel_actual.periodos_group:
                    if periodo in grupo.periodos:
                        nombre_grupo = grupo.nombre
                        break

                if nombre_grupo:
                    if nombre_grupo not in grupos_periodos:
                        grupos_periodos[nombre_grupo] = []
                    grupos_periodos[nombre_grupo].append(periodo)

        if not grupos_periodos:
            self.periodos_text.insert(tk.END, "⚠️ ADVERTENCIA:\n", "advertencia")
            self.periodos_text.insert(tk.END, "Sin periodos asignados", "advertencia")
            self.periodos_text.config(state='disabled')
            return

        # Insertar con formato mejorado
        for i, (nombre_grupo, periodos) in enumerate(grupos_periodos.items()):
            if i > 0:
                self.periodos_text.insert(tk.END, "\n")

            # Insertar nombre del grupo con estilo
            self.periodos_text.insert(tk.END, f"{nombre_grupo}\n", "grupo")

            # Insertar cada periodo
            for periodo in periodos:
                inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
                fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
                # Agregar el nombresito si existe
                if periodo.nombresito:
                    self.periodos_text.insert(tk.END, f"  • {periodo.nombresito}: {inicio_str} - {fin_str}\n", "periodo")
                else:
                    self.periodos_text.insert(tk.END, f"  • {inicio_str} - {fin_str}\n", "periodo")

        self.periodos_text.config(state='disabled')

    def limpiar_periodos(self):
        """Limpia el widget de periodos"""
        self.periodos_text.config(state='normal')
        self.periodos_text.delete('1.0', tk.END)
        self.periodos_text.config(state='disabled')


    def ejecutar_comparacion_wrapper(self):
        threading.Thread(target=self.run_async, daemon= True).start()
        pass
    
    def run_async(self):
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


def run_interfaz():
    # Ejecutar testExtractor2 para generar archivo de validación
    print("\n" + "="*60)
    print("EJECUTANDO testExtractor2.py...")
    print("="*60 + "\n")

    try:
        subprocess.run([sys.executable, "testExtractor2.py"], check=True)
        print("\n" + "="*60)
        print("testExtractor2.py ejecutado exitosamente")
        print("="*60 + "\n")
    except subprocess.CalledProcessError as e:
        print(f"\nError al ejecutar testExtractor2.py: {e}\n")
    except FileNotFoundError:
        print("\nNo se encontró testExtractor2.py, continuando con la interfaz...\n")

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