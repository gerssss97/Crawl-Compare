"""Mide el impacto de ocultar subarboles durante el resize (opcion A').

Corre el mismo drag simulado en 3 escenarios y compara tiempo/frame:
  baseline  → nada oculto (estado actual)
  der       → oculto el panel derecho durante el drag (grid_remove)
  ambos     → oculto panel izq + der, queda solo header

Tambien cuenta cuantos de los CTkFrame son contenedores transparentes
aplanables (techo de la opcion E) para descartarla/confirmarla con numero.

Uso:  python resize_subtree.py baseline
      python resize_subtree.py der
      python resize_subtree.py ambos
"""
import sys, os, time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

escenario = sys.argv[1] if len(sys.argv) > 1 else "baseline"

import customtkinter as ctk
from UI.interfaz_ctk import CrawlCompareGUI

root = ctk.CTk()
app = CrawlCompareGUI(root)


def _contar_aplanables():
    """Cuenta CTkFrame con fg_color='transparent' y corner_radius 0 (techo de opcion E)."""
    total_canvas = 0
    aplanables = 0
    stack = [root]
    while stack:
        w = stack.pop()
        cls = w.__class__.__name__
        if cls in ("CTkCanvas", "Canvas"):
            total_canvas += 1
        if cls == "CTkFrame":
            try:
                fg = w.cget("fg_color")
                cr = w.cget("corner_radius")
                if (fg == "transparent" or fg is None) and (cr == 0):
                    aplanables += 1
            except Exception:
                pass
        stack.extend(w.winfo_children())
    return total_canvas, aplanables


def _paneles_del_content():
    """Devuelve (panel_col0, panel_col1) buscando en el grid del content_frame."""
    cf = app._content_frame
    col0 = col1 = None
    for child in cf.winfo_children():
        info = child.grid_info()
        if not info:
            continue
        if str(info.get("column")) == "0":
            col0 = child
        elif str(info.get("column")) == "1":
            col1 = child
    return col0, col1


def run_probe():
    root.update()
    root.update_idletasks()

    total_canvas, aplanables = _contar_aplanables()
    col0, col1 = _paneles_del_content()

    # Aplicar el escenario: ocultar subarboles ANTES del drag.
    if escenario in ("der", "ambos") and col1 is not None:
        col1.grid_remove()
    if escenario == "ambos" and col0 is not None:
        col0.grid_remove()

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
    print(f"[E-techo] canvas_totales={total_canvas}  CTkFrame_aplanables={aplanables}")

    root.quit()
    root.destroy()


root.after(2500, run_probe)
root.mainloop()
