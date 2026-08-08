# 🌦️ TermWeather

A live-updating weather **TUI** (terminal user interface) built with [Textual](https://textual.textualize.io/). It pulls current conditions, a 5-day forecast, and a 24-hour breakdown from the free [Open-Meteo](https://open-meteo.com/) API — no API key required.

![Python](https://img.shields.io/badge/Python-3.15+-blue)
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

- Python 3.15+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/weatherterm.git
cd weatherterm

# Set up the environment with uv
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run the TUI

```bash
uv run python main.py
```

### Run a one-off data check (no TUI)

```bash
uv run python main.py --once "Holbæk"
```

---

## 🎮 Usage

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate the city list / table cells |
| `Enter` | Select a city from the list |
| `Tab` / `Shift+Tab` | Cycle between panels |
| `Esc` | Return focus to the city list |
| `q` / `Ctrl+C` | Quit |

**Add a city:** type a city name in the input at the bottom and press `Enter`. It will be added to the list and saved for next time.

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

User-added cities are stored in `cities.json` (created automatically).

---

## Project Structure

```
weatherterm/
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

## License

This project is licensed under the MIT License.
