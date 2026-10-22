from ui import DesktopWeatherApp
import sys
import tkinter as tk


if sys.platform.startswith("win"):
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

def main():
    root = tk.Tk()
    app = DesktopWeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
