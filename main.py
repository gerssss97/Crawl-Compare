from Core.gestor_datos import *
##from UI.interfaz import run_interfaz

if __name__ == "__main__":
    
     # Test de extracción
    path_excel = "./Data/Extracto2.xlsx"  # ajusta la ruta según tu estructura
    datos = cargar_excel(path_excel)
    
    print("\n=== 📊 DATOS EXTRAÍDOS DEL EXCEL ===\n")
    
    # Imprimir información de cada hotel
    for hotel in datos.hoteles:
        print(f"\n🏨 Hotel: {hotel.nombre}")
        print("=" * (8 + len(hotel.nombre)))
        
        # Mostrar periodos si existen
        if hotel.periodos:
            print("\n📅 Periodos:")
            for periodo in hotel.periodos:
                print(f"  • {periodo.nombre}: {periodo.fecha_inicio} - {periodo.fecha_fin}")
        
        # Mostrar tipos de habitaciones
        if hotel.tipos:
            print("\n🏷️ Tipos de Habitaciones:")
            for tipo in hotel.tipos:
                print(f"\n  📌 {tipo.nombre}")
                for hab in tipo.habitaciones:
                    precio_str = f"${hab.precio}" if hab.precio else "Sin precio"
                    print(f"    • {hab.nombre} ({precio_str})")
        
        # Mostrar habitaciones directas
        if hotel.habitaciones_directas:
            print("\n🛏️ Habitaciones Directas:")
            for hab in hotel.habitaciones_directas:
                precio_str = f"${hab.precio}" if hab.precio else "Sin precio"
                print(f"  • {hab.nombre} ({precio_str})")
        
        print("\n" + "-"*50)
       

