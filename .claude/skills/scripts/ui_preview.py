#!/usr/bin/env python3
"""
ui_preview.py - Preview de componentes UI en ventanas standalone

Uso:
    python ui_preview.py [componente] [--datos JSON]

Ejemplos:
    python ui_preview.py fecha
    python ui_preview.py combo --datos='{"opciones": ["A", "B", "C"]}'
    python ui_preview.py formulario
"""

import sys
import json
import importlib
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk

# Fix para emojis en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar path raíz al PYTHONPATH
# .claude/skills/scripts/ui_preview.py -> .claude/skills/ -> .claude/ -> raíz
REPO_ROOT = Path(__file__).parent.parent.parent.parent
HOTELES_DIR = REPO_ROOT / "Hoteles"

# Cambiar al directorio Hoteles para imports correctos
import os
os.chdir(str(HOTELES_DIR))

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HOTELES_DIR))


# Mapeo de nombres cortos → (módulo, clase)
COMPONENTES = {
    # Widgets básicos
    'fecha': ('UI.components.date_input', 'DateInputWidget'),
    'combo': ('UI.components.labeled_combobox', 'LabeledComboBox'),
    'entrada': ('UI.components.entrada_etiquetada', 'EntradaEtiquetada'),
    'precio': ('UI.components.precio_panel', 'PrecioPanel'),
    'periodos': ('UI.components.periodos_panel', 'PeriodosPanel'),

    # Vistas
    'formulario': ('UI.views.formulario_seleccion_hotel', 'FormularioSeleccionHotel'),
    'formulario-reserva': ('UI.views.formulario_reserva', 'FormularioReserva'),
    'resultados': ('UI.views.vista_resultados', 'VistaResultados'),
}


