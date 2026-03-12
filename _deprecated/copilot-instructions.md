# Project Guidelines

## Scope

This repository is a rapidly-iterable Python sandbox for Traveller 5 sophont modeling.
The active codebase is no longer the older `sophont/game/gui/t5` layout documented in legacy notes.

Treat this codebase as systems-style Python: explicit, type-driven, low-dynamic, and data-first. Prefer closed sets of known component types, immutable structures, and validated construction over Python’s more permissive dynamic patterns.

Default to the active packages and scripts:
- `components/`
- `processors/`
- `semantics/`
- `humaniseT5/`
- `api/`
- `utils/`
- `data/`

Treat these areas as archival or exploratory unless the task explicitly targets them:
- `_deprecated/`
- `_learning/`
- `_prototypes/`
- `_tests/`

## Architecture

- `components/` defines the current domain model.
  - `components/primitives.py` contains primitive codes backed by canonical T5 semantics.
  - `components/applied.py` contains composed or runtime-applied components such as `GeneCode`, `PheneCode`, `SpeciesCode`, and `UPP`.
- `components/__init__.py` provides the `@component` decorator. It behaves like a frozen dataclass with slot support and optional flyweight caching.
- `components/base.py` builds semantic maps and subclass registries for `Primitive` and `Applied` types at class creation time.
- `semantics/definitions.py` owns the runtime `SEMANTICS` singleton that loads canonical definitions and is treated as immutable after initialization.
- `processors/` holds business logic. `processors/inheritance.py` is the main active processor and converts species/genotype data into inherited UPP values.
- `components/factories/species.py` and JSON files under `data/species/` are the current path for constructing runtime species data.
- `humaniseT5/` and `api/` provide authoring, lookup, and T5 integration helpers.


## Build And Validation

Use the virtual environment interpreter to avoid tool-version churn:
- `.venv\Scripts\python.exe -m pip install -r requirements.txt`
- `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`
- `.venv\Scripts\python.exe -m ruff check --fix <paths>`
- `.venv\Scripts\python.exe -m black <paths>`
- `.venv\Scripts\python.exe -m ruff check <paths>`

Project defaults:
- Python 3.9 compatibility matters.
- Ruff and Black are the primary validation tools.
- There is no reliable automated test suite yet. `_tests/` is exploratory, and `pytest` is a dependency rather than a dependable project workflow.

`runner.py` is the live development runner. It exists to hot-reload and repeatedly execute experimental entry-point scripts such as `sandbox.py` or `experiment.py` while behavior is being explored. Once an approach stabilizes, the implementation is moved into the appropriate package. This allows for rapid iteration with any relevant module or approach being introduced without worrying about test scaffolding or maintaining a stable API during early exploration.

## Conventions

Use Python in a statically constrained, data-oriented style. Prefer explicit domain types, frozen or effectively immutable objects, slot-based layouts, and well-defined construction paths. Avoid dynamic attribute injection, shapeless dictionaries as core domain objects, permissive Any-heavy APIs, and implicit runtime polymorphism unless a task explicitly requires them.

- Preserve the `@component` pattern where it already exists. Do not replace component classes with ad hoc mutable classes unless the task requires it.
- Keep the distinction between `Primitive` and `Applied` types clear.
  - Primitive components map directly to canonical semantics.
  - Applied components compose primitive data or represent derived runtime state.
- Prefer extending authored data and definition-loading paths over hardcoding new Traveller rules values in business logic.
- Avoid broad refactors while the repository is still iterating on structure. Make minimal, local changes unless the prompt explicitly asks for reorganization.
- Use type hints when they improve clarity, but keep them Python 3.9 compatible.
- Prefer focused helper functions and local imports when they reduce coupling or circular-import risk.
- When modifying GUID compatibility shims, remember that Pylance in this repo does better when aliased class attributes are declared on the class body before module-scope assignment.

## Pitfalls

- Do not assume the legacy architecture in older docs is still active.
- Do not add new work to `_deprecated/` unless the task is explicitly about migration or legacy support.
- Do not reference nonexistent active packages such as `game`, `sophont`, `gui`, or `t5` when writing new code.
- Do not trust `pyproject.toml`'s current Ruff first-party module list as an accurate map of the live package layout; verify imports against the actual workspace.
- `semantics/definitions.py` initializes global state at import time, so be careful about import order and side effects in startup code.

## Representative Files

Use these files to infer current patterns before making larger changes:
- `components/__init__.py`
- `components/base.py`
- `components/primitives.py`
- `components/applied.py`
- `components/factories/species.py`
- `processors/inheritance.py`
- `semantics/definitions.py`
