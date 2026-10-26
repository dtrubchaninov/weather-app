import tkinter as tk
from ui import DesktopWeatherApp


def main():
    root = tk.Tk()
    app = DesktopWeatherApp(root, enable_network=True, port=8888)
    root.mainloop()


if __name__ == "__main__":
    main()
