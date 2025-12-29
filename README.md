
# Sophont (Traveller 5 character sandbox)

This repository is a **quickly-iterable Python codebase for designing the classes, data structures, and logic** needed to manipulate a *Sophont* (a character) that follows the rules and concepts of **Traveller 5 (T5)**.

The primary focus is on building a clean, extensible object model (and supporting mapping tables) that can evolve quickly while you refine how “character math” and “character state” should work.

## Status / Scope

- This is **not** a complete game, UI, or character generator.
- Much of the project is intentionally “model-first”: data types, packages, and collation layers.
- Some higher-level computed layers (e.g. phenotype collation in epigenetics) are **TODO** and still evolving.

## Key Ideas (current architecture)

### Two “state domains” on a Sophont

- **Aptitudes** (skills/knowledge, training progress, computed levels)
- **Epigenetics** (genotype as a blueprint + acquired characteristic packages over time)

The top-level class is `sophont.character.Sophont`.

### Flyweight immutable items + mutable “applied” state

Many core entities are implemented as immutable, interned *flyweights*:

- `game.skill.Skill` (interned by code)
- `game.knowledge.Knowledge` (interned by identity key)
- `game.characteristic.Characteristic`
- `game.gene.Gene`
- `game.phene.Phene`
- `game.genotype.Genotype`

Mutable “character state” is expressed via **acquired packages** over time:

- `game.aptitude_package.AptitudePackage` modifies a `Skill` / `Knowledge`
- `game.characteristic_package.CharacteristicPackage` modifies a `Gene` / `Phene`

### Collation layers

`sophont.aptitudes.Aptitudes` keeps a time-ordered collection of acquired packages and can build a summarized list of unique applied aptitudes (e.g. total computed skill level) via `update_collation()`.

## Installation

Recommended: Python 3.9+.

```bash
pip install -r requirements.txt
```

The only third-party runtime dependency currently is `sortedcontainers`.

## Quick Start

Create a minimal species genotype, then create a `Sophont`, then apply an aptitude package:

```python
from game.genotype import Genotype
from sophont.character import Sophont

from game.skill import Skill
from game.aptitude_package import AptitudePackage

# Traveller-style base characteristic names are mapped in game/mappings/characteristics.py
species_genotype = Genotype.by_gene_characteristic_names(
		[
				"strength",
				"dexterity",
				"endurance",
				"intelligence",
				"education",
				"social standing",
				"psionics",
				"sanity",
		]
)

s = Sophont(species_genotype=species_genotype, name="Ria", age_seconds=18 * 365 * 24 * 3600)

# Acquire a skill package at current age (example skill code; see game/mappings/skills.py)
basic_training = AptitudePackage(item=Skill(38), level=1, context="Basic Training")
s.aptitudes.insert_package_acquired(basic_training, age_acquired_seconds=s.age_seconds)

s.aptitudes.update_collation()
print(s)
print(s.aptitudes.aptitude_collation)
```

## Project Layout

- `sophont/`
	- Character-facing domain objects (e.g. `Sophont`, `Aptitudes`, epigenetics profile)
- `game/`
	- Immutable “rules data” types (skills, knowledges, characteristics, genes, phenes)
	- Package types that apply deltas over time
	- Mapping tables in `game/mappings/` (name/code tables and lookup helpers)

## Notes

- The code intentionally prefers **small, explicit types** and predictable behavior over “one giant character class”.
- Interning/flyweight patterns are used to make it cheap to reference the same rules-data objects across many characters.

## License

None

