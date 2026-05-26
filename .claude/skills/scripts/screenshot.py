import sys, os

base = r'C:\Users\German Lucero\ProyectosChino\Crawl-Compare'
hoteles_dir = os.path.join(base, 'Hoteles')
sys.path.insert(0, base)
sys.path.insert(0, hoteles_dir)
os.chdir(hoteles_dir)

import customtkinter as ctk

try:
    from UI.interfaz_ctk import CrawlCompareGUI
    root = ctk.CTk()
    app = CrawlCompareGUI(root)

    def take_screenshot_and_quit():
        root.update()
        root.lift()
        root.focus_force()
        root.update()
        import time; time.sleep(0.5)
        try:
            from PIL import ImageGrab
            x = root.winfo_rootx()
            y = root.winfo_rooty()
            w = root.winfo_width()
            h = root.winfo_height()
            screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            out = os.path.join(base, '.claude', 'skills', 'scripts', 'app_screenshot.png')
            screenshot.save(out)
            print(f'Screenshot saved to {out}')
        except Exception as e:
            print(f'Screenshot failed: {e}')
            import traceback; traceback.print_exc()
        root.quit()
        root.destroy()

    root.after(3000, take_screenshot_and_quit)
    root.mainloop()
    print('Done')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
