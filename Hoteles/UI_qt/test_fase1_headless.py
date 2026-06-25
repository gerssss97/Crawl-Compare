"""Test headless de Fase 1: AppState v2 (sin Tkinter) + controladores reales sin cambios.

Demuestra la tesis del plan: los controladores tocan AppState solo via .get/.set/
trace_add, asi que con ObservableVar (Signal de Qt con esa misma API) funcionan SIN
modificarse. No abre ventana; solo necesita un QApplication vivo para los Signals.

Correr con el Python del env crawler:
    "C:/Users/German Lucero/anaconda3/envs/crawler/python.exe" Hoteles/UI_qt/test_fase1_headless.py
"""
import sys
import os

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

from PySide6.QtCore import QCoreApplication
from UI_qt.state import EventBus, AppState
from UI_qt.state.observable import StringVar, IntVar
from UI_qt.controllers import ControladorPrecios, ControladorComparacion, ControladorValidacion

app = QCoreApplication(sys.argv)  # event loop minimo para que los Signals funcionen

fallos = []


def check(cond, msg):
    estado = "OK  " if cond else "FALL"
    print(f"  [{estado}] {msg}")
    if not cond:
        fallos.append(msg)


print("== 1. ObservableVar replica el contrato de tk.Variable ==")
sv = StringVar()
check(sv.get() == "", "StringVar() arranca en ''")
sv.set(123)
check(sv.get() == "123", "StringVar coacciona a str (123 -> '123')")

iv = IntVar(value=1)
check(iv.get() == 1, "IntVar(value=1) arranca en 1 (int)")
iv.set("5")
check(iv.get() == 5 and isinstance(iv.get(), int), "IntVar coacciona a int ('5' -> 5)")

# trace_add: callback con firma estilo Tk (*args), y emite SIEMPRE
emisiones = []
sv2 = StringVar()
sv2.trace_add('write', lambda *args: emisiones.append(sv2.get()))
sv2.set("a")
sv2.set("a")   # mismo valor: tk.Variable re-emite -> nosotros tambien
sv2.set("b")
check(emisiones == ["a", "a", "b"], f"trace_add emite en cada set (incl. repetido): {emisiones}")


print("== 2. AppState v2 instancia sin Tkinter y emite por EventBus ==")
bus = EventBus()
state = AppState(bus)
check(state.adultos.get() == 1, "adultos default = 1")
check(state.precio.get() == "(ninguna seleccionada)", "precio default correcto")

eventos = []
bus.on('hotel_changed', lambda data: eventos.append(('hotel_changed', data)))
state.hotel.set("Hotel Serene")
check(('hotel_changed', "Hotel Serene") in eventos, "set(hotel) dispara hotel_changed via EventBus")


print("== 3. Controladores reales se conectan SIN modificarse ==")
try:
    validacion = ControladorValidacion(state)
    precios = ControladorPrecios(state, bus)        # hace trace_add sobre fechas
    comparacion = ControladorComparacion(state, bus, validacion)
    check(True, "ControladorPrecios/Comparacion/Validacion instanciados con AppState v2")
except Exception as e:
    check(False, f"instanciacion de controladores fallo: {type(e).__name__}: {e}")

# ControladorPrecios escucha 'habitacion_changed' (string vacio limpia precio).
# Verificamos que su trace sobre fechas + su listener de EventBus reaccionan.
precios_eventos = []
bus.on('precios_actualizados', lambda data: precios_eventos.append(data.get('tipo')))
# Disparar el handler de habitacion vacia -> debe emitir 'precios_actualizados' tipo sin_fechas
bus.emit('habitacion_changed', "")
check('sin_fechas' in precios_eventos,
      f"ControladorPrecios reacciono a habitacion vacia sin cambios de codigo: {precios_eventos}")


print()
if fallos:
    print(f"RESULTADO: {len(fallos)} FALLO(S)")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULTADO: TODO OK. Fase 1 validada: controladores reutilizados sin tocar una linea.")
    sys.exit(0)
