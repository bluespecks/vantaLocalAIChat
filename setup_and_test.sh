#!/bin/bash
set -e

# Create venv if not exists
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Run tests
pytest tests/test_app.py

echo "Setup and tests passed."
