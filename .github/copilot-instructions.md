# Copilot Instructions (Sophont / Traveller 5)

## Project Intent

This repo is a **rapidly-iterable sandbox** for designing Python classes and supporting tables used to model a *Sophont* (character) according to **Traveller 5 (T5)** concepts.

Primary goals:
- Keep the domain model **easy to refactor** as rules interpretation evolves.
- Prefer **clear data types** and predictable behavior over “magic”.
- Separate **immutable rules-data** (skills, characteristics, genes) from **mutable character state** (acquired packages, training progress).

Non-goals (unless explicitly requested):
- Full character generator UI
- Complete T5 rules implementation
- Persistence, database, or networking

## Architecture Snapshot

Top-level domains:
- `sophont/` — character-facing domain objects
  - `sophont.character.Sophont` is the main entry point
  - `sophont.aptitudes.Aptitudes` summarizes learned skills/knowledge
  - `sophont.epigenetics.EpigeneticProfile` tracks genotype + acquired characteristic packages (phenotype collation is TODO)

- `game/` — immutable rules-data + packages + mapping tables
  - Flyweight immutable items: `Skill`, `Knowledge`, `Characteristic`, `Gene`, `Phene`, `Genotype`
  - Package containers applied over time: `AptitudePackage`, `CharacteristicPackage`
  - Lookup tables/helpers live under `game/mappings/`

## Coding Conventions

When modifying or adding code:
- Preserve the “**flyweight immutable item**” pattern where it already exists.
  - Use `__slots__` consistently.
  - Initialize immutable fields in `__new__` and keep `__init__` as `pass` where the pattern is used.
  - Prefer deterministic caching keys (tuples of primitive or flyweight items).

- Keep mutable state in dedicated containers:
  - Time-ordered acquired collections (e.g., `SortedKeyList`) are preferred for incremental updates.
  - Collation/summarization should be recomputed only when flagged dirty.

- Avoid introducing new dependencies unless they materially reduce complexity.

- Prefer type hints and small helper functions when they improve clarity.

## Style / Formatting

- Python: 4-space indentation.
- Keep modules focused; avoid circular imports (use local imports where necessary).
- Use docstrings when adding new public classes/functions.

## Safety Rails

- Do not “invent” new rules values or tables. If a mapping/table needs extending, place it under `game/mappings/` and keep changes minimal.
- Don’t refactor broadly unless the prompt explicitly asks for it.

## Quick Commands (typical)

- Install runtime deps: `pip install -r requirements.txt`
- Optional dev tools (if present): `pip install -r requirements-dev.txt`
