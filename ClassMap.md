
# Class Map (MVP)

This document describes how the **current MVP** classes interact to model a `Sophont` with:

- **Aptitudes** (skills/knowledge)
- **Characteristics** (via epigenetics: genotype + acquired characteristic packages)

Scope: this intentionally excludes incomplete/adjacent domains (e.g. Species).

## High-level Concept

The design splits the world into two layers:

1. **Immutable rules-data (flyweights)**: skills, knowledges, characteristics, genes, phenes, genotype.
2. **Mutable character state**: the character’s time-ordered acquired packages, plus cached “collated” summaries.

Changes to a character (training, buffs/debuffs, events) are modeled as **packages acquired over time**. A collation step summarizes those packages into “effective state”.

Terminology note:

- **Phene** is an uncommon term. In this repository it is used as an “atom” of phenotype: a smallest, composable unit of expressed trait that can be applied/collated (often alongside `Gene`) to compute effective characteristics.

## Primary Objects

### Sophont (aggregate root)

- `Sophont` (sophont/character.py)
	- Owns mutable state:
		- `aptitudes: Aptitudes`
		- `epigenetic_profile: EpigeneticProfile`
	- Owns identity and narrative fields:
		- `uuid`, `name`, `age_seconds`

### Aptitudes (skills/knowledge state)

- `Aptitudes` (sophont/aptitudes.py)
	- `acquired_packages_collection`: time-ordered list of `Acquired(AptitudePackage, age, memo)`
	- `aptitude_collation`: cached list of `UniqueAppliedAptitude(item, computed_level, training_progress)`
	- `is_packages_dirty`: dirty flag controlling recomputation

Relevant immutable types:

- `AptitudePackage` (game/aptitude_package.py): immutable flyweight package
	- `item: Skill | Knowledge`
	- `level: int` (delta)
	- `context: str`
- `Skill` (game/skill.py): immutable flyweight
- `Knowledge` (game/knowledge.py): immutable flyweight

### EpigeneticProfile (characteristics state)

- `EpigeneticProfile` (sophont/epigenetics.py)
	- `genotype: Genotype` (immutable blueprint)
	- `acquired_packages_collection`: time-ordered list of `Acquired(CharacteristicPackage, age, memo)`
	- `characteristics_collation`: cached list of `UniqueAppliedCharacteristic(characteristic, computed_level, training_progress)`
	- `is_packages_dirty`: dirty flag controlling recomputation

Relevant immutable types:

- `Genotype` (game/genotype.py): immutable flyweight containing:
	- `genes: tuple[Gene, ...]`
	- `phenes: tuple[Phene, ...] | None`
- `CharacteristicPackage` (game/characteristic_package.py): immutable flyweight package
	- `item: Gene | Phene`
	- `level: int` (delta)
	- `context: str`
- `Gene` (game/gene.py): immutable flyweight; includes a `characteristic: Characteristic`
- `Phene` (game/phene.py): immutable flyweight; includes a `characteristic: Characteristic`
- `Characteristic` (game/characteristic.py): immutable flyweight

## Data Flow When Constructing a Sophont

### 1) Create immutable blueprint

1. Create (or look up) `Characteristic` flyweights by name/code.
2. Create `Gene` flyweights (each gene references a `Characteristic`).
3. Optionally create `Phene` flyweights (each phene references a `Characteristic`).
4. Create `Genotype(genes, phenes)`.

The genotype is a stable, shareable blueprint.

### 2) Instantiate character state

1. Create `Sophont(species_genotype=Genotype, ...)`.
2. `Sophont` constructs:
	 - `Aptitudes()` (empty acquisition timeline)
	 - `EpigeneticProfile(genotype)` (holds the genotype + empty acquisition timeline)

### 3) Apply changes as acquired packages

- Aptitudes:
	- Create `AptitudePackage(item=Skill|Knowledge, level=Δ, context=...)`
	- Insert into `Aptitudes.acquired_packages_collection` with `age_acquired_seconds`

- Characteristics:
	- Create `CharacteristicPackage(item=Gene|Phene, level=Δ, context=...)`
	- Insert into `EpigeneticProfile.acquired_packages_collection` with `age_acquired_seconds`

### 4) Collate (compute effective state)

- Call `aptitudes.update_collation()` to build `aptitude_collation`:
	- group by unique Skill/Knowledge item
	- sum package `level` deltas into `computed_level`
	- preserve `training_progress` from prior collation

- Call `epigenetic_profile.update_collation()` to build `characteristics_collation`:
	- each package targets a Gene/Phene, but collation groups by their shared `Characteristic`
	- sum package `level` deltas into `computed_level`
	- preserve `training_progress` from prior collation

## Mutability & Why It Matters

### Immutable (flyweight) objects

Immutable flyweights: `Skill`, `Knowledge`, `Characteristic`, `Gene`, `Phene`, `Genotype`, plus package definitions `AptitudePackage` and `CharacteristicPackage`.

Benefits:

- Safe to share across all characters.
- Stable identity/keys and no accidental cross-character mutation.
- Supports memory efficiency because “rules objects” are reused, not duplicated.

Drawbacks:

- You cannot “edit Strength”; you must apply changes via packages (which is intentional).

### Mutable character state

Mutable containers: `Sophont`, `Aptitudes`, `EpigeneticProfile`, and their `Acquired` wrappers and cached collation lists.

Benefits:

- Time-ordered acquisition makes “history” explicit.
- Dirty-flagged collation avoids recomputing summaries on every insert.

Drawbacks:

- Consumers must call `update_collation()` (or otherwise ensure collation is current) before relying on computed summaries.

## Diagram (Mermaid)

```mermaid
flowchart TD
		S[Sophont]
		A[Aptitudes]
		E[EpigeneticProfile]

		AP[AptitudePackage]
		CP[CharacteristicPackage]

		SK[Skill]
		KN[Knowledge]

		GT[Genotype]
		GE[Gene]
		PH[Phene]
		CH[Characteristic]

		AAcq[Acquired (aptitude)]
		EAcq[Acquired (characteristic)]

		ACol[UniqueAppliedAptitude (collation)]
		ECol[UniqueAppliedCharacteristic (collation)]

		S --> A
		S --> E

		A --> AAcq
		AAcq --> AP
		AP --> SK
		AP --> KN
		A --> ACol

		E --> GT
		GT --> GE
		GT --> PH
		GE --> CH
		PH --> CH

		E --> EAcq
		EAcq --> CP
		CP --> GE
		CP --> PH
		E --> ECol
		ECol --> CH
```

## “Buff/Debuff” Style Usage (MVP interpretation)

In this architecture, a “buff” or “debuff” is modeled as **acquiring one or more packages** that provide positive/negative deltas. Because the underlying items and packages are immutable flyweights, the per-character changes are mostly limited to:

- storing small acquisition records
- (re)computing cached summaries when needed

