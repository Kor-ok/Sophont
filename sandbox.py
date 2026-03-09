from __future__ import annotations

from random import randint

from rich.pretty import pprint

from components.applied import UPP, GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode
from semantics.definitions import SEMANTICS
from utils.guid import GUID


def display_species_info(species: SpeciesCode) -> None:
    print(f"Species Name: {species.identifying_guid.uid_to_string}")
    print("Genes:")
    for gene in species.genotype.genes:
        semantics = SEMANTICS.of(gene.characteristic)
        canonical = semantics[CharacteristicCode]["canonical"]
        print(canonical)
    print("Phenes:")
    for phene in species.genotype.phenes:
        semantics = SEMANTICS.of(phene.characteristic)
        canonical = semantics[CharacteristicCode]["canonical"]
        print(canonical)


def apply_dice_rolls(die_mult: int) -> tuple[int, ...]:
    values = []
    for _ in range(die_mult):
        roll = randint(1, 6)
        values.append(roll)
    return tuple(values)


entity_registry = {}


class DemoEntity:
    """Experimental ECS entity manager for testing the applied components."""

    @staticmethod
    def add_entity(name: str) -> int:
        id = GUID.generate(
            ns1=GUID.NameSpaces.Entity.PACKAGES,
            ns2=GUID.NameSpaces.Owner.NPC,
            name=name,
        )
        try:
            entity_registry[id] = ()
            return id
        except Exception:
            return -1

    @staticmethod
    def add_component(entity, component) -> bool:
        try:
            # Add only the component signature to the entity registry for simplicity
            entity_registry[entity] += (component.component_signature,)
            return True
        except Exception:
            return False

    @staticmethod
    def remove_component(entity, component) -> bool:
        try:
            entity_registry[entity] = tuple(
                sig for sig in entity_registry[entity] if sig != component.component_signature
            )
            return True
        except Exception:
            return False


if __name__ == "__main__":
    test_caste_characteristic = SEMANTICS.create(type=CharacteristicCode, name="caste")

    species_guid = GUID.generate(
        ns1=GUID.NameSpaces.Entity.PACKAGES,
        ns2=GUID.NameSpaces.Owner.ENV,
        name="Human",
    )

    gene_characteristics_collection = [
        strength := SEMANTICS.create(type=CharacteristicCode, name="strength"),
        dexterity := SEMANTICS.create(type=CharacteristicCode, name="dexterity"),
        endurance := SEMANTICS.create(type=CharacteristicCode, name="endurance"),
        intelligence := SEMANTICS.create(type=CharacteristicCode, name="intelligence"),
        psionic := SEMANTICS.create(type=CharacteristicCode, name="psionic"),
        sanity := SEMANTICS.create(type=CharacteristicCode, name="sanity"),
    ]

    phene_characteristics_collection = [
        education := SEMANTICS.create(type=CharacteristicCode, name="education"),
        social := SEMANTICS.create(type=CharacteristicCode, name="social"),
    ]

    genes: tuple[GeneCode, ...] = ()
    phenes: tuple[PheneCode, ...] = ()

    for i, characteristic in enumerate(gene_characteristics_collection):
        gene = GeneCode(
            characteristic=characteristic,
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=None,
            contributor_pool_size=2,
            contributor_guid=species_guid,
        )
        genes += (gene,)

    for i, characteristic in enumerate(phene_characteristics_collection):
        phene = PheneCode(
            characteristic=characteristic,
            is_grafted=False,
            precedence=1,
            die_mult=2,
            contributor_guid=species_guid,
        )
        phenes += (phene,)

    genotype = GenotypeCode(
        genes=genes,
        phenes=phenes,
    )

    species = SpeciesCode(
        genotype=genotype,
        identifying_guid=species_guid,
    )

    print()

    upps: tuple[UPP, ...] = ()
    for gene in species.genotype.genes:
        rolled = apply_dice_rolls(gene.die_mult)
        for roll in rolled:
            upp = UPP(
                position=gene.characteristic.upp_position,
                value=roll,
            )
            upps += (upp,)
    for phene in species.genotype.phenes:
        rolled = apply_dice_rolls(phene.die_mult)
        upp = UPP(
            position=phene.characteristic.upp_position,
            value=sum(rolled),
        )
        upps += (upp,)

    # Order by position
    upps = tuple(sorted(upps, key=lambda x: x.position))

    entity_name = "Test Entity"
    entity = DemoEntity.add_entity(entity_name)
    print(f"Created '{entity_name}' with ID: {entity}")

    DemoEntity.add_component(entity, species)

    for upp in upps:
        DemoEntity.add_component(entity, upp)

    pprint(entity_registry.get(entity))
