import json
import urllib.parse
import urllib.request


def fetch_weather_data(city: str):
    encoded = urllib.parse.quote(city)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=ru&format=json"
    req = urllib.request.Request(geo_url, headers={"User-Agent": "DesktopWeatherApp/1.0"})

    with urllib.request.urlopen(req, timeout=15) as resp:
        geo_data = json.loads(resp.read().decode("utf-8"))

    if not geo_data.get("results"):
        return None

    loc = geo_data["results"][0]
    lat = loc["latitude"]
    lon = loc["longitude"]
    city_name = loc.get("name", city)
    country = loc.get("country", "")

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max&timezone=auto"
    )
    w_req = urllib.request.Request(weather_url, headers={"User-Agent": "DesktopWeatherApp/1.0"})
    with urllib.request.urlopen(w_req, timeout=20) as resp:
        w_data = json.loads(resp.read().decode("utf-8"))

    return city_name, country, w_data
