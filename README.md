# Sophont Object Model Design Sandbox (Traveller 5 character rules)

Purpose: **quickly-iterable Python codebase for designing the classes, data structures, and logic** to model an RPG character for the Traveller 5 ruleset. Intention of design during the initial Object Oriented approach is to verge on an easy transition into a Data Oriented Entity Component System architecture while maintaining a TypeScript port branch.

A NiceGUI **interface to communicate and demonstrate** concepts that runs in browser. ***NOTE:*** *Not intended as a final framework to implement the data model.*

## Status / Scope

- A **very basic MVP**: `Sophont` owns *Aptitudes* (Collections of Skill/Knowledge/Certification Packages that have been acquired by the character over its lifetime), *Epigenetics* (Characteristics derived from collections of "Gene" and "Phene" Packages) and *Personals* (Granular modifiers for the above through character states logic, inventory and character location tracking) with their respective data structures and collation logic.
- Intentionally “model-first”: data types, packages, and collation layers.
- Time Ordered Packages compose a character history
- Packages can be authored to hold unique references like the context by which a character obtained it through a custom GUID system.
- Some higher-level computed layers (e.g. automatically generating inherited packages / phenotype math, attribute training) are **TODO** and still evolving.

## Design Principles

- The code intentionally prefers **small, explicit types** and predictable behavior over “one giant character class”.
- Interning/flyweight patterns are used to make it cheap to reference the same rules-data objects across many characters.
- Memory Efficiency is being prioritised to allow for large numbers of character entities that share building blocks. Debugging and Game Balancing is simplified as many of these flyweight objects will be authored, i.e. 
  - a Skill Package that can be earned under certain conditions during Character Creation
  - Gene Packages that are shared by characters of the same Species or family. A foundation also for Traveller 5 chimera or mutation rules.
  - Aptitudes or Characteristics that are "grafted" allowing for Traveller 5 personality wafer rules

## Key Ideas (current architecture)
![Concept Map](/ConceptMap.jpg)
### High-level Concept

The design splits the world into two layers:

1. **Immutable rules-data (flyweights)**: 
   1. ***PRIMITIVE ATTRIBUTES:*** skills, knowledges, characteristics
   2. ***APPLIED ATTRIBUTES:*** genes, phenes, species, genotype
   3. ***PACKAGES:*** higher level packages/events containing the flyweights for ad-hoc application to the character.
   - ***To transition to Components in ECS architecture.***
2. **Mutable character state**: the character’s time-ordered acquired packages, plus cached “collated” summaries.
   - ***To transition to Entities in ECS architecture.***

### Three “state domains” on a Sophont

- **Aptitudes** (skills/knowledge, training progress, computed levels) 

![Aptitudes Class Map](/ClassMap_Aptitudes.jpg)
- **Epigenetics** (genotype as a blueprint + acquired gene/phene packages over time, collated into computed characteristic levels)
  - Note on terminology: **“Phene”** is used as an “atom” of the "expressed phenotype" — a smallest, composable unit of a expressed characteristic (i.e. Strength, Agility, Caste, etc) that can be applied/collated (often alongside `Gene`) to compute effective characteristics.

![Epigenetics Class Map](/ClassMap_Epigenetics.jpg)

- **Personals** (acquired characteristics packages constrained by Epigenetics over time, specifically for granular state management where packages can act as temporary modifiers. For instance, T5 Personal Day and T5 burden tracking. Packages here will include as yet implemented Location, Injury, etc tracking.)

The top-level class is `sophont.character.Sophont`.

### Flyweight immutable items + mutable “applied” state

Many core entities are implemented as immutable, interned *flyweights*:

Aptitudes:
- `game.skill.Skill` (interned by code)
- `game.knowledge.Knowledge` (interned by identity key)

Epigenetics:
- `game.gene.Gene`
- `game.phene.Phene`
- `game.species.Species`
- `game.genotype.Genotype`

Pure Characteristics:
- `game.characteristic.Characteristic`

Packages/Events:
- `game.package.AttributePackage`
- `game.event.Event`

Mutable “character state” is expressed via **acquired packages** over time:

- `game.aptitude_package.AptitudePackage` modifies a `Skill` / `Knowledge`
- `game.characteristic_package.CharacteristicPackage` modifies a `Gene` / `Phene`

### Collation layers

`sophont.aptitudes.Aptitudes` keeps a time-ordered collection of acquired packages and can build a summarized list of unique applied aptitudes (e.g. total computed skill level) via `update_collation()`.

Similarly, `sophont.epigenetics.Epigenetics` keeps a time-ordered collection of acquired characteristic packages and collates them into a computed list of effective characteristics via `update_collation()`.

`sophont.personals.Personals` (TO BE FULLY IMPLEMENTED) keeps time-ordered collections of acquired attribute packages (abstracted Aptitudes and Characteristics Based data), `personal_day` tracking and `locations` tracking.

## Project Notes

Recommended: Python 3.9+.

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Third-party runtime dependencies:
`sortedcontainers`
`nicegui`
`humanizer`

Development specific dependencies:
`ruff`
`black`
`mypy`
`pytest`
`pandas`
`openpyxl`
`Pympler`


## Project Layout

- `sophont/`
	- Character-facing domain objects (e.g. `Sophont`, `Aptitudes`, epigenetics profile)
- `game/`
	- Immutable “rules data” types (skills, knowledges, characteristics, genes, phenes)
	- Package types that apply deltas over time
	- Mapping tables in `game/mappings/` (name/code tables and lookup helpers)
	- GUID system `game/uid/`
- `t5/`
  - Isolated module for humanisation helpers related to T5 data types and logic
- `gui/`
  - NiceGUI related