#!/usr/bin/env python
"""
multiperiodo_test.py - Test multi-periodo con datos fake o scraping real

Uso:
    python multiperiodo_test.py [--modo fake|real] [--hotel HOTEL] [--habitacion HAB]

Ejemplos:
    python multiperiodo_test.py
    python multiperiodo_test.py --modo fake --hotel "Alvear Palace" --habitacion "dbl superior"
    python multiperiodo_test.py --modo real
"""

import sys
import os
import argparse
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date, datetime

# Agregar Hoteles/ al path
# El script está en .claude/skills/scripts/, necesitamos subir 3 niveles para llegar a la raíz
hoteles_dir = Path(__file__).parent.parent.parent.parent / "Hoteles"
sys.path.insert(0, str(hoteles_dir))

# Cambiar working directory a Hoteles/ para que los paths relativos funcionen
os.chdir(str(hoteles_dir))

from Core.controller import dar_hoteles_excel, generar_texto_email_multiperiodo
from Core.comparador_multiperiodo import comparar_multiperiodo, ResultadoComparacionMultiperiodo
from Core.servicio_habitaciones import inferir_periodos_desde_fechas, unificar_habitaciones
from Models.hotelWeb import HabitacionWeb, ComboPrecio
from Models.habitacion_unificada import HabitacionUnificada
from UI.views.vista_resultados import VistaResultados
from UI.styles.fonts import FontManager


