import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from network import WeatherClient
from constants import CITIES, C_BG, C_SURFACE, C_CARD, C_BORDER, C_TEXT, C_MUTED, C_ACCENT, C_ACCENT_HOVER, C_SUCCESS

class WeatherRemoteGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Пульт управления")
        self.root.geometry("450x680")
        self.root.minsize(420, 620)
        self.root.configure(bg=C_BG)

        self.client = None
        self.connected = False

        self._build_ui()

    def _build_ui(self):
        conn_frame = tk.LabelFrame(
            self.root,
            text=" Подключение к серверу",
            font=("Segoe UI", 10, "bold"),
            bg=C_SURFACE,
            fg=C_TEXT,
            padx=14,
            pady=10,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            relief="flat",
        )
        conn_frame.pack(fill="x", padx=16, pady=(16, 10))

        row1 = tk.Frame(conn_frame, bg=C_SURFACE)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="IP адрес:", font=("Segoe UI", 10), bg=C_SURFACE, fg=C_MUTED).pack(side="left")
        self.entry_ip = tk.Entry(
            row1,
            font=("Segoe UI", 10, "bold"),
            bg=C_CARD,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            bd=6,
            width=16,
        )
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(side="left", padx=8)

        tk.Label(row1, text="Порт:", font=("Segoe UI", 10), bg=C_SURFACE, fg=C_MUTED).pack(side="left")
        self.entry_port = tk.Entry(
            row1,
            font=("Segoe UI", 10),
            bg=C_CARD,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            bd=6,
            width=6,
        )
        self.entry_port.insert(0, "8888")
        self.entry_port.pack(side="left", padx=4)

        row2 = tk.Frame(conn_frame, bg=C_SURFACE)
        row2.pack(fill="x", pady=(8, 2))

        self.btn_connect = tk.Button(
            row2,
            text="Подключиться",
            font=("Segoe UI", 10, "bold"),
            bg=C_ACCENT,
            fg="white",
            activebackground=C_ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.toggle_connection,
        )
        self.btn_connect.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.lbl_conn_status = tk.Label(
            row2,
            text="Отключено",
            font=("Segoe UI", 9, "bold"),
            bg=C_SURFACE,
            fg="#ef4444",
        )
        self.lbl_conn_status.pack(side="right", padx=6)

        city_frame = tk.LabelFrame(
            self.root,
            text="Переключение города ",
            font=("Segoe UI", 10, "bold"),
            bg=C_SURFACE,
            fg=C_TEXT,
            padx=14,
            pady=10,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            relief="flat",
        )
        city_frame.pack(fill="x", padx=16, pady=(0, 10))

        search_row = tk.Frame(city_frame, bg=C_SURFACE)
        search_row.pack(fill="x", pady=(0, 8))

        self.entry_city = tk.Entry(
            search_row,
            font=("Segoe UI", 11),
            bg=C_CARD,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            bd=6,
        )
        self.entry_city.insert(0, "Казань")
        self.entry_city.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_city.bind("<Return>", lambda e: self.send_city())

        self.btn_send_city = tk.Button(
            search_row,
            text="Вывести",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.send_city,
        )
        self.btn_send_city.pack(side="right")

        tk.Label(
            city_frame,
            text="Быстрые кнопки для отправки:",
            font=("Segoe UI", 9),
            bg=C_SURFACE,
            fg=C_MUTED,
        ).pack(anchor="w", pady=(2, 4))

        quick_grid = tk.Frame(city_frame, bg=C_SURFACE)
        quick_grid.pack(fill="x")
        for i, c in enumerate(CITIES):
            row = i // 4
            col = i % 4
            quick_grid.columnconfigure(col, weight=1)
            b = tk.Button(
                quick_grid,
                text=c,
                font=("Segoe UI", 8),
                bg=C_CARD,
                fg=C_TEXT,
                activebackground=C_BORDER,
                relief="flat",
                bd=0,
                padx=4,
                pady=4,
                cursor="hand2",
                command=lambda name=c: self.send_quick_city(name),
            )
            b.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

        ctrl_frame = tk.LabelFrame(
            self.root,
            text="Команды:",
            font=("Segoe UI", 10, "bold"),
            bg=C_SURFACE,
            fg=C_TEXT,
            padx=14,
            pady=10,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            relief="flat",
        )
        ctrl_frame.pack(fill="x", padx=16, pady=(0, 10))

        ctrl_row = tk.Frame(ctrl_frame, bg=C_SURFACE)
        ctrl_row.pack(fill="x")

        self.btn_toggle_unit = tk.Button(
            ctrl_row,
            text="Переключить °C / °F",
            font=("Segoe UI", 9, "bold"),
            bg=C_CARD,
            fg=C_TEXT,
            activebackground=C_BORDER,
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.send_toggle_unit,
        )
        self.btn_toggle_unit.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_get_status = tk.Button(
            ctrl_row,
            text="Запросить данные",
            font=("Segoe UI", 9, "bold"),
            bg=C_CARD,
            fg=C_TEXT,
            activebackground=C_BORDER,
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.send_get_status,
        )
        self.btn_get_status.pack(side="right", fill="x", expand=True, padx=(4, 0))

        msg_frame = tk.LabelFrame(
            self.root,
            text="Отправить текст на экран",
            font=("Segoe UI", 10, "bold"),
            bg=C_SURFACE,
            fg=C_TEXT,
            padx=14,
            pady=10,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            relief="flat",
        )
        msg_frame.pack(fill="x", padx=16, pady=(0, 10))

        msg_row = tk.Frame(msg_frame, bg=C_SURFACE)
        msg_row.pack(fill="x")

        self.entry_msg = tk.Entry(
            msg_row,
            font=("Segoe UI", 10),
            bg=C_CARD,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            bd=6,
        )
        self.entry_msg.insert(0, "Тестовое сообщение")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_msg.bind("<Return>", lambda e: self.send_alert())

        self.btn_send_msg = tk.Button(
            msg_row,
            text="📢 Послать",
            font=("Segoe UI", 9, "bold"),
            bg="#d97706",
            fg="white",
            activebackground="#b45309",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.send_alert,
        )
        self.btn_send_msg.pack(side="right")

        log_frame = tk.Frame(self.root, bg=C_BG)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tk.Label(
            log_frame,
            text="Телеметрия:",
            font=("Segoe UI", 9, "bold"),
            bg=C_BG,
            fg=C_MUTED,
        ).pack(anchor="w", pady=(0, 4))

        self.txt_log = tk.Text(
            log_frame,
            font=("Consolas", 9),
            bg=C_SURFACE,
            fg="#38bdf8",
            insertbackground=C_TEXT,
            relief="flat",
            bd=6,
            height=6,
            wrap="word",
        )
        self.txt_log.pack(fill="both", expand=True)
        self.log("Пульт готов к работе. Нажмите 'Подключиться'.")

    def log(self, text, tag=None):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("end", f"[{time_str}] {text}\n")
        self.txt_log.see("end")

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        host = self.entry_ip.get().strip() or "127.0.0.1"
        try:
            port = int(self.entry_port.get().strip())
        except ValueError:
            port = 8888

        self.log(f"Подключение к {host}:{port}...")
        self.btn_connect.config(state="disabled")

        def _do_connect():
            try:
                self.client = WeatherClient(host=host, port=port, timeout=4)
                self.client.connect()
                resp = self.client.send_command({"cmd": "ping"})
                if resp.get("status") == "ok":
                    self.root.after(0, self._on_connect_success, host, port)
                else:
                    self.root.after(0, self._on_connect_fail, f"Неожиданный ответ: {resp}")
            except Exception as err:
                self.root.after(0, self._on_connect_fail, str(err))

        threading.Thread(target=_do_connect, daemon=True).start()

    def _on_connect_success(self, host, port):
        self.connected = True
        self.btn_connect.config(state="normal", text="Отключиться", bg="#dc2626", activebackground="#b91c1c")
        self.lbl_conn_status.config(text="● Онлайн", fg=C_SUCCESS)
        self.log(f"✅ Успешно подключено к экрану {host}:{port}")

    def _on_connect_fail(self, error):
        self.connected = False
        self.btn_connect.config(state="normal", text="⚡ Подключиться", bg=C_ACCENT, activebackground=C_ACCENT_HOVER)
        self.lbl_conn_status.config(text="● Ошибка", fg="#ef4444")
        self.log(f"❌ Ошибка соединения: {error}")
        messagebox.showerror(
            "Ошибка подключения",
            f"Не удалось подключиться к экрану! \n\nПричина: {error}\n\n1. Запущен ли server.py?\n2. Правильно ли указан IP адрес?",
        )

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
        self.connected = False
        self.btn_connect.config(text="⚡ Подключиться", bg=C_ACCENT, activebackground=C_ACCENT_HOVER)
        self.lbl_conn_status.config(text="● Отключено", fg="#ef4444")
        self.log("Пульт отключен от сервера.")

    def _send(self, payload, success_callback=None):
        if not self.connected or not self.client:
            messagebox.showwarning("Внимание", "Сначала подключитесь к экрану!")
            return

        def _worker():
            try:
                resp = self.client.send_command(payload)
                self.root.after(0, self._handle_response, resp, success_callback)
            except Exception as err:
                self.root.after(0, self.log, f"❌ Ошибка отправки: {err}")

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_response(self, resp, callback):
        msg = resp.get("message", "OK")
        self.log(f"Ответ экрана: {msg}")
        if callback:
            callback(resp)

    def send_city(self):
        city = self.entry_city.get().strip()
        if not city:
            return
        self.log(f"Отправка команды: сменить город на '{city}'...")
        self._send({"cmd": "set_city", "city": city})

    def send_quick_city(self, city):
        self.entry_city.delete(0, "end")
        self.entry_city.insert(0, city)
        self.send_city()

    def send_toggle_unit(self):
        self.log("Отправка команды: переключить шкалу (°C / °F)...")
        self._send({"cmd": "toggle_unit"})

    def send_get_status(self):
        self.log("Запрос текущего состояния экрана по сети...")

        def _show_status(resp):
            if resp.get("status") == "ok":
                info = (
                    f"📊 Данные с экрана:\n"
                    f"   Город: {resp.get('city')}\n"
                    f"   Температура: {resp.get('temp')}\n"
                    f"   Погода: {resp.get('condition')}\n"
                    f"   Влажность: {resp.get('humidity')} | Ветер: {resp.get('wind')}\n"
                    f"   Давление: {resp.get('pressure')}"
                )
                self.log(info)

        self._send({"cmd": "get_status"}, _show_status)

    def send_alert(self):
        text = self.entry_msg.get().strip()
        if not text:
            return
        self.log(f"Отправка сообщения на экран: '{text}'...")
        self._send({"cmd": "alert", "text": text})


def main():
    root = tk.Tk()
    app = WeatherRemoteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
