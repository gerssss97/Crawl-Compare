from .gestor_datos import *
import smtplib
from email.mime.text import MIMEText ##crea msjs con formato adecuado
from email.mime.multipart import MIMEMultipart


gestor = GestorDatos("./Data/Extracto.xlsx")

def dar_hoteles_excel():
    return gestor.hoteles_excel_get

def dar_habitaciones_excel(hotelExcel, tipo):
    return gestor.habitaciones_excel_get(hotelExcel, tipo)

def dar_tipos_habitacion_excel(HotelExcel):
    return gestor.tipos_habitaciones_excel_get(HotelExcel)

## devuelve true si la diferencia es mayor o igual a 1
async def comparar_habitaciones(habitacion_excel,precio_hab_excel):
    await gestor.coincidir_excel_web(habitacion_excel) #busca la mejor coincidencia con hab web

    precio_web = gestor.mejor_habitacion_web_get.combos[0].precio  # type: ignore
    ##precio_web = gestor.mejor_habitacion_web.combos[0].precio # type: ignore
    ##precio_combo_elegido = precio_hab_excel # type: ignore
    diferencia = abs(float(precio_hab_excel) - precio_web) # type: ignore
    print(f"Precio Excel: {precio_hab_excel} - Precio Web: {precio_web} - Diferencia: {diferencia}")
    if diferencia>=1:
        print("true")   
        return True
    else:
        print("False") 
        return False
    

def dar_habitacion_web():
    return gestor.mejor_habitacion_web_get

async def dar_hotel_web(fecha_ingreso,fecha_egreso,adultos,niños):
    hotel = await gestor.obtener_hotel_web( fecha_ingreso,fecha_egreso,adultos,niños)
    
    if hotel is None or not hotel.habitacion:
        raise ValueError("No se pudieron obtener datos válidos del hotel web")
    return hotel



def enviar_correo(remitente, clave, destinatario, asunto, cuerpo_mensaje):
    # Configurar el servidor SMTP de Gmail
    servidor_smtp = "smtp.gmail.com"
    puerto = 587 # Puerto para TLS

    # Crear un objeto de mensaje
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto

    # Adjuntar el cuerpo del mensaje
    msg.attach(MIMEText(cuerpo_mensaje, 'plain'))

    try:
        # Iniciar la conexión segura con TLS
        server = smtplib.SMTP(servidor_smtp, puerto)
        server.starttls()

        # Iniciar sesión en la cuenta de Gmail
        server.login(remitente, clave)

        # Enviar el correo
        server.sendmail(remitente, destinatario, msg.as_string())
        print("Correo enviado exitosamente!")
        return True
    except Exception as e:
        print(f"Ocurrió un error al enviar el correo: {e}")
        return False
    finally:
        # Cerrar la conexión
        server.quit()


