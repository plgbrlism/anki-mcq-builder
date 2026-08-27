#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" &>/dev/null; then
  echo "Error: $PYTHON not found. Install Python 3.11+ first."
  exit 1

fi

PYMAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PYMINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

if [ "$PYMAJOR" -lt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 11 ]; }; then
  echo "Error: Python 3.11+ required, found $("$PYTHON" --version)"
  exit 1
fi

echo "Using $("$PYTHON" --version)"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate

echo "Installing anki-mcq-builder..."
pip install -e .

echo ""
echo "Done. Run: source .venv/bin/activate && anki-mcq-builder --help"
