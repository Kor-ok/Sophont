# Contributing

This repo is intended as a fast sandbox for iterating on the Traveller 5 “Sophont” domain model.

## Architectural Context

The codebase uses **Object-Oriented design as a deliberate stepping stone** toward an Entity-Component-System (ECS) architecture. Current patterns are chosen to translate naturally to ECS:

- **Flyweight/interned immutable data** → future *Components*
- **Mutable character state in time-ordered collections** → future *Entities*
- **Collation/update logic in dedicated methods** → future *Systems*

See README.md for full architectural philosophy.

## Setup

- Runtime dependencies:
  - `pip install -r requirements.txt`
- Optional dev tooling:
  - `pip install -r requirements-dev.txt`

## Conventions

- Prefer small, explicit types.
- Keep **immutable rules-data** (flyweights) separate from **mutable character state**.
- Respect the three state domains on a Sophont: **Aptitudes**, **Epigenetics**, **Personals**.
- When extending tables, keep them in `game/mappings/`.
- First-party imports: `game`, `sophont`, `gui`, `t5`.

## Useful checks

- Syntax / import sanity:
  - `python -m compileall -q .`

- Lint (with auto-fix):
  - `ruff check --fix .`

- Format:
  - `black .`

- Verify lint clean:
  - `ruff check .`
