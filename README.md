# Vanta

Local-first terminal AI client for Ollama.

*Note: Ollama integration is not yet implemented.*

## Prerequisites
- Python 3.14+
- `direnv` installed and allowed

## Initial Setup
1. `direnv allow`
2. `./setup_and_test.sh` (this will create .venv if missing, install dependencies, and run tests)

If not using `direnv`:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Launch
```bash
python3 -m vanta.app
```

## Testing
```bash
pytest tests/
```
