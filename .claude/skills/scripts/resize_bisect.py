"""Bisección del costo de re-layout en resize.

Mismo drag simulado que resize_probe.py, pero ademas instrumenta TODOS los
CTkScrollableFrame de la ventana para contar cuantos eventos <Configure> se
disparan por frame y cuanto tarda cada widget. Asi identificamos cual es el caro.
"""
import sys, os, time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

import customtkinter as ctk
import tkinter as tk
from UI.interfaz_ctk import CrawlCompareGUI

root = ctk.CTk()
app = CrawlCompareGUI(root)

# Contador global de eventos <Configure> por tipo de widget.
configure_counts = {}


def _walk(widget, depth=0):
    """Recorre el arbol de widgets y reporta los CTkScrollableFrame + canvas."""
    cls = widget.__class__.__name__
    yield widget, cls, depth
    for child in widget.winfo_children():
        yield from _walk(child, depth + 1)


def run_probe():
    root.update()
    root.update_idletasks()

    # Inventario: cuantos scrollables / canvas hay vivos.
    scrollables = []
    canvases = []
    for w, cls, d in _walk(root):
        if "ScrollableFrame" in cls:
            scrollables.append((cls, d))
        if cls == "CTkCanvas" or cls == "Canvas":
            canvases.append((cls, d))
    print(f"[bisect] CTkScrollableFrame vivos: {len(scrollables)}")
    for cls, d in scrollables:
        print(f"         - {cls} (depth {d})")
    print(f"[bisect] Canvas vivos: {len(canvases)}")

    # Instrumentar: contar <Configure> globalmente con bind_all.
    counter = {"n": 0}

    def _count(_e):
        counter["n"] += 1

    root.bind_all("<Configure>", _count, add="+")

    base_h = root.winfo_height()
    x, y = root.winfo_x(), root.winfo_y()
    widths = list(range(1000, 1400, 25)) + list(range(1400, 1000, -25))

    tiempos = []
    eventos = []
    for w in widths:
        counter["n"] = 0
        root.geometry(f"{w}x{base_h}+{x}+{y}")
        t0 = time.perf_counter()
        root.update_idletasks()
        root.update()
        dt = (time.perf_counter() - t0) * 1000
        tiempos.append(dt)
        eventos.append(counter["n"])

    n = len(tiempos)
    print(f"[bisect] frames={n}  avg={sum(tiempos)/n:.1f}ms  peor={max(tiempos):.1f}ms")
    print(f"[bisect] <Configure> por frame: avg={sum(eventos)/n:.1f}  "
          f"peor={max(eventos)}  total={sum(eventos)}")

    root.quit()
    root.destroy()


root.after(2500, run_probe)
root.mainloop()
print("Done")
