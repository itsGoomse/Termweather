import json
import os

location = ""
cities = []
refresh = 600
temp_unit = "°C"
speed_unit = "km/h"
humidity_unit = "%"
precip_unit = "mm"
theme = "textual-dark"

# Extra hourly forecast variables the user can opt into (beyond the always-on
# temperature, wind and precipitation). Key = Open-Meteo variable name,
# value = (display label, unit).
HOURLY_VARIABLE_OPTIONS = {
    "relative_humidity_2m": ("Humidity", "%"),
    "apparent_temperature": ("Feels like", "°C"),
    "dew_point_2m": ("Dew point", "°C"),
    "pressure_msl": ("Pressure", "hPa"),
    "cloud_cover": ("Cloud cover", "%"),
    "visibility": ("Visibility", "km"),
    "wind_direction_10m": ("Wind dir", "°"),
    "wind_gusts_10m": ("Wind gusts", "km/h"),
    "rain": ("Rain", "mm"),
    "snowfall": ("Snowfall", "cm"),
}

# The extra hourly variables currently enabled (subset of HOURLY_VARIABLE_OPTIONS).
hourly_variables: list[str] = []

# Path to the JSON file that persists user-added cities.
CITIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cities.json")

# Path to the JSON file that persists user preferences (e.g. the chosen theme).
PREFERENCES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "userpreferences.json"
)


def load_cities() -> list[str]:
    """Read the persisted list of user-added cities from the JSON file.

    Returns ``[]`` if the file does not exist, is empty, or is malformed.
    """
    try:
        with open(CITIES_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [str(city) for city in data]


def save_cities(cities: list[str]) -> None:
    """Write the list of user-added cities to the JSON file."""
    with open(CITIES_FILE, "w", encoding="utf-8") as fh:
        json.dump(cities, fh, ensure_ascii=False, indent=2)


# Initialize the module-level list from the persisted file on import.
cities = load_cities()


def load_preferences() -> dict:
    """Read persisted user preferences from the JSON file.

    Returns ``{}`` if the file does not exist, is empty, or is malformed.
    """
    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save_preferences(preferences: dict) -> None:
    """Write the user preferences to the JSON file."""
    with open(PREFERENCES_FILE, "w", encoding="utf-8") as fh:
        json.dump(preferences, fh, ensure_ascii=False, indent=2)


def load_theme() -> str:
    """Return the saved theme name, or the default if none is stored."""
    prefs = load_preferences()
    saved = prefs.get("theme")
    return str(saved) if saved else theme


def save_theme(name: str) -> None:
    """Persist the chosen theme name to the preferences file."""
    prefs = load_preferences()
    prefs["theme"] = name
    save_preferences(prefs)


# Initialize the module-level theme from the persisted file on import.
theme = load_theme()


def load_hourly_variables() -> list[str]:
    """Return the saved extra hourly variables, or ``[]`` if none stored."""
    prefs = load_preferences()
    saved = prefs.get("hourly_variables")
    if not isinstance(saved, list):
        return []
    # Keep only variables we actually support.
    return [str(v) for v in saved if str(v) in HOURLY_VARIABLE_OPTIONS]


def save_hourly_variables(variables: list[str]) -> None:
    """Persist the chosen extra hourly variables to the preferences file."""
    prefs = load_preferences()
    prefs["hourly_variables"] = variables
    save_preferences(prefs)


# Initialize the module-level list from the persisted file on import.
hourly_variables = load_hourly_variables()

