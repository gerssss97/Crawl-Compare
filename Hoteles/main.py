import sys
import io
import time
from datetime import datetime

# Forzar UTF-8 en stdout/stderr — necesario en .exe de PyInstaller en Windows
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Trazas de arranque con timestamp. Útiles para diagnosticar dónde se va el
# tiempo entre el doble click del .exe y la aparición de la UI.
_T0 = time.perf_counter()
def _trace(etapa: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    elapsed_ms = int((time.perf_counter() - _T0) * 1000)
    try:
        print(f"[startup {ts}] (+{elapsed_ms:>5}ms) {etapa}", flush=True)
    except Exception:
        pass

_trace("UTF-8 wrappers instalados")

# Logger ANTES de todo: si algo más abajo crashea, queda registrado.
from Deploy.error_logger import setup_error_logging
setup_error_logging()
_trace("error_logger setup completo")

# Smoke test post-build: si se invoca con --self-test, corre verificaciones
# de bundling y sale (no levanta la UI). Se ejecuta en build.bat tras compilar.
# ANTES del splash: si no, queda una ventana Tk huérfana al final del build.
if "--self-test" in sys.argv:
    from Deploy.smoke_test import run_smoke_test
    run_smoke_test()

# Splash solo en .exe. En dev ya se ve la consola y el arranque es <1s.
# El import va adentro del if para no cargar tk innecesariamente en dev.
_splash = None
if getattr(sys, "frozen", False):
    from Deploy.splash import SplashScreen
    _splash = SplashScreen()
    _trace("SplashScreen creado y visible")

from Deploy.startup_check import run_checks
_trace("antes de run_checks")
run_checks(on_progress=_splash.update_status if _splash else None)
_trace("run_checks completo")

# El splash queda abierto durante los imports pesados (CTk, gestor_datos,
# CrawlCompareGUI) — son ~800ms en frío. Lo cerramos recién antes del mainloop.
if _splash:
    _splash.update_status("Cargando interfaz...")

_trace("importando customtkinter")
import customtkinter as ctk
_trace("importando Core.gestor_datos")
from Core.gestor_datos import *

if _splash:
    _splash.update_status("Preparando datos...")

_trace("importando CrawlCompareGUI")
from UI.interfaz_ctk import CrawlCompareGUI
_trace("imports principales completos")


def run_app():
    """Lanza la interfaz CustomTkinter."""
    global _splash

    # IMPORTANTE: cerrar el splash ANTES de instanciar ctk.CTk().
    # Tener dos roots Tk vivos en simultáneo (tk.Tk del splash + ctk.CTk)
    # rompe el registro de imágenes de PIL/CTk: las CTkImage se asocian al
    # intérprete Tcl viejo y al destruirlo explota con
    # "image pyimage1 doesn't exist" cuando los CTkButton del header
    # intentan redibujarse en mainloop.
    if _splash:
        _splash.update_status("Iniciando ventana...")
        _splash.close()
        _splash = None
        _trace("splash cerrado")

    _trace("instanciando ctk.CTk()")
    root = ctk.CTk()

    _trace("instanciando CrawlCompareGUI")
    app = CrawlCompareGUI(root)

    _trace("entrando a mainloop")
    root.mainloop()


if __name__ == "__main__":
    run_app()


# ============================================================
# Codigo de test / debug (descomentar segun necesidad)
# ============================================================
def _test_carga_datos():
    """Imprime un resumen del Excel para verificar la carga."""
    
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
       