class MultiperiodoTestUI:
    """UI Tkinter para inventar datos web por periodo."""

    def __init__(self, habitacion_unificada, hotel, periodos_aplicables):
        """
        Inicializa la UI de test.

        Args:
            habitacion_unificada: HabitacionUnificada desde Excel
            hotel: HotelExcel completo
            periodos_aplicables: List[Periodo] aplicables a esta habitación
        """
        self.habitacion_unificada = habitacion_unificada
        self.hotel = hotel
        self.periodos_aplicables = periodos_aplicables
        self.resultado = None  # Guardará el resultado de la comparación

        # Crear ventana
        self.root = tk.Tk()
        self.root.title("Test Multi-Periodo - Inventar Datos Web")
        self.root.geometry("600x500")

        # Variables
        self.nombre_web_var = tk.StringVar(value="Double Superior Room with Breakfast")
        self.precio_vars = {}  # {periodo.id: tk.DoubleVar}

        self._setup_ui()

    def _setup_ui(self):
        """Construye la interfaz."""
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Header
        header_label = ttk.Label(
            main_frame,
            text=f"Inventar Datos Web - {self.habitacion_unificada.nombre}",
            font=("Helvetica", 14, "bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Info de periodos
        info_label = ttk.Label(
            main_frame,
            text=f"Periodos aplicables: {len(self.periodos_aplicables)}",
            font=("Helvetica", 10)
        )
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)

        # Nombre de habitación web
        ttk.Label(main_frame, text="Habitación Web:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.nombre_web_var, width=50).grid(row=3, column=1, sticky='w', pady=5)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)

        # Frame scrollable para periodos
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        canvas = tk.Canvas(canvas_frame, height=200)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Loop dinámico: inputs por cada periodo
        for i, periodo in enumerate(self.periodos_aplicables):
            # Label del periodo
            nombre = periodo.nombre if periodo.nombre else f"Periodo {periodo.id}"
            periodo_label = ttk.Label(
                scrollable_frame,
                text=f"{nombre} ({periodo.fecha_inicio.strftime('%d/%m')}-{periodo.fecha_fin.strftime('%d/%m')})",
                font=("Helvetica", 9)
            )
            periodo_label.grid(row=i, column=0, sticky='w', padx=5, pady=3)

            # Entry del precio
            precio_var = tk.DoubleVar(value=150.0)  # Default: $150
            self.precio_vars[periodo.id] = precio_var

            precio_entry = ttk.Entry(scrollable_frame, textvariable=precio_var, width=15)
            precio_entry.grid(row=i, column=1, sticky='w', padx=5, pady=3)

            # Label "USD"
            ttk.Label(scrollable_frame, text="USD").grid(row=i, column=2, sticky='w', padx=2, pady=3)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)

        # Botón generar
        generar_btn = ttk.Button(
            main_frame,
            text="Generar Comparación",
            command=self._generar_comparacion,
            style="Accent.TButton"
        )
        generar_btn.grid(row=7, column=0, columnspan=2, pady=10)

        # Configurar grid weights para expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def _generar_comparacion(self):
        """Genera la comparación con los datos inventados."""
        nombre_web = self.nombre_web_var.get().strip()

        if not nombre_web:
            messagebox.showerror("Error", "Debe ingresar un nombre para la habitación web")
            return

        print("\n🎯 Datos Web Inventados:")
        print(f"   Habitación web: \"{nombre_web}\"\n")

        # Crear ComboPrecio por cada periodo
        combos = []
        for periodo in self.periodos_aplicables:
            precio = self.precio_vars[periodo.id].get()
            nombre = periodo.nombre if periodo.nombre else f"Periodo {periodo.id}"
            print(f"   Periodo {periodo.id} ({nombre}): ${precio:.2f}")

            combos.append(ComboPrecio(
                titulo=nombre_web,
                descripcion=f"Inventado para testing - {nombre}",
                precio=precio
            ))

        # Crear HabitacionWeb fake
        habitacion_web = HabitacionWeb(
            nombre=nombre_web,
            detalles="Habitación inventada para testing multi-periodo",
            combos=combos
        )

        print("\n⚙️  Ejecutando comparación...")

        # Ejecutar comparación multi-periodo
        # Nota: En modo fake, no hacemos scraping real, solo fuzzy matching + comparación
        try:
            # Para ejecutar la comparación necesitamos fechas
            # Usamos las fechas de los periodos aplicables
            fecha_entrada = self.periodos_aplicables[0].fecha_inicio
            fecha_salida = self.periodos_aplicables[-1].fecha_fin

            # Crear un resultado "fake" usando la estructura esperada
            from Core.comparador_multiperiodo import ResultadoPeriodo

            resultados_periodos = []
            tiene_discrepancias = False

            for periodo in self.periodos_aplicables:
                # Obtener precio Excel del periodo
                precio_excel = self.habitacion_unificada.precio_para_periodo(periodo.id)

                # Obtener precio web del combo correspondiente
                nombre = periodo.nombre if periodo.nombre else f"Periodo {periodo.id}"
                combo_periodo = next((c for c in combos if nombre in c.descripcion), None)
                precio_web = combo_periodo.precio if combo_periodo else 0.0

                # Calcular diferencia
                if isinstance(precio_excel, (int, float)):
                    diferencia = precio_web - precio_excel
                    coincide = abs(diferencia) < 1.0
                else:
                    # Precio es leyenda
                    diferencia = 0.0
                    coincide = True

                if not coincide:
                    tiene_discrepancias = True

                # Calcular fechas específicas (en modo fake, usamos las del periodo completo)
                fecha_inicio_real = periodo.fecha_inicio
                fecha_fin_real = periodo.fecha_fin

                resultados_periodos.append(ResultadoPeriodo(
                    periodo=periodo,
                    precio_excel=precio_excel,
                    precio_web=precio_web,
                    diferencia=diferencia,
                    coincide=coincide,
                    fecha_inicio_real=fecha_inicio_real,
                    fecha_fin_real=fecha_fin_real
                ))

            # Crear resultado completo
            self.resultado = ResultadoComparacionMultiperiodo(
                habitacion_excel_nombre=self.habitacion_unificada.nombre,
                habitacion_web_matcheada=habitacion_web,
                periodos=resultados_periodos,
                tiene_discrepancias=tiene_discrepancias,
                mensaje_match=f"Match manual: {nombre_web}"
            )

            # Mostrar resultados en consola
            print("\n✅ Resultados:\n")
            self._imprimir_tabla_comparativa(self.resultado)

            # Mostrar resultados en ventana visual (igual que en la app)
            self._mostrar_vista_resultados(self.resultado)

            # Generar email
            texto_email = generar_texto_email_multiperiodo(self.hotel, self.resultado)

            # Guardar email en archivo
            tmp_dir = Path(__file__).parent.parent.parent / "tmp"
            tmp_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            email_file = tmp_dir / f"multiperiodo-test-email-{timestamp}.txt"

            with open(email_file, "w", encoding="utf-8") as f:
                f.write(texto_email)

            print(f"\n💾 Email guardado en: {email_file}")

            # Mostrar email en ventana
            self._mostrar_email(texto_email)

            # Cerrar ventana de datos
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error durante comparación:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _imprimir_tabla_comparativa(self, resultado):
        """Imprime tabla comparativa en consola."""
        print("┌" + "─" * 14 + "┬" + "─" * 13 + "┬" + "─" * 12 + "┬" + "─" * 13 + "┬" + "─" * 8 + "┐")
        print(f"│ {'Periodo':<12} │ {'Precio Excel':<11} │ {'Precio Web':<10} │ {'Diferencia':<11} │ {'Estado':<6} │")
        print("├" + "─" * 14 + "┼" + "─" * 13 + "┼" + "─" * 12 + "┼" + "─" * 13 + "┼" + "─" * 8 + "┤")

        for res_periodo in resultado.periodos:
            # Manejar caso cuando nombre es None o vacío
            nombre = res_periodo.periodo.nombre if res_periodo.periodo.nombre else f"Periodo {res_periodo.periodo.id}"
            periodo_nombre = nombre[:12]

            if isinstance(res_periodo.precio_excel, (int, float)):
                precio_excel_str = f"${res_periodo.precio_excel:.2f}"
            else:
                precio_excel_str = str(res_periodo.precio_excel)[:11]

            precio_web_str = f"${res_periodo.precio_web:.2f}"
            diferencia_str = f"${res_periodo.diferencia:.2f}"
            estado_str = "✅ OK" if res_periodo.coincide else "❌ DIFF"

            print(f"│ {periodo_nombre:<12} │ {precio_excel_str:<11} │ {precio_web_str:<10} │ {diferencia_str:<11} │ {estado_str:<6} │")

        print("└" + "─" * 14 + "┴" + "─" * 13 + "┴" + "─" * 12 + "┴" + "─" * 13 + "┴" + "─" * 8 + "┘")

    def _mostrar_vista_resultados(self, resultado):
        """Muestra resultados en ventana visual usando VistaResultados."""
        resultados_window = tk.Toplevel()
        resultados_window.title("Vista de Resultados (igual que en la app)")
        resultados_window.geometry("900x600")

        # Label header
        header = ttk.Label(
            resultados_window,
            text="📊 Vista de Resultados - Preview",
            font=("Helvetica", 12, "bold")
        )
        header.pack(pady=10)

        # Crear FontManager
        fonts = FontManager(resultados_window)

        # Crear VistaResultados
        vista = VistaResultados(resultados_window, fonts=fonts)
        vista.pack(fill='both', expand=True, padx=10, pady=10)

        # Mostrar resultado
        vista.mostrar_resultado_multiperiodo(resultado)

        # Botón cerrar
        close_btn = ttk.Button(resultados_window, text="Cerrar", command=resultados_window.destroy)
        close_btn.pack(pady=10)

    def _mostrar_email(self, texto_email):
        """Muestra email en ventana Text."""
        email_window = tk.Toplevel()
        email_window.title("Email Generado (NO enviado)")
        email_window.geometry("700x500")

        # Label header
        header = ttk.Label(
            email_window,
            text="📧 Email generado - NO se enviará",
            font=("Helvetica", 12, "bold")
        )
        header.pack(pady=10)

        # Text widget con scrollbar
        text_frame = ttk.Frame(email_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap='word')
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)

        # Insertar texto
        text_widget.insert('1.0', texto_email)

        # Botón cerrar
        close_btn = ttk.Button(email_window, text="Cerrar", command=email_window.destroy)
        close_btn.pack(pady=10)

    def run(self):
        """Ejecuta la UI."""
        self.root.mainloop()


