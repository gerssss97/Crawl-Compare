"""Mide el costo de re-layout durante un resize simulado de la ventana principal.

Levanta CrawlCompareGUI, simula un drag del borde (varios geometry() consecutivos)
y cronometra cuánto tarda Tk en resolver el layout (update_idletasks) en cada paso.
Si el layout es barato, los tiempos por frame son bajos (< ~16ms = 60fps).
Toma un screenshot al final para verificar que el layout 65/35 quedó intacto.
"""
import sys, os, time

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

import customtkinter as ctk
from UI.interfaz_ctk import CrawlCompareGUI

root = ctk.CTk()
app = CrawlCompareGUI(root)


def run_probe():
    root.update()
    root.update_idletasks()

    # Simular un drag horizontal del borde derecho: anchos crecientes y decrecientes.
    base_h = root.winfo_height()
    x = root.winfo_x()
    y = root.winfo_y()
    widths = list(range(1000, 1400, 25)) + list(range(1400, 1000, -25))

    tiempos = []
    for w in widths:
        root.geometry(f"{w}x{base_h}+{x}+{y}")
        t0 = time.perf_counter()
        root.update_idletasks()   # acá Tk resuelve el layout completo
        root.update()
        dt = (time.perf_counter() - t0) * 1000
        tiempos.append(dt)

    n = len(tiempos)
    avg = sum(tiempos) / n
    peor = max(tiempos)
    over16 = sum(1 for t in tiempos if t > 16)
    print(f"[resize-probe] frames={n}  avg={avg:.1f}ms  peor={peor:.1f}ms  "
          f"frames>16ms={over16}/{n}")
    print(f"[resize-probe] {'OK: resize fluido' if peor < 50 else 'LENTO: hay freeze'}")

    # Screenshot final para verificar el layout
    try:
        from PIL import ImageGrab
        root.geometry(f"1200x{base_h}+{x}+{y}")
        root.update()
        time.sleep(0.4)
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        out = os.path.join(base, '.claude', 'skills', 'scripts', 'resize_probe.png')
        ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh)).save(out)
        print(f"[resize-probe] screenshot: {out}")
    except Exception as e:
        print(f"[resize-probe] screenshot failed: {e}")

    root.quit()
    root.destroy()


root.after(2500, run_probe)
root.mainloop()
print("Done")