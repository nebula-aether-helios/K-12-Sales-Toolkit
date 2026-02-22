#!/usr/bin/env bash
set -euo pipefail

# bootstrap_dev.sh
# POSIX bootstrap for offline-first development inside Linux devcontainer
# Usage: ./scripts/bootstrap_dev.sh

VENV_DIR=".venv"
PYTHON=${PYTHON:-python3}

echo "Starting bootstrap_dev.sh"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment: $VENV_DIR"
  $PYTHON -m venv "$VENV_DIR"
else
  echo "Virtual environment already exists: $VENV_DIR"
fi

# Activate and install
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

if [ -d "vendor_wheels" ]; then
  echo "Found vendor_wheels directory — installing from cache"
  pip install --no-index --find-links=vendor_wheels -r requirements.txt || true
elif [ -f requirements.txt ]; then
  echo "No vendor cache found. Attempting online install from PyPI (may require network)"
  pip install -r requirements.txt || true
  echo "If you have network access and want offline installs later, run on a connected machine: pip download -r requirements.txt -d vendor_wheels"
else
  echo "No requirements.txt found — skipping Python package install"
fi

# Prepare .env from example if present
if [ -f .env.example ] && [ ! -f .env ]; then
  cp .env.example .env
  echo "Copied .env.example to .env (please edit and add real secrets as needed)"
fi

echo "Bootstrap complete. Next steps:"
echo "  . $VENV_DIR/bin/activate  # activate the venv"
echo "  # (optional) start local emulators if available, e.g. Azurite or Functions Core Tools"

echo "Done."