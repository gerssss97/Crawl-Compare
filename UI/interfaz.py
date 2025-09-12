import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re
import threading

from models.hotel import *
from Core.controller import *


class InterfazApp:
    ##valida que sean de cero a dies digitos, solo separados por guiones
    def validar_caracter(self, valor):
            return re.fullmatch(r"[\d\-]{0,10}", valor) is not None

    def validar_fecha(self):
        campos = [("entrada", self.fecha_entrada.get()), ("salida", self.fecha_salida.get())]
        for nombre, fecha in campos:
            try:
                datetime.strptime(fecha, "%d-%m-%Y")
            except ValueError:
                messagebox.showerror("Error", f"La fecha de {nombre} debe tener el formato DD-MM-AAAA y ser válida.")
                return False
        return True
    
    def validar_orden_fechas(self):
        fecha_entrada = datetime.strptime(self.fecha_entrada.get(), "%d-%m-%Y")
        fecha_salida = datetime.strptime(self.fecha_salida.get(), "%d-%m-%Y")

        if fecha_salida <= fecha_entrada:
            messagebox.showerror("Error", "La fecha de salida debe ser posterior a la fecha de entrada.")
            print("false")
            return False
        return True
            


    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de precios - Alvear Hotel")

        # Campos de entrada
        self.seleccion_hotel = tk.StringVar()
        self.seleccion_edificio = tk.StringVar()
        self.seleccion_habitacion_excel = tk.StringVar()
        self.fecha_entrada = tk.StringVar()
        self.fecha_salida = tk.StringVar()
        self.adultos = tk.IntVar(value=1)
        self.niños = tk.IntVar()
        self.precio_var = tk.StringVar(value="(ninguna seleccionada)")

        vcmd = (root.register(self.validar_caracter), '%P')
        self.vcmd = vcmd
        
        # FRAME Encabezado
        self.encabezado_frame = ttk.Frame(self.root)
        self.encabezado_frame.columnconfigure(1, weight=2, uniform='col')
        self.encabezado_frame.columnconfigure(0, weight=1, uniform='col')
        
        self.encabezado_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Label(self.encabezado_frame, text="Selección hotel: ").grid(row=0, column=0, sticky='w', padx=4, pady=2)
        self.hotel_cb = ttk.Combobox(self.encabezado_frame, textvariable=self.seleccion_hotel, state="readonly")
        self.hotel_cb.grid(row=0, column=1, sticky='ew', padx=4, pady=2)
        self.hotel_cb.bind("<<ComboboxSelected>>", self.on_hotel_cambiado)
        self.crear_campos_estaticos(1)
        
        # FRAME precio de la habitación (col 2)
        self.precio_frame = ttk.Frame(self.root)
        self.precio_frame.grid(row=0, column=2, rowspan=3, sticky='nsew', padx=4, pady=2)

        ttk.Label(self.precio_frame, text="Precio de la habitación").grid(row=0, column=0, sticky='w', pady=(0,2))
        self.label_precio = ttk.Label(self.precio_frame, textvariable=self.precio_var)
        self.label_precio.grid(row=1, column=0, sticky='w')
        
        self.cargar_hoteles_excel()
        
        # Permite que las columnas se expandan
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1)
    
    def mostrar_email_btn(self):
        self.boton_ejecutar = ttk.Button(self.precio_frame, text="Envio de email", command=self.crear_pantalla_mail)
        self.boton_ejecutar.grid(row=2, column=0, sticky="ew")
        
    
    def crear_campos_estaticos(self, desde=1, incluir_edificio=False):
        
        # Si el frame ya existe, lo destruimos para recrearlo
        if hasattr(self, 'campos_frame'):
            self.campos_frame.grid_forget()

        self.campos_frame = ttk.Frame(self.root)
        self.campos_frame.columnconfigure(1,weight=2, uniform='col')
        self.campos_frame.columnconfigure(0,weight=1, uniform='col')
               
        self.campos_frame.grid(row=desde, column=0, columnspan=2, sticky="nsew")

        i = 0  # fila relativa dentro del frame

        # Campo opcional: Edificio
        if incluir_edificio:
            self.label_edificio = ttk.Label(self.campos_frame, text="Edificio:")
            self.var_edificio_cb = ttk.Combobox(self.campos_frame, textvariable=self.seleccion_edificio, state="readonly")
            self.var_edificio_cb.bind("<<ComboboxSelected>>", self.on_edificio_cambiado)
            self.label_edificio.grid(row=i, column=0, sticky='w', padx=4, pady=2)
            self.var_edificio_cb.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
            i += 1

        # Selección habitación Excel
        self.label_habit_excel = ttk.Label(self.campos_frame, text="Selección habitación Excel:")
        self.habit_excel_cb = ttk.Combobox(self.campos_frame, textvariable=self.seleccion_habitacion_excel, state="readonly")
        self.habit_excel_cb.bind("<<ComboboxSelected>>", self.on_habitacion_excel_cambiada)
        self.label_habit_excel.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        self.habit_excel_cb.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Fecha entrada
        self.label_fecha_entrada = ttk.Label(self.campos_frame, text="Fecha de entrada (DD-MM-AAAA):")
        self.entry_fecha_entrada = ttk.Entry(self.campos_frame, textvariable=self.fecha_entrada, validate='key', validatecommand=self.vcmd)
        self.label_fecha_entrada.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        self.entry_fecha_entrada.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Fecha salida
        self.label_fecha_salida = ttk.Label(self.campos_frame, text="Fecha de salida (DD-MM-AAAA):")
        self.entry_fecha_salida = ttk.Entry(self.campos_frame, textvariable=self.fecha_salida, validate='key', validatecommand=self.vcmd)
        self.label_fecha_salida.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        self.entry_fecha_salida.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Adultos
        self.label_adultos = ttk.Label(self.campos_frame, text="Cantidad de adultos:")
        self.entry_adultos = ttk.Entry(self.campos_frame, textvariable=self.adultos)
        self.label_adultos.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        self.entry_adultos.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Niños
        self.label_niños = ttk.Label(self.campos_frame, text="Cantidad de niños:")
        self.entry_niños = ttk.Entry(self.campos_frame, textvariable=self.niños)
        self.label_niños.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        self.entry_niños.grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        i += 1

        # Botón ejecutar comparacion
        self.boton_ejecutar = ttk.Button(self.campos_frame, text="Ejecutar comparación", command=self.ejecutar_comparacion_wrapper)
        self.boton_ejecutar.grid(row=i, column=0, columnspan=2, sticky='ew', padx=4, pady=6)
        i += 1

        # Resultado
        self.resultado = tk.Text(self.campos_frame, height=15, width=80)
        self.resultado.grid(row=i, column=0, columnspan=2, sticky='nsew', padx=4, pady=2)

        # self.campos_frame.rowconfigure(i, weight=1)
    def crear_pantalla_mail(self):
        self.geometria_anterior = self.root.geometry()
        
        self.campos_frame.grid_forget()
        self.encabezado_frame.grid_forget()
        self.precio_frame.grid_forget()
        
        self.mail_frame = ttk.Frame(self.root)
        self.mail_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.mail_frame.columnconfigure(1, weight=2, uniform='col')
        self.root.geometry(self.geometria_anterior)

        lbl_email = ttk.Label(self.mail_frame, text="Contenido del Email:")
        lbl_email.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    
        self.email_textbox = tk.Text(self.mail_frame, wrap="word", height=15, width=50)
        self.email_textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        texto_predeterminado = (
            "Estimado equipo de reservas,\n\n"
            "He notado una discrepancia en los precios de las habitaciones entre el archivo Excel y la página web del hotel "f"{self.seleccion_hotel.get()}" ".\n\n"
            "Detalles de la comparación:\n"
            f"- Habitación Excel: {self.seleccion_habitacion_excel.get()}\n"
            f"- Precio en Excel: {self.precio_var.get()}\n"
            f"- Precio en Web: (obtenido tras la comparación)"f"{self.habitacion_web.combos[0].precio}"" \n\n"
            "Agradecería si pudieran revisar esta diferencia y proporcionarme una explicación o corrección si es necesario.\n\n"
            "Gracias por su atención.\n\n"
            "Saludos cordiales,\n"
            "[Tu Nombre]"
        )
        self.email_textbox.insert(tk.END, texto_predeterminado)

        enviar_btn = ttk.Button(self.mail_frame, text="Enviar Email", command=self.enviar_email)
        enviar_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def enviar_email(self):
        texto_mensaje = self.email_textbox.get("1.0", tk.END).strip()
        remitente ="gerlucero1997@gmail.com"
        destinatario = "gerlucero1977@gmail.com"
        clave=os.getenv("GMTP_KEY")
        asunto = f"Discrepancia de precios - {self.seleccion_hotel.get()}"
        enviar_correo(remitente,clave,destinatario,asunto,texto_mensaje)
        
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
    
    def cargar_edificios_excel(self, hotel):
        edificios = []
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel:
                edificios = [tipo.nombre for tipo in hotel_excel.tipos]
        self.var_edificio_cb['values'] = edificios
        self.seleccion_edificio.set("")

    def cargar_habitaciones_excel(self, hotel, tipo=None):
        if tipo is None:
            for hotelExcel in self.hoteles_excel:
                if hotelExcel.nombre.lower() == hotel:
                    self.habitaciones_excel = hotelExcel.habitaciones_directas
        else:
            for hotelExcel in self.hoteles_excel:
                if hotelExcel.nombre.lower() == hotel:
                    for tipos in hotelExcel.tipos:
                        if tipos.nombre == tipo:
                            self.habitaciones_excel = tipos.habitaciones
        self.habit_excel_cb['values'] = [HabitacionExcel.nombre for HabitacionExcel in self.habitaciones_excel]
        self.seleccion_habitacion_excel.set("")
        if self.habitaciones_excel:
            self.on_habitacion_excel_cambiada(None)

    def on_hotel_cambiado(self, event):
        hotel = self.seleccion_hotel.get().lower()
        hotel = hotel + " (a)"
        print(f"Hotel cambiado a: {hotel}")
        for hotel_excel in self.hoteles_excel:
            if hotel_excel.nombre.lower() == hotel and hotel_excel.tipos:
                self.crear_campos_estaticos(desde=1, incluir_edificio=True)
                self.cargar_edificios_excel(hotel)
            elif hotel_excel.nombre.lower() == hotel:
                self.crear_campos_estaticos(desde=1, incluir_edificio=False)
                self.cargar_habitaciones_excel(hotel)
            else:
                print("no se encontro el hotel")

    def on_edificio_cambiado(self, event):
        edificio = self.seleccion_edificio.get()
        hotel = self.seleccion_hotel.get().lower()
        hotel = hotel + " (a)"
        self.cargar_habitaciones_excel(hotel, edificio)
    
    def on_habitacion_excel_cambiada(self, event):
        seleccionado = self.seleccion_habitacion_excel.get()
    
        try:
            idx = self.habit_excel_cb['values'].index(seleccionado)
            print(idx)
            habitacion = self.habitaciones_excel[idx]
            self.precio_var.set(f"${habitacion.precio:.2f}")
            print(habitacion.row_idx, habitacion.precio)
        except ValueError:
            self.precio_var.set("") # Limpia el campo de precio
            print(f"Error: La selección '{seleccionado}' no es válida.")
            
 
    def ejecutar_comparacion_wrapper(self):
        threading.Thread(target=self.run_async, daemon= True).start()
        pass
    
    def run_async(self):
        asyncio.run(self.ejecutar_comparacion())
        
    async def ejecutar_comparacion(self):
        try:
        # Validaciones iniciales
            if not self.validar_fecha() or not self.validar_orden_fechas():
                return
            datos = (
                self.fecha_entrada.get(), 
                self.fecha_salida.get(),
                self.adultos.get(),
                self.niños.get(),
                self.seleccion_habitacion_excel.get(),
                self.precio_var.get()
            )
            self.resultado.insert(tk.END, f"Ejecutando scraping con: {datos}\n")
            
            hotel_web = await dar_hotel_web(self.fecha_entrada.get(),self.fecha_salida.get(),self.adultos.get(),self.niños.get())
            if not hotel_web or not hotel_web.habitacion:
                self.resultado.insert(tk.END, "Error: No se pudieron obtener datos del hotel web\n")
                return
        
            precio = normalizar_precio_str(self.precio_var.get())
            coincide = await comparar_habitaciones(self.seleccion_habitacion_excel.get(),precio)
            self.habitacion_web =  dar_habitacion_web()
            
            
            if  coincide: 
                self.resultado.insert(tk.END, "Se encontraron diferencias de precio.\n")
                self.mostrar_email_btn()
            else:
                self.resultado.insert(tk.END, "Las habitaciones coinciden en precio y nombre.\n")
                texto_habitacion = imprimir_habitacion_web(self.habitacion_web)
                self.resultado.insert(tk.END, f"Habitacion web:\n {texto_habitacion}\n") 
        except ValueError as ve:
            self.resultado.insert(tk.END, f"Error de validación: {str(ve)}\n")
        except Exception as e:
            self.resultado.insert(tk.END, f"Error inesperado: {str(e)}\n")


def run_interfaz():
    root = tk.Tk()
    app = InterfazApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_interfaz()
        #PARA VER EN DISTINTOS COLORES 
        # for col in range(2):
        #     color = 'lightblue' if col == 0 else 'lightgreen'
        #     ttk.Label(self.campos_frame, text=f'Col {col}', background=color).grid(row=0, column=col, sticky='nsew')