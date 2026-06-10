"""Compara el costo de resize segun el preferred_drawing_method de CTk.

CTk dibuja las esquinas redondeadas de cada widget sobre un canvas. El metodo
de dibujo (font_shapes / polygon_shapes / circle_shapes) cambia cuanto cuesta
ese redibujo. font_shapes (default Windows) rasteriza glifos antialiased = caro.
Este script mide el mismo drag simulado con cada metodo, SIN tocar corner_radius
(las esquinas siguen redondeadas). Toma el metodo del argv.

Uso:  python resize_drawmethod.py font_shapes
      python resize_drawmethod.py polygon_shapes
      python resize_drawmethod.py circle_shapes
"""
import sys, os, time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

metodo = sys.argv[1] if len(sys.argv) > 1 else "font_shapes"

# CRITICO: setear el metodo ANTES de instanciar cualquier widget CTk.
from customtkinter.windows.widgets.core_rendering.draw_engine import DrawEngine
DrawEngine.preferred_drawing_method = metodo

import customtkinter as ctk
from UI.interfaz_ctk import CrawlCompareGUI

root = ctk.CTk()
app = CrawlCompareGUI(root)


def run_probe():
    root.update()
    root.update_idletasks()

    base_h = root.winfo_height()
    x, y = root.winfo_x(), root.winfo_y()
    widths = list(range(1000, 1400, 25)) + list(range(1400, 1000, -25))

    tiempos = []
    for w in widths:
        root.geometry(f"{w}x{base_h}+{x}+{y}")
        t0 = time.perf_counter()
        root.update_idletasks()
        root.update()
        tiempos.append((time.perf_counter() - t0) * 1000)

    n = len(tiempos)
    print(f"[{metodo}] frames={n}  avg={sum(tiempos)/n:.1f}ms  "
          f"peor={max(tiempos):.1f}ms  >16ms={sum(1 for t in tiempos if t>16)}/{n}")

    root.quit()
    root.destroy()


root.after(2500, run_probe)
root.mainloop()
