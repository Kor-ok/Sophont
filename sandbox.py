from __future__ import annotations

from random import randint

from rich.pretty import pprint

from components.applied import UPP, GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode, GenderCode
from processors.inheritance import InheritanceProcessor
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


class Entities:
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
            entity_registry[entity] += (component,)
            return True
        except Exception:
            return False

    @staticmethod
    def remove_component(entity, component) -> bool:
        try:
            entity_registry[entity] = tuple(c for c in entity_registry[entity] if c != component)
            return True
        except Exception:
            return False

    @staticmethod
    def get_components_of_type(entity, component_type) -> tuple:
        try:
            return tuple(c for c in entity_registry[entity] if isinstance(c, component_type))
        except Exception:
            return ()


def generate_human_species() -> SpeciesCode:
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

    return species


def generate_test_species() -> SpeciesCode:
    species_guid = GUID.generate(
        ns1=GUID.NameSpaces.Entity.PACKAGES,
        ns2=GUID.NameSpaces.Owner.ENV,
        name="TestSpecies",
    )

    gene_characteristics_collection = [
        strength := SEMANTICS.create(type=CharacteristicCode, name="strength"),
        agility := SEMANTICS.create(type=CharacteristicCode, name="agility"),
        stamina := SEMANTICS.create(type=CharacteristicCode, name="stamina"),
        intelligence := SEMANTICS.create(type=CharacteristicCode, name="intelligence"),
        caste := SEMANTICS.create(type=CharacteristicCode, name="caste"),
        training := SEMANTICS.create(type=CharacteristicCode, name="training"),
        psionic := SEMANTICS.create(type=CharacteristicCode, name="psionic"),
        sanity := SEMANTICS.create(type=CharacteristicCode, name="sanity"),
    ]

    genes: tuple[GeneCode, ...] = ()

    gene_collection = [
        gene_strength := GeneCode(
            characteristic=gene_characteristics_collection[0],
            precedence=1,
            die_mult=2,
            gender_link=SEMANTICS.create(type=GenderCode, name="male"),
            characteristic_link=gene_characteristics_collection[4],
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_agility := GeneCode(
            characteristic=gene_characteristics_collection[1],
            precedence=1,
            die_mult=2,
            gender_link=SEMANTICS.create(type=GenderCode, name="female"),
            characteristic_link=None,
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_stamina := GeneCode(
            characteristic=gene_characteristics_collection[2],
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=None,
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_intelligence := GeneCode(
            characteristic=gene_characteristics_collection[3],
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=gene_characteristics_collection[0],
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_caste := GeneCode(
            characteristic=gene_characteristics_collection[4],
            precedence=1,
            die_mult=2,
            gender_link=SEMANTICS.create(type=GenderCode, name="donor"),
            characteristic_link=gene_characteristics_collection[4],
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_training := GeneCode(
            characteristic=gene_characteristics_collection[5],
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=None,
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_psionic := GeneCode(
            characteristic=gene_characteristics_collection[6],
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=None,
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
        gene_sanity := GeneCode(
            characteristic=gene_characteristics_collection[7],
            precedence=1,
            die_mult=2,
            gender_link=None,
            characteristic_link=None,
            contributor_pool_size=3,
            contributor_guid=species_guid,
        ),
    ]

    for gene in gene_collection:
        genes += (gene,)

    genotype = GenotypeCode(
        genes=genes,
        phenes=None,
    )

    species = SpeciesCode(
        genotype=genotype,
        identifying_guid=species_guid,
    )

    return species


if __name__ == "__main__":
    species = generate_test_species()

    print()

    genotype = InheritanceProcessor.species_to_genotype(species)
    pprint(genotype)

    # entity_name = "Test Entity"
    # entity = Entities.add_entity(entity_name)
    # # print(f"Created '{entity_name}' with ID: {entity}")

    # Entities.add_component(entity, species)

    # entity_species = Entities.get_components_of_type(entity, SpeciesCode)

    # upps: tuple[UPP, ...] = ()
    # for gene in entity_species[0].genotype.genes:
    #     rolled = apply_dice_rolls(gene.die_mult)
    #     for roll in rolled:
    #         upp = UPP(
    #             position=gene.characteristic.upp_position,
    #             value=roll,
    #         )
    #         upps += (upp,)
    # for phene in entity_species[0].genotype.phenes:
    #     rolled = apply_dice_rolls(phene.die_mult)
    #     upp = UPP(
    #         position=phene.characteristic.upp_position,
    #         value=sum(rolled),
    #     )
    #     upps += (upp,)

    # # Order by position
    # upps = tuple(sorted(upps, key=lambda x: x.position))
    # for upp in upps:
    #     Entities.add_component(entity, upp)

    # print("\nEntity Components:")
    # pprint(Entities().get_components_of_type(entity, UPP))
