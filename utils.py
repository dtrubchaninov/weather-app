def get_wind_direction_ru(degrees: float) -> str:
    directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
    return directions[round(degrees / 45) % 8]


def format_temp(celsius: float, unit: str) -> str:
    if unit == "F":
        f = round((celsius * 9 / 5) + 32)
        return f"{f:+d}°F" if f != 0 else "0°F"
    c = round(celsius)
    return f"{c:+d}°C" if c != 0 else "0°C"
