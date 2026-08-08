"""Entry point for the TermWeather TUI."""

import signal
import sys

import config
from ui import WeatherApp


def main() -> None:
    if "--once" in sys.argv:
        # Non-interactive test mode: fetch data and print, then exit cleanly.
        # This avoids entering the alternate screen buffer.
        from weather import get_city_weather

        # Use an optional city argument, else the first persisted city,
        # else a sensible default for testing.
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        city = args[0] if args else (config.cities[0] if config.cities else "Holbæk")
        info, weather, forecast, hourly = get_city_weather(city)
        print(f"City: {info['name']} ({info['latitude']:.4f}, {info['longitude']:.4f})")
        print(f"Temp: {weather['temperature_2m']} {config.temp_unit}")
        print(f"Wind: {weather['wind_speed_10m']} {config.speed_unit}")
        print(f"Humidity: {weather['relative_humidity_2m']}{config.humidity_unit}")
        print(f"Daily days: {len(forecast['time'])}")
        print(f"Hourly hours: {len(hourly['time'])}")
        print(f"Hourly temps: {hourly['temperature_2m'][:5]}...")
        return

    app = WeatherApp()

    def _restore_and_exit(signum, frame):
        """Restore the terminal and exit cleanly on SIGINT/SIGTERM."""
        app.exit()
        sys.exit(0)

    # Ensure the terminal is restored even if the app is interrupted.
    signal.signal(signal.SIGINT, _restore_and_exit)
    signal.signal(signal.SIGTERM, _restore_and_exit)

    app.run()


if __name__ == "__main__":
    main()