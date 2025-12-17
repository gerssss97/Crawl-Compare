from .gestor_datos import *
import smtplib
from email.mime.text import MIMEText ##crea msjs con formato adecuado
from email.mime.multipart import MIMEMultipart


gestor = GestorDatos("./Data/Extracto_prueba.xlsx")

def dar_hoteles_excel():
    return gestor.hoteles_excel_get

def dar_habitaciones_excel(hotelExcel: HotelExcel, tipo):
    return gestor.habitaciones_excel_get(hotelExcel, tipo)

def dar_tipos_habitacion_excel(HotelExcel: HotelExcel):
    return gestor.tipos_habitaciones_excel_get(HotelExcel)

## devuelve true si la diferencia es mayor o igual a 1
async def comparar_habitaciones(habitacion_excel: HabitacionExcel, precio_hab_excel):
    await gestor.coincidir_excel_web(habitacion_excel) #busca la mejor coincidencia con hab web

    precio_web = gestor.mejor_habitacion_web_get.combos[0].precio  # type: ignore
    diferencia = abs(float(precio_hab_excel) - precio_web) # type: ignore
    print(f"Precio Excel: {precio_hab_excel} - Precio Web: {precio_web} - Diferencia: {diferencia}")
    if diferencia>=1:
        return True
    else: 
        return False
    

def dar_habitacion_web():
    return gestor.mejor_habitacion_web_get

def dar_mensaje():
    return gestor.mensaje_get

async def dar_hotel_web(fecha_ingreso, fecha_egreso, adultos, niños, force_fresh=False):
    """Obtiene datos del hotel web.

    Args:
        fecha_ingreso: Fecha entrada DD-MM-YYYY
        fecha_egreso: Fecha salida DD-MM-YYYY
        adultos: Número de adultos
        niños: Número de niños
        force_fresh: Si True, fuerza scraping fresco ignorando caché

    Returns:
        HotelWeb con datos scrapeados

    Raises:
        ValueError: Si no se pueden obtener datos válidos
    """
    hotel = await gestor.obtener_hotel_web(fecha_ingreso, fecha_egreso, adultos, niños, force_fresh)

    if hotel is None or not hotel.habitacion:
        raise ValueError("No se pudieron obtener datos válidos del hotel web")
    return hotel

def generar_texto_email(hotel, habitacion_excel, precio_excel, precio_web):
    return (
        "Estimado equipo de reservas,\n\n"
        f"He notado una discrepancia en los precios de las habitaciones entre el archivo Excel y la página web del hotel {hotel}.\n\n"
        "Detalles de la comparación:\n"
        f"- Habitación Excel: {habitacion_excel}\n"
        f"- Precio en Excel: {precio_excel}\n"
        f"- Precio en Web: {precio_web}\n\n"
        "Agradecería si pudieran revisar esta diferencia y proporcionarme una explicación o corrección si es necesario.\n\n"
        "Gracias por su atención.\n\n"
        "Saludos cordiales,\n"
        "Germán Lucero"
    )

def enviar_email_discrepancia(hotel, habitacion_excel, precio_excel, precio_web, remitente, destinatario, texto_override=None):
    """Envía email notificando discrepancia de precios.

    Args:
        hotel: Nombre del hotel
        habitacion_excel: Nombre de habitación en Excel
        precio_excel: Precio en Excel
        precio_web: Precio en web
        remitente: Email del remitente
        destinatario: Email del destinatario
        texto_override: Texto personalizado (opcional)

    Returns:
        bool: True si el envío fue exitoso, False en caso contrario

    Raises:
        ValueError: Si GMTP_KEY no está configurada en variables de entorno
    """
    clave = os.getenv("GMTP_KEY")

    if not clave:
        raise ValueError(
            "GMTP_KEY no está configurada. Configure la variable de entorno "
            "con su clave de aplicación de Gmail antes de enviar emails.\n"
            "Ejemplo: set GMTP_KEY=tu_clave_aqui (Windows) o export GMTP_KEY=tu_clave_aqui (Linux/Mac)"
        )

    asunto = f"Discrepancia de precios - {hotel}"

    if texto_override:
        texto_mensaje = texto_override
    else:
        texto_mensaje = generar_texto_email(hotel, habitacion_excel, precio_excel, precio_web)

    return enviar_correo(remitente, clave, destinatario, asunto, texto_mensaje)

