import time

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10  # seconds

# How long (in seconds) cached weather data stays fresh before we re-fetch.
CACHE_TTL = 3600  # 1 hour

# A single session is reused across all calls for connection pooling.
_session = requests.Session()

# In-memory cache: city name -> (timestamp, (info, current, daily, hourly)).
_cache: dict[str, tuple[float, tuple[dict, dict, dict, dict]]] = {}


class WeatherError(Exception):
    """Raised when the weather API cannot fulfil a request."""


def _get_json(url: str, params: dict) -> dict:
    """Perform a GET request and return the parsed JSON, or raise WeatherError."""
    try:
        response = _session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherError(f"Network error contacting the weather service: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise WeatherError("The weather service returned an invalid response.") from exc

    if not isinstance(data, dict):
        raise WeatherError("The weather service returned an unexpected response.")

    if "error" in data:
        reason = data.get("reason", "unknown error")
        raise WeatherError(f"The weather service reported an error: {reason}")

    return data


def _geocode(city: str) -> dict:
    """Return the first geocoding result for a city, or raise WeatherError."""
    data = _get_json(GEOCODING_URL, {"name": city, "count": 1})
    results = data.get("results") or []
    if not results:
        raise WeatherError(f"City not found: {city!r}")
    return results[0]


def get_coords(city: str) -> tuple[float, float]:
    """Return (latitude, longitude) for a city name."""
    result = _geocode(city)
    return result["latitude"], result["longitude"]


def get_city_info(city: str) -> dict:
    """Return geocoding details (name, country, lat, lon) for a city."""
    result = _geocode(city)
    return {
        "name": result.get("name", city),
        "country": result.get("country", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


def get_weather(city: str) -> dict:
    """Return current weather for a city (geocodes internally)."""
    lat, lon = get_coords(city)
    data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,relative_humidity_2m",
        },
    )
    current = data.get("current")
    if not isinstance(current, dict):
        raise WeatherError("The weather service returned no current-weather data.")
    return current


def get_forecast(city: str) -> dict:
    """Return a short daily forecast for a city (geocodes internally)."""
    lat, lon = get_coords(city)
    data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "forecast_days": 5,
        },
    )
    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise WeatherError("The weather service returned no forecast data.")
    return daily


def get_hourly_forecast(city: str) -> dict:
    """Return the next 24 hours of hourly forecast data for a city."""
    lat, lon = get_coords(city)
    data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "forecast_hours": 24,
        },
    )
    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherError("The weather service returned no hourly forecast data.")
    return hourly


def get_city_weather(
    city: str, force: bool = False
) -> tuple[dict, dict, dict, dict]:
    """Fetch city info, current weather, daily and hourly forecast in one geocode.

    Returns ``(info, weather, daily, hourly)``.  This avoids geocoding the same
    city multiple times and is the recommended entry point for the UI.

    Results are cached per city for ``CACHE_TTL`` seconds (1 hour). If a cached
    result is still fresh, it is returned without hitting the API again, unless
    ``force`` is ``True`` (which bypasses the cache and re-fetches).
    """
    now = time.time()
    cached = _cache.get(city)
    if not force and cached is not None:
        timestamp, data = cached
        if now - timestamp < CACHE_TTL:
            return data

    result = _geocode(city)
    info = {
        "name": result.get("name", city),
        "country": result.get("country", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }
    lat, lon = result["latitude"], result["longitude"]

    weather_data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,relative_humidity_2m",
        },
    )
    current = weather_data.get("current")
    if not isinstance(current, dict):
        raise WeatherError("The weather service returned no current-weather data.")

    forecast_data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "forecast_days": 5,
        },
    )
    daily = forecast_data.get("daily")
    if not isinstance(daily, dict):
        raise WeatherError("The weather service returned no forecast data.")

    hourly_data = _get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,wind_speed_10m,precipitation,precipitation_probability,weather_code",
            "forecast_hours": 24,
        },
    )
    hourly = hourly_data.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherError("The weather service returned no hourly forecast data.")

    data = (info, current, daily, hourly)
    _cache[city] = (now, data)
    return data