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
                print(f"  • {periodo.id} - {periodo.nombre}: {periodo.fecha_inicio} - {periodo.fecha_fin}")
        
        # Mostrar tipos de habitaciones
        if hotel.tipos:
            print("\n🏷️ Tipos de Habitaciones:")
            for tipo in hotel.tipos:
                print(f"\n  📌 {tipo.nombre}")
                for hab in tipo.habitaciones:
                    precio_str = f"${hab.precio}" if hab.precio else "Sin precio"
                    print(f"    • {hab.nombre} ({precio_str})")
                    for id in range(len(hab.periodo_ids)):
                        if id == 0:
                            print(f"primer periodo de id: {hab.periodo_ids[id]}")
                        if id == len(hab.periodo_ids)-1:
                            print(f"ultimo periodo de id: {hab.periodo_ids[id]}")
                        
        # Mostrar habitaciones directas
        if hotel.habitaciones_directas:
            print("\n🛏️ Habitaciones Directas:")
            for hab in hotel.habitaciones_directas:
                if hab.precio:
                    precio_str = f"${hab.precio}" if hab.precio else "Sin precio"
                    print(f"  • {hab.nombre} ({precio_str})")
                else:
                    print(f"  • {hab.nombre} con precio especial: {hab.precio_string}   ")
                for id in range(len(hab.periodo_ids)):
                    if id == 0:
                        print(f"primer periodo de id: {hab.periodo_ids[id]}")
                    if id == len(hab.periodo_ids)-1:
                        print(f"ultimo periodo de id: {hab.periodo_ids[id]}")
            
        print("\n" + "-"*50)
       

