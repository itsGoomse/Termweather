# 🌦️ TermWeather

A live-updating weather **TUI** (terminal user interface) built with [Textual](https://textual.textualize.io/). It pulls current conditions, a 5-day forecast, and a 24-hour breakdown from the free [Open-Meteo](https://open-meteo.com/) API — no API key required.

![Python](https://img.shields.io/badge/Python-3.14+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Current weather** — temperature, wind, humidity, and coordinates for the selected city
- **5-day forecast** — daily high/low temperatures with weather descriptions
- **24-hour breakdown** — hourly temperature, wind, and precipitation in a table
- **Multi-city support** — add cities and switch between them with the keyboard
- **Persistent city list** — your added cities are saved to `cities.json` and restored on next launch
- **Live auto-refresh** — updates on a configurable interval
- **Fully keyboard-navigable** — arrow keys, Tab, and Esc to move between panels

---

## Getting Started

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

### Installation

```bash
# Run the included install script (recommended)
cd termweather
./install.sh
```

```bash
# Or set up manually
git clone https://github.com/itsGoomse/termweather.git
cd termweather

# With uv
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run the TUI

```bash
TermWeather
```

### Run a one-off data check (no TUI)

```bash
TermWeather --once "Holbæk"
```

> The `TermWeather` command is created automatically when the package is installed (via `uv sync` or `pip install -e .`). The `install.sh` script also installs a **global launcher** in `~/.local/bin`, so you can run `TermWeather` from any directory without activating the virtual environment. If `~/.local/bin` is not on your `PATH`, add it to your shell config (e.g. `export PATH="$HOME/.local/bin:$PATH"` in `~/.bashrc`). If you're in the project directory without installing, you can still run `python main.py` directly.

---

## 🎮 Usage

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate the city list / table cells |
| `Enter` | Select a city from the list |
| `Tab` / `Shift+Tab` | Cycle between panels |
| `Esc` | Return focus to the city list |
| `Ctrl+P` | Open the command palette |
| `Ctrl+F` | Force update (bypass the cache) |
| `Ctrl+Q` | Quit |

**Add a city:** type a city name in the input at the bottom and press `Enter`. It will be added to the list and saved for next time.

**Change the theme:** press `Ctrl+P` to open the command palette, select **Theme**, then pick any of the available themes (e.g. `nord`, `gruvbox`, `catppuccin-mocha`, `dracula`, `tokyo-night`). Your choice is saved to `userpreferences.json` and restored on the next launch. The usual system commands (Keys, Quit, Screenshot, etc.) remain available in the palette.

**Add extra hourly variables:** press `Ctrl+P`, select **Variables**, then toggle any of the extra 24-hour forecast columns (e.g. Humidity, Feels like, Cloud cover, Wind gusts). Enabled variables are saved to `userpreferences.json` and requested from the API on the next fetch.

---

## Configuration

Edit `config.py` to change defaults:

| Setting | Description | Default |
|---------|-------------|---------|
| `refresh` | Auto-refresh interval (seconds) | `600` |
| `temp_unit` | Temperature unit | `°C` |
| `speed_unit` | Wind speed unit | `km/h` |
| `humidity_unit` | Humidity unit | `%` |
| `precip_unit` | Precipitation unit | `mm` |
| `theme` | Default theme | `textual-dark` |

User-added cities are stored in `cities.json` (created automatically). Your chosen theme is stored in `userpreferences.json` (created automatically).

---

## Project Structure

```
termweather/
├── main.py        # Entry point (TUI + --once test mode)
├── ui.py          # Textual TUI app (panels, keybindings, layout)
├── weather.py     # Data layer (Open-Meteo API calls)
├── config.py      # Settings + city persistence
└── cities.json    # Persisted user-added cities (auto-generated)
```

---

## Tech Stack

- **[Textual](https://textual.textualize.io/)** — terminal UI framework
- **[Open-Meteo](https://open-meteo.com/)** — free weather & geocoding API
- **[requests](https://docs.python-requests.org/)** — HTTP client

---

## Caching

To reduce API requests, weather data is cached **per city** for **1 hour**. When you switch back to a city that was fetched less than an hour ago, the cached data is shown without hitting the API again. Press **`Ctrl+F`** to force a fresh fetch that bypasses the cache. The cache is in-memory (cleared when the app exits) and lives in `weather.py` (`CACHE_TTL = 3600`).

---

## License

This project is licensed under the MIT License.
