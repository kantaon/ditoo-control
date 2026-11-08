"""Weather from Open-Meteo (free, no API key)."""
import json
import time
import urllib.parse
import urllib.request

from . import __version__

UA = {"User-Agent": f"DitooControl/{__version__}"}

WMO = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
    51: "Drizzle", 53: "Drizzle", 55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Showers", 81: "Showers", 82: "Heavy showers", 85: "Snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
        return json.loads(r.read().decode())


def geocode(name, lang="en"):
    q = urllib.parse.urlencode({"name": name, "count": 6, "language": lang, "format": "json"})
    data = _get("https://geocoding-api.open-meteo.com/v1/search?" + q)
    return [{"name": r["name"], "country": r.get("country", ""), "admin": r.get("admin1", ""),
             "lat": r["latitude"], "lon": r["longitude"]} for r in data.get("results", [])]


class Weather:
    def __init__(self):
        self.data = None
        self.fetched = 0.0
        self.error = None
        self._loc = None

    def invalidate(self):
        self._loc, self.data = None, None

    def get(self, lat, lon, max_age=900):
        if self._loc != (lat, lon):
            self._loc, self.data = (lat, lon), None
        if self.data and time.time() - self.fetched < max_age:
            return self.data
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 2,
            "current": "temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m,relative_humidity_2m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        })
        try:
            d = _get("https://api.open-meteo.com/v1/forecast?" + q)
            c, dl = d["current"], d["daily"]
            self.data = {
                "temp": c["temperature_2m"], "feels": c["apparent_temperature"], "code": c["weather_code"],
                "is_day": bool(c["is_day"]), "wind": c["wind_speed_10m"], "humidity": c["relative_humidity_2m"],
                "text": WMO.get(c["weather_code"], ""),
                "tomorrow": {"code": dl["weather_code"][1], "max": dl["temperature_2m_max"][1],
                             "min": dl["temperature_2m_min"][1], "rain": dl["precipitation_probability_max"][1],
                             "text": WMO.get(dl["weather_code"][1], "")},
                "today": {"max": dl["temperature_2m_max"][0], "min": dl["temperature_2m_min"][0]},
            }
            self.fetched, self.error = time.time(), None
        except Exception as e:  # network down, keep last data
            self.error = str(e)
            self.fetched = time.time() - max_age + 120  # retry in 2 min
        return self.data