def modo_fake(hotel_nombre, habitacion_nombre):
    """Ejecuta test en modo fake (inventar datos)."""
    print("\n🧪 Test Multi-Periodo - Modo FAKE\n")

    # Cargar datos de Excel
    print("📂 Cargando datos de Excel...")
    hoteles_excel = dar_hoteles_excel()

    # Buscar hotel
    hotel = None
    for h in hoteles_excel:
        if hotel_nombre.lower() in h.nombre.lower():
            hotel = h
            break

    if not hotel:
        print(f"❌ Error: No se encontró hotel '{hotel_nombre}'")
        print(f"Hoteles disponibles: {', '.join([h.nombre for h in hoteles_excel])}")
        sys.exit(1)

    print(f"✅ Hotel cargado: {hotel.nombre}")

    # Recolectar TODAS las habitaciones de TODOS los tipos
    todas_habitaciones = []
    for tipo in hotel.tipos:
        todas_habitaciones.extend(tipo.habitaciones)

    # También agregar habitaciones directas si hay
    todas_habitaciones.extend(hotel.habitaciones_directas)

    print(f"📊 Total de habitaciones encontradas: {len(todas_habitaciones)}")

    # Buscar habitación unificada
    habitaciones_unificadas = unificar_habitaciones(todas_habitaciones)
    print(f"📊 Habitaciones unificadas: {len(habitaciones_unificadas)}")

    habitacion_unificada = None

    for hab_unif in habitaciones_unificadas:
        if habitacion_nombre.lower() in hab_unif.nombre.lower():
            habitacion_unificada = hab_unif
            break

    if not habitacion_unificada:
        print(f"❌ Error: No se encontró habitación '{habitacion_nombre}'")
        print(f"\nHabitaciones disponibles ({len(habitaciones_unificadas)} total):")
        for i, h in enumerate(habitaciones_unificadas[:20], start=1):
            print(f"  {i}. {h.nombre}")
        if len(habitaciones_unificadas) > 20:
            print(f"  ... y {len(habitaciones_unificadas) - 20} más")
        sys.exit(1)

    print(f"✅ Habitación cargada: {habitacion_unificada.nombre}")

    # Obtener periodos aplicables (todos los de la habitación)
    periodos_aplicables = []
    todos_periodo_ids = habitacion_unificada.todos_los_periodos()
    for periodo_id in todos_periodo_ids:
        periodo = hotel.periodo_por_id(periodo_id)
        if periodo:
            periodos_aplicables.append(periodo)

    if not periodos_aplicables:
        print(f"❌ Error: La habitación no tiene periodos asociados")
        sys.exit(1)

    print(f"✅ Periodos aplicables: {len(periodos_aplicables)}\n")

    # Mostrar info de periodos
    for p in periodos_aplicables:
        nombre = p.nombre if p.nombre else f"Periodo {p.id}"
        print(f"   - {nombre} ({p.fecha_inicio.strftime('%d/%m')}-{p.fecha_fin.strftime('%d/%m')})")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Abriendo UI para inventar datos web...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Abrir UI
    ui = MultiperiodoTestUI(habitacion_unificada, hotel, periodos_aplicables)
    ui.run()


