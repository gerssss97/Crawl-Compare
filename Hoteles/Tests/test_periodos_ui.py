"""
Script de prueba para verificar el formateo de periodos en la interfaz
"""
import sys
import io
from ExtractorDatos.extractor import cargar_excel
from Core.periodo_utils import formatear_periodos_habitacion

# Configurar encoding UTF-8 para la consola
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_formateo_periodos():
    # Cargar datos del Excel
    path_excel = "./Data/Extracto_prueba2.xlsx"
    datos = cargar_excel(path_excel)

    print("\n=== PRUEBA DE VISUALIZACION DE PERIODOS ===\n")

    # Probar con el primer hotel
    if datos.hoteles:
        hotel = datos.hoteles[0]
        print(f"Hotel: {hotel.nombre}")
        print("=" * 60)

        # Mostrar información de grupos de periodos
        print(f"\nGrupos de Periodos disponibles: {len(hotel.periodos_group)}")
        for grupo in hotel.periodos_group:
            print(f"\n  Grupo: {grupo.nombre}")
            print(f"  Cantidad de periodos: {len(grupo.periodos)}")
            for periodo in grupo.periodos:
                print(f"    - ID {periodo.id}: {periodo.fecha_inicio} - {periodo.fecha_fin}")

        print("\n" + "=" * 60)
        print("\nHABITACIONES Y SUS PERIODOS:\n")

        # Probar con habitaciones directas
        if hotel.habitaciones_directas:
            print("\n--- Habitaciones Directas ---\n")
            for i, hab in enumerate(hotel.habitaciones_directas[:5]):  # Primeras 5
                print(f"\n{i+1}. {hab.nombre}")
                print(f"   Precio: ${hab.precio}" if hab.precio else f"   Precio string: {hab.precio_string}")
                print(f"   IDs de periodos: {hab.periodo_ids}")

                # Formatear periodos
                texto_formateado = formatear_periodos_habitacion(hotel, hab)
                print("\n   VISUALIZACION EN INTERFAZ:")
                print("   " + "-" * 50)
                for linea in texto_formateado.split('\n'):
                    print(f"   {linea}")
                print("   " + "-" * 50)

        # Probar con habitaciones por tipo
        if hotel.tipos:
            print("\n\n--- Habitaciones por Tipo ---\n")
            for tipo in hotel.tipos[:2]:  # Primeros 2 tipos
                print(f"\n[Tipo: {tipo.nombre}]")
                for i, hab in enumerate(tipo.habitaciones[:3]):  # Primeras 3 de cada tipo
                    print(f"\n  {i+1}. {hab.nombre}")
                    print(f"     Precio: ${hab.precio}" if hab.precio else f"     Precio string: {hab.precio_string}")
                    print(f"     IDs de periodos: {hab.periodo_ids}")

                    # Formatear periodos
                    texto_formateado = formatear_periodos_habitacion(hotel, hab)
                    print("\n     VISUALIZACION EN INTERFAZ:")
                    print("     " + "-" * 45)
                    for linea in texto_formateado.split('\n'):
                        print(f"     {linea}")
                    print("     " + "-" * 45)

if __name__ == "__main__":
    test_formateo_periodos()