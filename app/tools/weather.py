import requests

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def get_weather(location: str) -> str:
    try:
        geo = requests.get(
            _GEOCODE_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=5,
        ).json()
    except Exception as e:
        return f"Could not reach the geocoding service: {e}"

    results = geo.get("results")
    if not results:
        return f"I couldn't find a location called **{location}**. Try being more specific (e.g. 'Delhi, India')."

    place = results[0]
    lat, lon = place["latitude"], place["longitude"]
    city = place.get("name", location)
    country = place.get("country", "")

    try:
        forecast = requests.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "weathercode",
                    "is_day",
                ],
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "timezone": "auto",
            },
            timeout=5,
        ).json()
    except Exception as e:
        return f"Could not fetch weather data: {e}"

    current = forecast.get("current", {})
    code = current.get("weathercode", 0)
    condition = _WMO_CODES.get(code, "Unknown")
    temp = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    is_day = current.get("is_day", 1)
    time_of_day = "daytime" if is_day else "nighttime"

    return (
        f"**{city}, {country}** — {condition}\n\n"
        f"- **Temperature:** {temp}°C (feels like {feels_like}°C)\n"
        f"- **Humidity:** {humidity}%\n"
        f"- **Wind:** {wind} km/h\n"
        f"- **Time of day:** {time_of_day}"
    )
