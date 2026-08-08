import json
import os

location = ""
cities = []
refresh = 600
temp_unit = "°C"
speed_unit = "km/h"
humidity_unit = "%"
precip_unit = "mm"

# Path to the JSON file that persists user-added cities.
CITIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cities.json")


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

