import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from utils import get_wind_direction_ru, format_temp
from api import fetch_weather_data

from constants import (
    WMO_CODES,
    C_BG,
    C_SURFACE,
    C_CARD,
    C_BORDER,
    C_TEXT,
    C_MUTED,
    C_ACCENT,
    C_ACCENT_HOVER,
    C_SUCCESS,
    CITIES,
    DAYS_RU,
)

class DesktopWeatherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Погода • Настольное приложение Python")
        self.root.geometry("820x680")
        self.root.minsize(740, 600)

        self.c_bg = C_BG
        self.c_surface = C_SURFACE
        self.c_card = C_CARD
        self.c_border = C_BORDER
        self.c_text = C_TEXT
        self.c_muted = C_MUTED
        self.c_accent = C_ACCENT
        self.c_accent_hover = C_ACCENT_HOVER
        self.c_success = C_SUCCESS

        self.root.configure(bg=self.c_bg)

        self.current_city = "Москва"
        self.temp_unit = "C"
        self.cached_weather = None

        self._build_ui()
        self.load_weather_async("Москва")

    def _build_ui(self):
        search_bar = tk.Frame(self.root, bg=self.c_bg)
        search_bar.pack(fill="x", padx=24, pady=(20, 10))

        self.search_var = tk.StringVar(value="Москва")
        self.search_entry = tk.Entry(
            search_bar,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            bg=self.c_surface,
            fg=self.c_text,
            insertbackground=self.c_text,
            relief="flat",
            bd=10,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        self.btn_search = tk.Button(
            search_bar,
            text="Найти погоду",
            font=("Segoe UI", 11, "bold"),
            bg=self.c_accent,
            fg="white",
            activebackground=self.c_accent_hover,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.on_search,
        )
        self.btn_search.pack(side="left", padx=(0, 10))

        self.btn_unit = tk.Button(
            search_bar,
            text="°C",
            font=("Segoe UI", 11, "bold"),
            bg=self.c_surface,
            fg=self.c_text,
            activebackground=self.c_card,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.toggle_unit,
        )
        self.btn_unit.pack(side="left")

        quick_bar = tk.Frame(self.root, bg=self.c_bg)
        quick_bar.pack(fill="x", padx=24, pady=(0, 10))

        tk.Label(
            quick_bar,
            text="Быстрый выбор:",
            font=("Segoe UI", 10),
            bg=self.c_bg,
            fg=self.c_muted,
        ).pack(side="left", padx=(0, 8))

        for c in CITIES:
            b = tk.Button(
                quick_bar,
                text=c,
                font=("Segoe UI", 9),
                bg=self.c_surface,
                fg=self.c_text,
                activebackground=self.c_card,
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda name=c: self.quick_select(name),
            )
            b.pack(side="left", padx=3)

        self.lbl_status = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 10),
            bg=self.c_bg,
            fg=self.c_muted,
        )
        self.lbl_status.pack(pady=(0, 8))

        self.main_card = tk.Frame(
            self.root,
            bg=self.c_surface,
            padx=24,
            pady=18,
            highlightbackground=self.c_border,
            highlightthickness=1,
        )
        self.main_card.pack(fill="x", padx=24, pady=(0, 14))

        self.lbl_city = tk.Label(
            self.main_card,
            text="Загрузка данных...",
            font=("Segoe UI", 22, "bold"),
            bg=self.c_surface,
            fg=self.c_text,
        )
        self.lbl_city.pack()

        self.lbl_date = tk.Label(
            self.main_card,
            text="",
            font=("Segoe UI", 10),
            bg=self.c_surface,
            fg=self.c_muted,
        )
        self.lbl_date.pack(pady=(2, 8))

        temp_row = tk.Frame(self.main_card, bg=self.c_surface)
        temp_row.pack(pady=4)

        self.lbl_icon = tk.Label(
            temp_row,
            text="☀️",
            font=("Segoe UI Emoji", 48),
            bg=self.c_surface,
            fg=self.c_text,
        )
        self.lbl_icon.pack(side="left", padx=16)

        self.lbl_temp = tk.Label(
            temp_row,
            text="--°C",
            font=("Segoe UI", 48, "bold"),
            bg=self.c_surface,
            fg=self.c_text,
        )
        self.lbl_temp.pack(side="left")

        self.lbl_condition = tk.Label(
            self.main_card,
            text="Ожидание ответа сервера...",
            font=("Segoe UI", 15),
            bg=self.c_surface,
            fg=self.c_accent,
        )
        self.lbl_condition.pack(pady=2)

        self.lbl_feels = tk.Label(
            self.main_card,
            text="Ощущается как: --°C",
            font=("Segoe UI", 11),
            bg=self.c_surface,
            fg=self.c_muted,
        )
        self.lbl_feels.pack(pady=(0, 4))

        metrics_frame = tk.Frame(self.root, bg=self.c_bg)
        metrics_frame.pack(fill="x", padx=24, pady=(0, 14))
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)

        self.val_humidity = self._create_tile(metrics_frame, 0, "Влажность", "💧", "--")
        self.val_wind = self._create_tile(metrics_frame, 1, "Ветер", "💨", "--")
        self.val_pressure = self._create_tile(metrics_frame, 2, "Давление", "⏱️", "--")
        self.val_uv = self._create_tile(metrics_frame, 3, "УФ-индекс", "☀️", "--")

        forecast_header = tk.Frame(self.root, bg=self.c_bg)
        forecast_header.pack(fill="x", padx=24, pady=(2, 6))

        tk.Label(
            forecast_header,
            text="Прогноз на 5 дней",
            font=("Segoe UI", 12, "bold"),
            bg=self.c_bg,
            fg=self.c_text,
        ).pack(side="left")

        tk.Label(
            forecast_header,
            text="Данные Open-Meteo REST API",
            font=("Segoe UI", 9),
            bg=self.c_bg,
            fg=self.c_muted,
        ).pack(side="right")

        self.forecast_card = tk.Frame(
            self.root,
            bg=self.c_surface,
            padx=16,
            pady=10,
            highlightbackground=self.c_border,
            highlightthickness=1,
        )
        self.forecast_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _create_tile(self, parent, col, title, icon, default_val):
        box = tk.Frame(
            parent,
            bg=self.c_surface,
            padx=12,
            pady=10,
            highlightbackground=self.c_border,
            highlightthickness=1,
        )
        box.grid(row=0, column=col, padx=4, sticky="nsew")

        tk.Label(box, text=icon, font=("Segoe UI Emoji", 16), bg=self.c_surface, fg=self.c_text).pack()
        tk.Label(box, text=title, font=("Segoe UI", 10), bg=self.c_surface, fg=self.c_muted).pack(pady=2)
        v = tk.Label(box, text=default_val, font=("Segoe UI", 13, "bold"), bg=self.c_surface, fg=self.c_text)
        v.pack()
        return v

    def quick_select(self, city: str):
        self.search_var.set(city)
        self.on_search()

    def toggle_unit(self):
        self.temp_unit = "F" if self.temp_unit == "C" else "C"
        self.btn_unit.config(text=f"°{self.temp_unit}")
        if self.cached_weather:
            self._render_weather(self.cached_weather[0], self.cached_weather[1], self.cached_weather[2])

    def on_search(self):
        city = self.search_var.get().strip()
        if not city:
            self.lbl_status.config(text="Пожалуйста, введите название города!", fg="#ef4444")
            return
        self.load_weather_async(city)

    def load_weather_async(self, city: str):
        self.btn_search.config(state="disabled")
        self.lbl_status.config(text=f"Загрузка погоды для '{city}'...", fg=self.c_muted)

        thread = threading.Thread(target=self._worker_fetch, args=(city,), daemon=True)
        thread.start()

    def _worker_fetch(self, city: str):
        try:
            result = fetch_weather_data(city)
            if not result:
                self.root.after(0, self._show_error, f"Город '{city}' не найден. Проверьте правильность названия.")
                return

            city_name, country, w_data = result
            self.cached_weather = (city_name, country, w_data)
            self.root.after(0, self._render_weather, city_name, country, w_data)
        except Exception as err:
            self.root.after(0, self._show_error, f"Ошибка сети: {str(err)}")

    def _format_temp(self, celsius: float) -> str:
        return format_temp(celsius, self.temp_unit)

    def _render_weather(self, city_name: str, country: str, data: dict):
        self.btn_search.config(state="normal")
        self.lbl_status.config(
            text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')} (Отклик получен успешно)",
            fg=self.c_success,
        )

        current = data.get("current", {})
        temp = current.get("temperature_2m", 0)
        feels = current.get("apparent_temperature", 0)
        code = current.get("weather_code", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        wind_dir = current.get("wind_direction_10m", 0)
        pressure_hpa = current.get("surface_pressure", 1013)
        pressure_mm = round(pressure_hpa * 0.750062)

        desc, icon = WMO_CODES.get(code, ("Неизвестно", "🌡️"))
        wind_dir_str = get_wind_direction_ru(wind_dir)

        full_city = f"{city_name}, {country}" if country else city_name
        self.lbl_city.config(text=full_city)
        self.lbl_date.config(text=datetime.now().strftime("%d.%m.%Y • %A"))
        self.lbl_temp.config(text=self._format_temp(temp))
        self.lbl_icon.config(text=icon)
        self.lbl_condition.config(text=desc)
        self.lbl_feels.config(text=f"Ощущается как: {self._format_temp(feels)}")

        self.val_humidity.config(text=f"{humidity} %")
        self.val_wind.config(text=f"{wind_speed:.1f} км/ч {wind_dir_str}")
        self.val_pressure.config(text=f"{pressure_mm} мм рт. ст.")

        daily = data.get("daily", {})
        uv_max = "--"
        if daily.get("uv_index_max"):
            uv_max = str(round(daily["uv_index_max"][0], 1))
        self.val_uv.config(text=uv_max)

        for widget in self.forecast_card.winfo_children():
            widget.destroy()

        d_times = daily.get("time", [])
        d_codes = daily.get("weather_code", [])
        d_maxs = daily.get("temperature_2m_max", [])
        d_mins = daily.get("temperature_2m_min", [])

        for i in range(min(5, len(d_times))):
            d_obj = datetime.strptime(d_times[i], "%Y-%m-%d")
            day_str = "Сегодня" if i == 0 else f"{DAYS_RU[d_obj.weekday()]}, {d_obj.strftime('%d.%m')}"

            f_code = d_codes[i] if i < len(d_codes) else 0
            f_desc, f_icon = WMO_CODES.get(f_code, ("Ясно", "☀️"))
            t_max = d_maxs[i] if i < len(d_maxs) else 0
            t_min = d_mins[i] if i < len(d_mins) else 0

            row = tk.Frame(self.forecast_card, bg=self.c_surface)
            row.pack(fill="x", pady=4)

            tk.Label(row, text=day_str, font=("Segoe UI", 10, "bold"), width=14, anchor="w", bg=self.c_surface, fg=self.c_text).pack(side="left")
            tk.Label(row, text=f_icon, font=("Segoe UI Emoji", 14), width=3, bg=self.c_surface, fg=self.c_text).pack(side="left", padx=4)
            tk.Label(row, text=f_desc, font=("Segoe UI", 10), anchor="w", bg=self.c_surface, fg=self.c_muted).pack(side="left", fill="x", expand=True)

            temp_range = f"{self._format_temp(t_min)} … {self._format_temp(t_max)}"
            tk.Label(row, text=temp_range, font=("Segoe UI", 10, "bold"), anchor="e", bg=self.c_surface, fg=self.c_text).pack(side="right")

    def _show_error(self, message: str):
        self.btn_search.config(state="normal")
        self.lbl_status.config(text=message, fg="#ef4444")
