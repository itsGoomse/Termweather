"""Simple live-updating weather TUI built with Textual."""

from collections.abc import Callable, Iterable

from textual import work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.command import CommandPalette, Hit, Hits, Provider
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Label, ListItem, ListView, Static

import config
from weather import get_city_weather

# WMO weather code -> short description
WEATHER_CODES = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm + hail",
    99: "Thunderstorm + hail",
}


class ThemeListProvider(Provider):
    """Provider that lists every theme, used inside the theme submenu."""

    async def search(self, query: str) -> Hits:
        """Yield a command for each theme matching the query."""
        matcher = self.matcher(query)
        for theme in self._themes():
            if (match := matcher.match(theme)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(theme),
                    self._make_callback(theme),
                    text=theme,
                    help=f"Switch to the {theme} theme",
                )

    async def discover(self) -> Hits:
        """Yield all themes so they show up before the user types."""
        for theme in self._themes():
            yield Hit(
                0,
                theme,
                self._make_callback(theme),
                text=theme,
                help=f"Switch to the {theme} theme",
            )

    def _themes(self) -> list[str]:
        """Return every theme available to the app, sorted by name."""
        return sorted(self.app.available_themes)

    def _make_callback(self, theme: str):
        """Return a zero-argument callback that applies the given theme."""
        def apply() -> None:
            app = self.app
            app.theme = theme
            config.theme = theme
            config.save_theme(theme)
        return apply


class HourlyVariableProvider(Provider):
    """Command palette provider that toggles extra hourly forecast variables."""

    async def search(self, query: str) -> Hits:
        """Yield a command for each variable matching the query."""
        matcher = self.matcher(query)
        for var, (label, _unit) in config.HOURLY_VARIABLE_OPTIONS.items():
            if (match := matcher.match(label)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(label),
                    self._make_callback(var),
                    text=label,
                    help=self._help_text(var),
                )

    async def discover(self) -> Hits:
        """Yield all variables so they show up before the user types."""
        for var, (label, _unit) in config.HOURLY_VARIABLE_OPTIONS.items():
            yield Hit(
                0,
                label,
                self._make_callback(var),
                text=label,
                help=self._help_text(var),
            )

    def _help_text(self, var: str) -> str:
        state = "on" if var in config.hourly_variables else "off"
        return f"Hourly {config.HOURLY_VARIABLE_OPTIONS[var][0]} is {state} — click to toggle"

    def _make_callback(self, var: str):
        """Return a zero-argument callback that toggles the given variable."""
        def toggle() -> None:
            if var in config.hourly_variables:
                config.hourly_variables.remove(var)
            else:
                config.hourly_variables.append(var)
            config.save_hourly_variables(config.hourly_variables)
            # Refresh the current city so the new columns appear.
            app = self.app
            if isinstance(app, WeatherApp) and app.current_city:
                app._fetch_weather(app.current_city, force=True)
        return toggle


class SettingsProvider(Provider):
    """Command palette provider that lets the user tweak app settings."""

    # (label, help, callback)
    def _commands(self) -> list[tuple[str, str, Callable[[], None]]]:
        return [
            (
                f"Refresh interval: {config.refresh}s",
                "Set how often the weather auto-refreshes",
                self._set_refresh,
            ),
            (
                f"Temperature unit: {config.temp_unit}",
                "Set the temperature unit",
                self._set_temp_unit,
            ),
            (
                f"Wind speed unit: {config.speed_unit}",
                "Set the wind speed unit",
                self._set_speed_unit,
            ),
            (
                f"Humidity unit: {config.humidity_unit}",
                "Set the humidity unit",
                self._set_humidity_unit,
            ),
            (
                f"Precipitation unit: {config.precip_unit}",
                "Set the precipitation unit",
                self._set_precip_unit,
            ),
        ]

    async def search(self, query: str) -> Hits:
        """Yield a command for each setting matching the query."""
        matcher = self.matcher(query)
        for label, help_text, callback in self._commands():
            if (match := matcher.match(label)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(label),
                    callback,
                    text=label,
                    help=help_text,
                )

    async def discover(self) -> Hits:
        """Yield all settings so they show up before the user types."""
        for label, help_text, callback in self._commands():
            yield Hit(
                0,
                label,
                callback,
                text=label,
                help=help_text,
            )

    def _set_refresh(self) -> None:
        """Cycle the refresh interval through a few sensible values."""
        options = [300, 600, 900, 1800, 3600]
        current = config.refresh
        next_value = options[(options.index(current) + 1) % len(options)] if current in options else options[0]
        config.save_refresh(next_value)
        app = self.app
        if isinstance(app, WeatherApp):
            app._restart_refresh_timer()
        self._reopen()

    def _set_temp_unit(self) -> None:
        self._cycle_unit("temp_unit", ["°C", "°F", "K"])

    def _set_speed_unit(self) -> None:
        self._cycle_unit("speed_unit", ["km/h", "mph", "m/s", "kn"])

    def _set_humidity_unit(self) -> None:
        self._cycle_unit("humidity_unit", ["%"])

    def _set_precip_unit(self) -> None:
        self._cycle_unit("precip_unit", ["mm", "in"])

    def _cycle_unit(self, key: str, options: list[str]) -> None:
        """Cycle a unit setting through the given options and persist it."""
        current = getattr(config, key)
        next_value = options[(options.index(current) + 1) % len(options)] if current in options else options[0]
        setattr(config, key, next_value)
        config.save_unit(key, next_value)
        app = self.app
        if isinstance(app, WeatherApp) and app.current_city:
            app._fetch_weather(app.current_city, force=True)
        self._reopen()

    def _reopen(self) -> None:
        """Re-open the settings menu so the user can keep adjusting settings."""
        app = self.app
        if isinstance(app, WeatherApp):
            app._open_settings_menu()


