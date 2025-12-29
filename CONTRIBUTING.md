# Contributing

This repo is intended as a fast sandbox for iterating on the Traveller 5 “Sophont” domain model.

## Setup

- Runtime dependencies:
  - `pip install -r requirements.txt`
- Optional dev tooling:
  - `pip install -r requirements-dev.txt`

## Conventions

- Prefer small, explicit types.
- Keep **immutable rules-data** (flyweights) separate from **mutable character state**.
- When extending tables, keep them in `game/mappings/`.

## Useful checks

- Syntax / import sanity:
  - `python -m compileall -q .`

- Lint:
  - `ruff check .`

- Format:
  - `black .`
