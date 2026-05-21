# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

NeuroGame is a Python isometric game engine prototype with zero third-party dependencies (pure stdlib). See `README.md` for usage examples.

### Running tests

```bash
python3 -m unittest discover -s tests -v
```

Tests exercise only the engine/math modules and do **not** require a display or tkinter.

### Running the demo

```bash
DISPLAY=:1 python3 demo.py
```

Requires `python3-tk` (installed via the update script) and a running X display (`:1` is available in Cloud Agent VMs).

### Key notes

- The package is installed in editable mode (`pip install -e .`) so `src/neurogame/` is importable as `neurogame` without setting `PYTHONPATH`.
- There is no linter or formatter configured in the repository; the project uses only stdlib and `unittest`.
- No external services, databases, or Docker containers are needed.
