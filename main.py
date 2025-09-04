from Core.gestor_datos import *

if __name__ == "__main__":
    async def main():
        gestor = GestorDatos("./Data/Extracto.xlsx")
        datos = cargar_excel("./Data/Extracto.xlsx")
                
        # for h in datos.hoteles:
        #     print(f"🏨 {h.nombre}")
        #     for t in h.tipos:
        #         print(f"  🏷️ {t.nombre}")
        #         for hab in t.habitaciones:
        #             print(f"     🛏️ {hab.nombre} → {hab.precio}")
        #     if h.habitaciones_directas:
        #         print("  (Habitaciones sin tipo)")
        #         for hab in h.habitaciones_directas:
        #             print(f"     🛏️ {hab.nombre} → {hab.precio}")
        # gestor.mostrar_habitaciones_excel()
        # print(gestor.habitaciones_excel)# Esta es síncrona, se puede llamar directamente
        
        # Llamada a función asíncrona y se espera a que termine
        await gestor.obtener_hotel_web("2025-07-15", "2025-07-17", 2, 0)

        # # Luego de que terminó la anterior, llamamos a la siguiente
        gestor.coincidir_excel_web()  # Esta suponemos que es sincrónica, si no avisame

    asyncio.run(main())