class WeatherApp(App):
    """A TUI that shows current weather + forecast, with city switching."""

    TITLE = "TermWeather"

    # Keybindings shown automatically in the Footer.
    # priority=True keeps these visible in the footer even when a focused
    # widget (e.g. the city list or the input) defines its own bindings for
    # the same keys.
    BINDINGS = [
        Binding("up", "focus_previous", "Previous panel"),
        Binding("down", "focus_next", "Next panel"),
        Binding("tab", "focus_next", "Next panel"),
        Binding("shift+tab", "focus_previous", "Previous panel"),
        Binding("escape", "back_to_city_list", "Back to city list"),
        Binding("ctrl+d", "delete_city", "Delete city"),
        Binding("ctrl+f", "force_refresh", "Force update"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    CSS = """
    #city-list {
        width: 30%;
        border: round $primary;
        margin: 1 1 1 2;
    }
    #weather-box {
        border: round $primary;
        padding: 1 2;
        margin: 1 2 1 1;
        width: 1fr;
    }
    #forecast-box {
        border: round $primary;
        padding: 1 2;
        margin: 1 2 1 1;
        width: 1fr;
    }
    #hourly-box {
        border: round $primary;
        padding: 1 2;
        margin: 1 2 1 1;
        width: 1fr;
    }
    #city {
        text-style: bold;
        color: $accent;
    }
    #coords {
        color: $text-muted;
    }
    #last-updated {
        color: $text-muted;
    }
    #status {
        color: $text-muted;
        text-style: italic;
    }
    #hint {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }
    #add-city {
        margin: 1 2 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # On first boot there is no persisted city, so start with an empty
        # selection and show empty values until the user adds a city.
        self.current_city = config.location or ""
        # Apply the saved theme (from userpreferences.json) on startup.
        self.theme = config.theme

    def get_system_commands(self, screen) -> Iterable[SystemCommand]:
        """Yield the usual system commands, but replace the built-in 'Theme'
        command with one that opens our theme submenu (which persists the
        choice to userpreferences.json), and add a 'Variables' command that
        opens the hourly-variable picker."""
        for command in super().get_system_commands(screen):
            if command.title == "Theme":
                yield SystemCommand(
                    "Theme",
                    "Choose a theme",
                    self._open_theme_menu,
                )
            else:
                yield command
        yield SystemCommand(
            "Variables",
            "Choose extra hourly forecast variables",
            self._open_variables_menu,
        )
        yield SystemCommand(
            "Settings",
            "Adjust refresh interval and units",
            self._open_settings_menu,
        )

    def _open_theme_menu(self) -> None:
        """Open a nested command palette listing all themes."""
        self.push_screen(
            CommandPalette(
                providers=[ThemeListProvider],
                placeholder="Search themes…",
            )
        )

    def _open_variables_menu(self) -> None:
        """Open a nested command palette listing the extra hourly variables."""
        self.push_screen(
            CommandPalette(
                providers=[HourlyVariableProvider],
                placeholder="Search variables…",
            )
        )

    def _open_settings_menu(self) -> None:
        """Open a nested command palette listing the app settings."""
        self.push_screen(
            CommandPalette(
                providers=[SettingsProvider],
                placeholder="Search settings…",
            )
        )

    def _restart_refresh_timer(self) -> None:
        """Restart the auto-refresh interval with the current config value."""
        if hasattr(self, "_refresh_timer"):
            self._refresh_timer.stop()
        self._refresh_timer = self.set_interval(config.refresh, self.refresh_all)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            ListView(
                *[ListItem(Label(city)) for city in config.cities],
                id="city-list",
            ),
            Vertical(
                Static("", id="city"),
                Static("", id="coords"),
                Static("", id="temp"),
                Static("", id="wind"),
                Static("", id="humidity"),
                Static("", id="last-updated"),
                Static("", id="status"),
                Static("", id="hint"),
                id="weather-box",
            ),
            Vertical(
                Static("📅 5-Day Forecast", id="forecast-title"),
                Static("", id="forecast"),
                id="forecast-box",
            ),
        )
        yield Vertical(
            Static("🕐 Next 24 Hours", id="hourly-title"),
            DataTable(id="hourly-chart"),
            id="hourly-box",
        )
        yield Input(placeholder="Add a city and press Enter…", id="add-city")
        yield Footer()

    def on_mount(self) -> None:
        if self.current_city:
            self.refresh_all()
        else:
            self.query_one("#hint", Static).update(
                "👋 No city selected yet. Type a city below and press Enter to get started."
            )
        # Refresh periodically based on config (seconds).
        self._refresh_timer = self.set_interval(config.refresh, self.refresh_all)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Switch the displayed city when the user selects one."""
        # event.item is a ListItem whose first child is the Label we created.
        label = event.item.children[0]
        self.current_city = str(label.content)  # type: ignore[union-attr]
        self.refresh_all()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Add a new city to the list and switch to it."""
        city = event.value.strip()
        if not city:
            return
        if city not in config.cities:
            config.cities.append(city)
            config.save_cities(config.cities)
            self.query_one("#city-list", ListView).append(
                ListItem(Label(city))
            )
        self.current_city = city
        event.input.value = ""
        # Move the cursor back to the start position.
        event.input.cursor_position = 0
        self.refresh_all()
        # Return focus to the city list so arrow keys navigate cities again.
        self.query_one("#city-list", ListView).focus()

    def action_back_to_city_list(self) -> None:
        """Blur the Input and return focus to the city list."""
        self.query_one("#city-list", ListView).focus()

    def action_delete_city(self) -> None:
        """Delete the currently highlighted city (Ctrl+D)."""
        list_view = self.query_one("#city-list", ListView)
        item = list_view.highlighted_child
        if item is None:
            return
        # Extract the city name from the highlighted item's label.
        label = item.children[0]
        city = str(label.content)  # type: ignore[union-attr]

        if city in config.cities:
            config.cities.remove(city)
            config.save_cities(config.cities)

        # Remove the item from the list view.
        index = list_view.index
        if index is not None:
            list_view.remove_items([index])

        # If we deleted the currently displayed city, clear the panels.
        if city == self.current_city:
            self.current_city = ""
            self._clear_panels()
            self.query_one("#hint", Static).update(
                "👋 No city selected. Type a city below and press Enter to get started."
            )

    def refresh_all(self) -> None:
        """Kick off a background fetch for the current city."""
        self._fetch_weather(self.current_city)

    def action_force_refresh(self) -> None:
        """Force a fresh fetch for the current city, bypassing the cache."""
        if not self.current_city:
            return
        self._fetch_weather(self.current_city, force=True)

    def _clear_panels(self) -> None:
        """Reset all weather panels to empty values."""
        self.query_one("#city", Static).update("")
        self.query_one("#coords", Static).update("")
        self.query_one("#temp", Static).update("")
        self.query_one("#wind", Static).update("")
        self.query_one("#humidity", Static).update("")
        self.query_one("#last-updated", Static).update("")
        self.query_one("#status", Static).update("")
        self.query_one("#forecast", Static).update("")
        table = self.query_one("#hourly-chart", DataTable)
        table.clear(columns=True)

    @work(thread=True, exclusive=True, group="weather")
    def _fetch_weather(self, city: str, force: bool = False) -> None:
        """Fetch weather data off the UI thread and update the UI when done."""
        self.query_one("#status", Static).update("⏳ Loading…")
        try:
            info, weather, forecast, hourly = get_city_weather(city, force=force)
        except Exception as exc:
            # Show a friendly "no results" message when the city isn't found.
            message = f"⚠️ No results for '{city}'. Check the spelling and try again."
            if "City not found" not in str(exc):
                message = f"⚠️ Error: {exc}"
            self.call_from_thread(
                self.query_one("#status", Static).update, message
            )
            return

        self.call_from_thread(self._update_ui, info, weather, forecast, hourly)

    def _update_ui(
        self, info: dict, weather: dict, forecast: dict, hourly: dict
    ) -> None:
        """Update the UI widgets with freshly fetched data (runs on UI thread)."""
        # Current weather panel
        self.query_one("#city", Static).update(f"📍 {info['name']}")
        self.query_one("#coords", Static).update(
            f"🌐 {info['latitude']:.4f}, {info['longitude']:.4f}"
        )
        self.query_one("#temp", Static).update(
            f"🌡️  Temperature: {config.convert_temp(weather['temperature_2m']):.1f} {config.temp_unit}"
        )
        self.query_one("#wind", Static).update(
            f"💨 Wind: {config.convert_speed(weather['wind_speed_10m']):.1f} {config.speed_unit}"
        )
        self.query_one("#humidity", Static).update(
            f"💧 Humidity: {weather['relative_humidity_2m']}{config.humidity_unit}"
        )
        self.query_one("#hint", Static).update("")
        self.query_one("#last-updated", Static).update(
            f"Updated: {weather['time']}"
        )
        self.query_one("#status", Static).update("")

        # Daily forecast panel
        self.query_one("#forecast", Static).update(self._format_forecast(forecast))

        # Hourly forecast chart
        self._update_hourly_chart(hourly)

    def _update_hourly_chart(self, hourly: dict) -> None:
        """Render the next 24 hours as a table of time, temp and wind."""
        table = self.query_one("#hourly-chart", DataTable)
        table.clear(columns=True)
        table.add_column("Time")
        table.add_column(f"Temp ({config.temp_unit})")
        table.add_column(f"Wind ({config.speed_unit})")
        table.add_column(f"Precip ({config.precip_unit})")

        # Add a column for each enabled extra variable.
        for var in config.hourly_variables:
            if var in config.HOURLY_VARIABLE_OPTIONS and var in hourly:
                label, unit = config.HOURLY_VARIABLE_OPTIONS[var]
                table.add_column(f"{label} ({unit})")

        times = hourly["time"]
        temps = hourly["temperature_2m"]
        winds = hourly["wind_speed_10m"]
        precip = hourly["precipitation"]
        for i, t in enumerate(times):
            row = [
                t[11:16],
                f"{config.convert_temp(temps[i]):.1f}",
                f"{config.convert_speed(winds[i]):.1f}",
                f"{config.convert_precip(precip[i]):.1f}",
            ]
            for var in config.hourly_variables:
                if var in config.HOURLY_VARIABLE_OPTIONS and var in hourly:
                    row.append(f"{hourly[var][i]}")
            table.add_row(*row)

    def _format_forecast(self, forecast: dict) -> str:
        """Build a multi-line string from the daily forecast data."""
        lines = []
        dates = forecast["time"]
        highs = forecast["temperature_2m_max"]
        lows = forecast["temperature_2m_min"]
        codes = forecast["weather_code"]
        for date, high, low, code in zip(dates, highs, lows, codes):
            desc = WEATHER_CODES.get(code, f"Code {code}")
            lines.append(
                f"{date}  {desc:<16} {config.convert_temp(low):.1f}{config.temp_unit} / {config.convert_temp(high):.1f}{config.temp_unit}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if "--once" in sys.argv:
        # Non-interactive test mode: fetch data and print, then exit cleanly.
        # This avoids entering the alternate screen buffer.
        from weather import get_city_weather

        city = config.location
        info, weather, forecast, hourly = get_city_weather(city)
        print(f"City: {info['name']} ({info['latitude']:.4f}, {info['longitude']:.4f})")
        print(f"Temp: {weather['temperature_2m']}{config.temp_unit}")
        print(f"Wind: {weather['wind_speed_10m']} {config.speed_unit}")
        print(f"Humidity: {weather['relative_humidity_2m']}{config.humidity_unit}")
        print(f"Daily days: {len(forecast['time'])}")
        print(f"Hourly hours: {len(hourly['time'])}")
        print(f"Hourly temps: {hourly['temperature_2m'][:5]}...")
    else:
        WeatherApp().run()