def modo_real(hotel_nombre, habitacion_nombre):
    """Ejecuta test en modo real (scraping de verdad)."""
    print("\n🧪 Test Multi-Periodo - Modo REAL\n")
    print("⚠️  Modo real no implementado todavía.")
    print("Este modo requeriría:")
    print("  1. Pedir fechas de reserva al usuario")
    print("  2. Ejecutar scraping real con force_fresh=True")
    print("  3. Ejecutar comparar_multiperiodo() completo")
    print("\nUsa --modo fake por ahora.")


def main():
    parser = argparse.ArgumentParser(description="Test multi-periodo con datos fake o real")
    parser.add_argument("--modo", choices=["fake", "real"], default="fake", help="Modo de test (default: fake)")
    parser.add_argument("--hotel", default=None, help="Nombre del hotel (default: primer hotel del Excel)")
    parser.add_argument("--habitacion", default=None, help="Nombre de habitación (default: primera habitación)")

    args = parser.parse_args()

    # Defaults
    hotel_nombre = args.hotel or "Alvear Palace"
    habitacion_nombre = args.habitacion or "dbl superior"

    if args.modo == "fake":
        modo_fake(hotel_nombre, habitacion_nombre)
    else:
        modo_real(hotel_nombre, habitacion_nombre)


if __name__ == "__main__":
    main()