class MockEventBus:
    """Mock simple de EventBus para componentes que lo requieren"""

    def __init__(self):
        self._handlers = {}
        self._debug = False

    def on(self, event, handler):
        """Suscribirse a un evento"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def emit(self, event, data=None):
        """Emitir un evento"""
        if self._debug:
            print(f"[MockEventBus] emit('{event}', {data})")

        if event in self._handlers:
            for handler in self._handlers[event]:
                handler(data)

    def enable_debug(self):
        self._debug = True


class MockAppState:
    """Mock simple de AppState para componentes que lo requieren"""

    def __init__(self):
        from UI.state.state_manager import StateVariable

        # Variables básicas
        self.hotel = StateVariable("Hotel Alvear Palace")
        self.habitacion = StateVariable("Superior King Room")
        self.fecha_entrada = StateVariable(datetime.today() + timedelta(days=1))
        self.fecha_salida = StateVariable(datetime.today() + timedelta(days=3))
        self.adultos = StateVariable(2)
        self.ninos = StateVariable(0)
        self.precio = StateVariable(250.00)

        # Datos Excel mock
        from Models.hotelExcel import HotelExcel, HabitacionExcel, PrecioExcel, Periodo

        self.hoteles_excel = [
            HotelExcel(
                nombre="Hotel Alvear Palace",
                habitaciones=[
                    HabitacionExcel(
                        nombre="Superior King Room",
                        precios=[
                            PrecioExcel(
                                periodo=Periodo(
                                    nombre="Temporada Alta",
                                    fecha_inicio=datetime(2026, 1, 1),
                                    fecha_fin=datetime(2026, 3, 31)
                                ),
                                precio_total=250.00
                            ),
                            PrecioExcel(
                                periodo=Periodo(
                                    nombre="Temporada Media",
                                    fecha_inicio=datetime(2026, 4, 1),
                                    fecha_fin=datetime(2026, 6, 30)
                                ),
                                precio_total=180.00
                            )
                        ]
                    ),
                    HabitacionExcel(
                        nombre="Deluxe Suite",
                        precios=[
                            PrecioExcel(
                                periodo=Periodo(
                                    nombre="Temporada Alta",
                                    fecha_inicio=datetime(2026, 1, 1),
                                    fecha_fin=datetime(2026, 3, 31)
                                ),
                                precio_total=450.00
                            )
                        ]
                    )
                ]
            )
        ]

        # Resultado comparación mock
        self.resultado_multiperiodo = None


def generar_datos_prueba(componente_nombre, datos_custom=None):
    """
    Genera datos de prueba según el tipo de componente

    Args:
        componente_nombre: Nombre del componente
        datos_custom: Dict con datos personalizados (opcional)

    Returns:
        Dict con datos de prueba
    """
    datos = {}

    # Datos por componente
    if componente_nombre == 'combo':
        datos = {
            'opciones': datos_custom.get('opciones', ['Opción A', 'Opción B', 'Opción C']) if datos_custom else ['Opción A', 'Opción B', 'Opción C'],
            'label': datos_custom.get('label', 'Seleccione:') if datos_custom else 'Seleccione:',
            'default': datos_custom.get('default', 'Opción A') if datos_custom else 'Opción A'
        }

    elif componente_nombre == 'fecha':
        datos = {
            'label': datos_custom.get('label', 'Fecha:') if datos_custom else 'Fecha:',
            'default': datos_custom.get('default', datetime.today() + timedelta(days=1)) if datos_custom else datetime.today() + timedelta(days=1)
        }

    elif componente_nombre == 'resultados':
        # Datos de ejemplo para TablaResultados
        from Models.comparacion import ResultadoComparacionMultiperiodo, ResultadoComparacionPeriodo, Match
        from Models.hotelExcel import Periodo

        periodos_data = datos_custom.get('periodos', 3) if datos_custom else 3
        discrepancias = datos_custom.get('discrepancias', 1) if datos_custom else 1

        resultados = []
        for i in range(periodos_data):
            tiene_discrepancia = i < discrepancias

            resultados.append(ResultadoComparacionPeriodo(
                periodo=Periodo(
                    nombre=f"Periodo {i+1}",
                    fecha_inicio=datetime(2026, 1 + i*2, 1),
                    fecha_fin=datetime(2026, 1 + i*2 + 1, 28)
                ),
                match=Match(
                    habitacion_web_nombre="Superior King Room",
                    habitacion_excel_nombre="Superior King Room",
                    precio_web=250.00 if not tiene_discrepancia else 280.00,
                    precio_excel=250.00,
                    coincide=not tiene_discrepancia,
                    score=1.0
                ) if True else None,  # Simular que siempre hay match
                scraping_exitoso=True,
                error=None
            ))

        datos['resultado_multiperiodo'] = ResultadoComparacionMultiperiodo(
            hotel="Hotel Alvear Palace",
            habitacion="Superior King Room",
            resultados_por_periodo=resultados,
            tiene_discrepancias=discrepancias > 0
        )

    return datos


def mostrar_info_componente(modulo_path, clase_nombre, componente_clase):
    """Muestra información del componente"""
    print(f"\n🎨 UI Preview - Componente: {clase_nombre}")
    print("━" * 80)
    print(f"\n📦 Cargando componente...")
    print(f"   Módulo: {modulo_path}")
    print(f"   Clase: {clase_nombre}")
    print("✅ Componente cargado\n")

    # Inspector de métodos
    metodos = [m for m in dir(componente_clase) if not m.startswith('_') or m == '_setup_ui']
    print(f"🔧 Métodos disponibles ({len(metodos)}):")
    for metodo in sorted(metodos)[:10]:  # Mostrar primeros 10
        print(f"   - {metodo}")
    if len(metodos) > 10:
        print(f"   ... y {len(metodos) - 10} más")

    # Herencia
    bases = [base.__name__ for base in componente_clase.__bases__]
    print(f"\n🧬 Hereda de: {', '.join(bases)}")
    print("\n" + "━" * 80)


def previsualizar_componente(nombre, datos_custom=None, mock_eventbus=True):
    """
    Crea ventana standalone con el componente

    Args:
        nombre: Nombre corto del componente
        datos_custom: Dict con datos personalizados (opcional)
        mock_eventbus: Si True, usa MockEventBus (default: True)
    """
    # Verificar que existe el componente
    if nombre not in COMPONENTES:
        print(f"❌ Error: Componente '{nombre}' no encontrado")
        print(f"\n📋 Componentes disponibles:")
        for key in sorted(COMPONENTES.keys()):
            print(f"   - {key}")
        return

    modulo_path, clase_nombre = COMPONENTES[nombre]

    try:
        # Importar componente dinámicamente
        modulo = importlib.import_module(modulo_path)
        componente_clase = getattr(modulo, clase_nombre)

        # Mostrar info
        mostrar_info_componente(modulo_path, clase_nombre, componente_clase)

        # Generar datos de prueba
        datos = generar_datos_prueba(nombre, datos_custom)

        if datos:
            print(f"\n🎯 Datos de prueba cargados:")
            for key, value in datos.items():
                if key != 'resultado_multiperiodo':  # No imprimir objeto completo
                    print(f"   - {key}: {value}")

        print(f"\n🪟 Abriendo ventana preview...")
        print("━" * 80)
        print("\n💡 Tips:")
        print("   - Interactúa con el componente para probarlo")
        print("   - Cierra la ventana cuando termines")
        print("   - Los cambios NO se guardan (es solo preview)")
        print("\n" + "━" * 80 + "\n")

        # Crear ventana standalone
        root = tk.Tk()
        root.title(f"Preview: {clase_nombre}")
        root.geometry("800x600")

        # Frame principal
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Instanciar componente
        # Algunos componentes requieren EventBus y AppState
        kwargs = {}

        # Revisar firma del constructor
        import inspect
        sig = inspect.signature(componente_clase.__init__)
        params = list(sig.parameters.keys())

        if 'event_bus' in params and mock_eventbus:
            kwargs['event_bus'] = MockEventBus()

        if 'estado_app' in params or 'state' in params:
            kwargs['estado_app'] = MockAppState()

        # Agregar datos específicos
        if nombre == 'combo' and 'opciones' in datos:
            kwargs['opciones'] = datos['opciones']
            if 'label' in datos:
                kwargs['label'] = datos['label']

        if nombre == 'fecha' and 'label' in datos:
            kwargs['label'] = datos['label']

        if nombre == 'resultados' and 'resultado_multiperiodo' in datos:
            # TablaResultados puede requerir set_value después de instanciar
            pass

        # Instanciar
        try:
            componente = componente_clase(main_frame, **kwargs)
            componente.pack(fill='both', expand=True)

            # Setear valores específicos después de instanciar
            if nombre == 'fecha' and 'default' in datos:
                if hasattr(componente, 'set_value'):
                    componente.set_value(datos['default'])

            if nombre == 'combo' and 'default' in datos:
                if hasattr(componente, 'set_value'):
                    componente.set_value(datos['default'])

            if nombre == 'resultados' and 'resultado_multiperiodo' in datos:
                if hasattr(componente, 'set_value'):
                    componente.set_value(datos['resultado_multiperiodo'])

        except Exception as e:
            print(f"\n⚠️  Error al instanciar componente: {e}")
            print(f"   Esto puede ocurrir si el componente requiere dependencias específicas")
            print(f"   Intenta con --mock-eventbus o ajusta los datos de prueba")

            # Mostrar error en la ventana
            error_label = ttk.Label(
                main_frame,
                text=f"❌ Error al instanciar componente:\n\n{str(e)}",
                foreground='red',
                justify='left'
            )
            error_label.pack(pady=20)

        # Mainloop
        root.mainloop()

        print("\n✅ Ventana cerrada. Preview finalizado.")

    except ImportError as e:
        print(f"❌ Error: No se pudo importar el módulo '{modulo_path}'")
        print(f"   Detalle: {e}")
        print(f"\n💡 Verifica que el módulo existe y el PYTHONPATH es correcto")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    # Parser de argumentos simple
    if len(sys.argv) < 2:
        print("❌ Error: Falta argumento 'componente'")
        print(f"\nUso: python {sys.argv[0]} [componente] [--datos JSON]\n")
        print("📋 Componentes disponibles:")
        for key in sorted(COMPONENTES.keys()):
            print(f"   - {key}")
        sys.exit(1)

    componente_nombre = sys.argv[1]

    # Parsear --datos si existe
    datos_custom = None
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if arg.startswith('--datos='):
                datos_json = arg.replace('--datos=', '')
                try:
                    datos_custom = json.loads(datos_json)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error al parsear --datos: {e}")
                    print(f"   Usando datos de prueba por defecto")

    # Ejecutar preview
    previsualizar_componente(componente_nombre, datos_custom)


if __name__ == '__main__':
    main()