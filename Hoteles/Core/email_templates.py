EMAIL_TAGS_GLOBALES = ["hotel", "habitacion_excel", "habitacion_web", "firma"]

EMAIL_TAGS_PERIODO = [
    "periodo_id",
    "fecha_inicio_periodo",
    "fecha_fin_periodo",
    "fecha_inicio_busqueda",
    "fecha_fin_busqueda",
    "precio_excel",
    "precio_web",
    "diferencia",
    "estado",
]

EMAIL_TAGS = EMAIL_TAGS_GLOBALES + EMAIL_TAGS_PERIODO

DEFAULT_EMAIL_TEMPLATE = """\
Estimado equipo de reservas,

He detectado discrepancias de precios en el hotel {hotel}.

Habitación Excel: {habitacion_excel}
Habitación Web: {habitacion_web}

COMPARACIÓN POR PERIODO:
{% for periodo %}
Periodo {periodo_id} ({fecha_inicio_periodo} - {fecha_fin_periodo})
  Búsqueda: {fecha_inicio_busqueda} - {fecha_fin_busqueda}
  Excel: {precio_excel} | Web: {precio_web} | Diferencia: {diferencia} | Estado: {estado}
{% end %}
Agradecería si pudieran revisar estas diferencias.

Saludos cordiales,
{firma}"""
