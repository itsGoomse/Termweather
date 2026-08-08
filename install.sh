#!/usr/bin/env bash
#
# install.sh — Set up the weatherterm project and its dependencies.
#
# Detects whether `uv` or `pip` is available and uses whichever is present.
#   - uv  -> `uv sync` (creates .venv and installs deps from pyproject.toml)
#   - pip -> creates a venv, activates it, and `pip install -e .`
#
# Usage:
#   ./install.sh
#   ./install.sh --once   # run the TUI once after installing
#

set -euo pipefail

# --- Colours (only when stdout is a TTY) -------------------------------------
if [[ -t 1 ]]; then
    C_RESET=$'\033[0m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_CYAN=$'\033[36m'
    C_RED=$'\033[31m'
else
    C_RESET=""
    C_GREEN=""
    C_YELLOW=""
    C_CYAN=""
    C_RED=""
fi

info()  { printf '%s[INFO]%s %s\n'  "$C_CYAN"   "$C_RESET" "$*"; }
ok()    { printf '%s[ OK ]%s %s\n'  "$C_GREEN"  "$C_RESET" "$*"; }
warn()  { printf '%s[WARN]%s %s\n'  "$C_YELLOW" "$C_RESET" "$*"; }
die()   { printf '%s[FAIL]%s %s\n'  "$C_RED"    "$C_RESET" "$*" >&2; exit 1; }

# --- Locate the script's directory ------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check for a Python interpreter -----------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    die "No Python interpreter found. Please install Python 3.15+ first."
fi

info "Using Python: $("$PYTHON" --version 2>&1)"

# --- Choose the package manager ---------------------------------------------
if command -v uv >/dev/null 2>&1; then
    PM="uv"
    info "Detected 'uv' — using it to manage the environment."
elif command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1; then
    PM="pip"
    info "No 'uv' found — falling back to 'pip'."
else
    die "Neither 'uv' nor 'pip' was found. Please install one of them first."
fi

# --- Install dependencies ----------------------------------------------------
case "$PM" in
    uv)
        info "Running 'uv sync'..."
        uv sync
        ok "Dependencies installed with uv."
        ;;
    pip)
        if [[ ! -d ".venv" ]]; then
            info "Creating virtual environment with $PYTHON..."
            "$PYTHON" -m venv .venv
        else
            info "Virtual environment '.venv' already exists — reusing it."
        fi

        # shellcheck disable=SC1091
        source .venv/bin/activate

        info "Upgrading pip and installing the project in editable mode..."
        python -m pip install --upgrade pip
        python -m pip install -e .
        ok "Dependencies installed with pip."
        ;;
esac

# --- Optional: run the TUI once ---------------------------------------------
if [[ "${1:-}" == "--once" ]]; then
    info "Launching weatherterm..."
    case "$PM" in
        uv) uv run python main.py ;;
        pip) python main.py ;;
    esac
fi

ok "Installation complete. Run the app with:"
case "$PM" in
    uv)  printf '    %suv run python main.py%s\n' "$C_GREEN" "$C_RESET" ;;
    pip) printf '    %ssource .venv/bin/activate && python main.py%s\n' "$C_GREEN" "$C_RESET" ;;
esac