def generar_texto_email_multiperiodo(hotel, resultado_multiperiodo):
    """Genera texto de email para resultado multi-periodo.

    Args:
        hotel: Nombre del hotel
        resultado_multiperiodo: ResultadoComparacionMultiperiodo

    Returns:
        str: Texto formateado del email
    """
    # Header
    texto = "Estimado equipo de reservas,\n\n"
    texto += f"He detectado discrepancias de precios en el hotel {hotel}.\n\n"

    # Habitaciones
    texto += f"Habitación Excel: {resultado_multiperiodo.habitacion_excel_nombre}\n"
    texto += f"Habitación Web: {resultado_multiperiodo.habitacion_web_matcheada.nombre}\n\n"

    # Tabla de comparación
    texto += "COMPARACIÓN POR PERIODO:\n"
    texto += "=" * 80 + "\n"
    texto += f"{'Periodo':<25} | {'Fechas':<20} | {'Excel':<10} | {'Web':<10} | {'Diferencia':<12}\n"
    texto += "-" * 80 + "\n"

    for res_periodo in resultado_multiperiodo.periodos:
        periodo = res_periodo.periodo
        nombre_periodo = f"Periodo {periodo.id}"

        fecha_inicio_str = periodo.fecha_inicio.strftime("%d/%m/%Y")
        fecha_fin_str = periodo.fecha_fin.strftime("%d/%m/%Y")
        fechas_str = f"{fecha_inicio_str}-{fecha_fin_str}"

        if isinstance(res_periodo.precio_excel, (int, float)):
            precio_excel_str = f"${res_periodo.precio_excel:.2f}"
            diferencia = abs(res_periodo.precio_excel - res_periodo.precio_web)
            diferencia_str = f"${diferencia:.2f}"
        else:
            precio_excel_str = str(res_periodo.precio_excel)
            diferencia_str = "N/A"

        precio_web_str = f"${res_periodo.precio_web:.2f}"
        estado = "OK" if res_periodo.coincide else "⚠️ DIFF"

        fila = f"{nombre_periodo:<25} | {fechas_str:<20} | {precio_excel_str:<10} | {precio_web_str:<10} | {diferencia_str:<12} {estado}\n"
        texto += fila

    texto += "=" * 80 + "\n\n"

    # Footer
    texto += "Agradecería si pudieran revisar estas diferencias.\n\n"
    texto += "Saludos cordiales,\nGermán Lucero"

    return texto


def enviar_email_multiperiodo(hotel, resultado_multiperiodo, remitente, destinatario):
    """Envía email con discrepancias multi-periodo.

    Args:
        hotel: Nombre del hotel
        resultado_multiperiodo: ResultadoComparacionMultiperiodo
        remitente: Email del remitente
        destinatario: Email del destinatario

    Returns:
        bool: True si el envío fue exitoso, False en caso contrario

    Raises:
        ValueError: Si GMTP_KEY no está configurada
    """
    if not resultado_multiperiodo.tiene_discrepancias:
        print("No hay discrepancias, no se envía email.")
        return False

    texto = generar_texto_email_multiperiodo(hotel, resultado_multiperiodo)
    asunto = f"Discrepancias de precios multi-periodo - {hotel}"

    clave = os.getenv("GMTP_KEY")
    if not clave:
        raise ValueError(
            "GMTP_KEY no está configurada. Configure la variable de entorno "
            "con su clave de aplicación de Gmail antes de enviar emails.\n"
            "Ejemplo: set GMTP_KEY=tu_clave_aqui (Windows) o export GMTP_KEY=tu_clave_aqui (Linux/Mac)"
        )

    return enviar_correo(remitente, clave, destinatario, asunto, texto)


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


