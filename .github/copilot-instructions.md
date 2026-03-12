# Project Guidelines

## Scope
This repository is a rapidly-iterable Python sandbox for Traveller 5 sophont modeling.

Treat this codebase as systems-style Python: explicit, type-driven, low-dynamic, and data-first. Prefer closed sets of known component types, immutable structures, slot-based layouts, and validated construction over Python’s permissive dynamic patterns.

Default to the active code paths:
- `components/`
- `processors/`
- `semantics/`
- `humaniseT5/`
- `api/`
- `utils/`
- `data/`

Treat these areas as non-default targets unless a task explicitly requires them:
- `_deprecated/`
- `_learning/`
- `_prototypes/`
- `_tests/`

## Architecture
  `components/` is the active domain model.
  `primitives.py` defines primitive codes backed by canonical T5 semantics.
  `applied.py` defines composed or runtime-applied components such as `GeneCode`, `PheneCode`, `SpeciesCode`, and `UPP`.
  `__init__.py` provides the component decorator. It behaves like a frozen dataclass with slot support and optional flyweight caching.
  `base.py` builds subclass registries and semantic maps for Primitive and Applied types at class creation time.
  `definitions.py` owns the SEMANTICS singleton and loads canonical definitions at import time.
  `processors/` contains business logic. `inheritance.py` is the main active processor.
  `species.py` and `data/species/` are the active species construction path.
  `humaniseT5/` and `api/` contain T5 integration, authoring, and helper logic.

## Build And Validation
Use the virtual environment interpreter:

- `.venv\Scripts\python.exe -m pip install -r requirements.txt`
- `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`
- `.venv\Scripts\python.exe -m ruff check --fix <paths>`
- `.venv\Scripts\python.exe -m black <paths>`
- `.venv\Scripts\python.exe -m ruff check <paths>`

Project defaults:

  Target Python 3.9 compatibility.
  Ruff and Black are the primary validation tools.
  There is no dependable automated test suite yet. Treat `_tests/` as exploratory.
  `runner.py` is the live development runner. Use it to hot-reload and repeatedly execute experimental entry-point scripts such as `sandbox.py` or `experiment.py`. Once behavior stabilizes, move the implementation into the appropriate package.

## Conventions
Use Python in a statically constrained, data-oriented style.

Prefer explicit domain types over shapeless dictionaries.
Prefer frozen or effectively immutable objects over mutable ad hoc state.
Prefer slot-based or otherwise constrained layouts where the pattern already exists.
Prefer validated construction paths over dynamic attribute injection.
Avoid Any-heavy APIs unless a task explicitly requires flexibility.
Avoid implicit runtime polymorphism when a closed set of domain types is known.

Repository-specific rules:

  Preserve the component decorator pattern where it already exists.
  Keep the distinction between Primitive and Applied types explicit.
  Extend authored data and definition-loading paths before hardcoding new Traveller values in processors.
  Make local changes. Do not broad-refactor unless the task explicitly asks for it.
  Keep type hints Python 3.9 compatible.
  Use local imports when they reduce coupling or circular-import risk.
  For GUID compatibility shims, declare aliased class attributes on the class body before module-scope assignment so Pylance resolves them correctly.

## Pitfalls
Do not assume legacy documentation reflects the active architecture.
Do not add new work to `_deprecated/` unless the task is explicitly about migration or legacy support.
Do not reference nonexistent active packages such as `game`, `sophont`, `gui`, or `t5` when writing new code.
Do not treat `pyproject.toml` Ruff first-party settings as an authoritative map of the current package layout.
`definitions.py` initializes global state at import time, so be careful with import order and startup side effects.

## Representative Files
Inspect these first when inferring patterns:

  `__init__.py`
  `base.py`
  `primitives.py`
  `applied.py`
  `species.py`
  `inheritance.py`
  `definitions.py`
  `runner.py`
  `experiment.py`