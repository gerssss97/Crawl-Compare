"""Mide la opcion A' real: durante el drag, reemplazar todo el content_frame
por un placeholder plano (tkinter.Frame, 1 canvas) y restaurar al soltar.

Compara 3 escenarios en el mismo drag simulado:
  baseline    → content_frame visible (estado actual, 44 canvas)
  placeholder → content_frame oculto + tk.Frame plano del color de fondo
  destroy     → content_frame oculto, nada en su lugar (piso teorico)

Uso:  python resize_placeholder.py baseline
      python resize_placeholder.py placeholder
      python resize_placeholder.py destroy
"""
import sys, os, time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

escenario = sys.argv[1] if len(sys.argv) > 1 else "baseline"

import tkinter as tk
import customtkinter as ctk
from UI.interfaz_ctk import CrawlCompareGUI
from UI.styles import Colors

root = ctk.CTk()
app = CrawlCompareGUI(root)


def run_probe():
    root.update()
    root.update_idletasks()

    cf = app._content_frame

    # Resolver el color de fondo real (Colors.BACKGROUND puede ser tupla light/dark).
    bg = Colors.BACKGROUND
    if isinstance(bg, (tuple, list)):
        bg = bg[0]  # light mode

    placeholder = None
    if escenario in ("placeholder", "destroy"):
        cf.pack_forget()                     # saco el content_frame real
        if escenario == "placeholder":
            placeholder = tk.Frame(root, bg=bg)   # tk puro = 0 canvas CTk
            placeholder.pack(fill="both", expand=True)

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
    print(f"[{escenario}] frames={n}  avg={sum(tiempos)/n:.1f}ms  "
          f"peor={max(tiempos):.1f}ms  >16ms={sum(1 for t in tiempos if t>16)}/{n}")

    # Restaurar (simula soltar el borde) y medir el costo de ese unico restore.
    if escenario in ("placeholder", "destroy"):
        if placeholder is not None:
            placeholder.destroy()
        t0 = time.perf_counter()
        cf.pack(fill="both", expand=True)
        root.update_idletasks()
        root.update()
        print(f"[{escenario}] costo restore al soltar = {(time.perf_counter()-t0)*1000:.1f}ms")

    root.quit()
    root.destroy()


root.after(2500, run_probe)
root.mainloop()
