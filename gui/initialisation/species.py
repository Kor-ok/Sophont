from __future__ import annotations

from collections import defaultdict
from random import choice, randint

from game.characteristic import Characteristic
from game.gene import Gene
from game.genotype import Genotype
from game.mappings.data import (
    AliasMappedFullCode,
    FullCode,
)
from game.mappings.set import ATTRIBUTES
from game.phene import Phene
from game.species import Species
from game.uid.guid import GUID, NameSpaces
from sophont.character import Sophont

CharacteristicName = str
CharacteristicCodeCollection = list[FullCode]

HUMAN_UUID = GUID.generate(ns1=NameSpaces.Entity.SPECIES, ns2=NameSpaces.Owner.ENV)
ALIEN_UUID = GUID.generate(ns1=NameSpaces.Entity.SPECIES, ns2=NameSpaces.Owner.ENV)
ASLAN_UUID = GUID.generate(ns1=NameSpaces.Entity.SPECIES, ns2=NameSpaces.Owner.ENV)

SPECIES_MAP: dict[str, int] = {
    "Human": HUMAN_UUID,
    "Alien": ALIEN_UUID,
    "Aslan": ASLAN_UUID,
}

def create_human_genotype() -> Genotype:
    
    # Let's first create a human genotype which will be a flyweight instance shared across 
    # all human sophonts.
    human_genes_by_name = [
        "Dexterity", 
        "Strength", 
        "Intelligence", 
        "Endurance",
        "Psionics",
        "Sanity"
        ] # Purposefully disordered compared to classical Traveller UPP indices.
    
    human_phenes_by_name = [
        "Education",
        "Social Standing",
        ]

    human_genotype = Genotype.by_characteristic_names(human_genes_by_name, human_phenes_by_name)

    return human_genotype

def create_random_genotype() -> Genotype:

    def _choose_random_codes_by_upp_index(
        entries: list[AliasMappedFullCode],
        *,
        expected_upp_indices: set[int] | None = None,
    ) -> CharacteristicCodeCollection:
        """Pick one FullCode per UPPIndexInt from a filtered view.

        The filtered view contains (alias_map, full_code) entries.
        We group by `full_code[0]` (UPPIndexInt) and choose a random option from the
        available sub_code variants.
        """
        by_upp_index: dict[int, list[FullCode]] = defaultdict(list)
        for _alias_map, code in entries:
            by_upp_index[int(code[0])].append(code)

        selected: CharacteristicCodeCollection = []
        upp_indices = sorted(by_upp_index.keys())
        for upp_index in upp_indices:
            selected.append(choice(by_upp_index[upp_index]))

        if expected_upp_indices is not None:
            missing = sorted(set(expected_upp_indices) - set(by_upp_index.keys()))
            if missing:
                raise RuntimeError(
                    "Filtered view did not contain any entries for upp_indices="
                    f"{missing}. Present={upp_indices}"
                )

        return selected

    def _random_bag() -> tuple[set[int], set[int]]:
        gene_rand_1 = {1, 2, 3, 4, 7}
        phene_rand_1 = {5, 6, 8}

        gene_rand_2 = {1, 2, 3, 4, 5, 7}
        phene_rand_2 = {6, 8}
        return choice([(gene_rand_1, phene_rand_1), (gene_rand_2, phene_rand_2)])

    gene_filter, phene_filter = _random_bag()

    filter_criteria_for_genes = {0: gene_filter}

    filtered_view_for_genes = (
        ATTRIBUTES.characteristics.combined_collection.get_filtered_collection(
            criteria=filter_criteria_for_genes
        )
    )

    filter_criteria_for_phenes = {0: phene_filter}

    filtered_view_for_phenes = (
        ATTRIBUTES.characteristics.combined_collection.get_filtered_collection(
            criteria=filter_criteria_for_phenes
        )
    )

    characteristics_by_upp_index_genes = _choose_random_codes_by_upp_index(
        list(filtered_view_for_genes),
        expected_upp_indices=gene_filter,
    )

    characteristics_by_upp_index_phenes = _choose_random_codes_by_upp_index(
        list(filtered_view_for_phenes),
        expected_upp_indices=phene_filter,
    )

    _inheritance_contributors = randint(0, 10)

    def _create_random_gene(code: FullCode) -> Gene:
        characteristic = Characteristic.by_code(code)
        die_mult = randint(1, 6)
        precidence = randint(-1, 1)
        inheritance_contributors = _inheritance_contributors
        gender_link = randint(-1, _inheritance_contributors)
        caste_link = randint(-1, 16)
        return Gene(
            characteristic=characteristic,
            die_mult=die_mult,
            precidence=precidence,
            gender_link=gender_link,
            caste_link=caste_link,
            inheritance_contributors=inheritance_contributors,
        )

    genes = [_create_random_gene(code) for code in characteristics_by_upp_index_genes]
    phenes = [Phene.by_characteristic_code(code) for code in characteristics_by_upp_index_phenes]
    return Genotype.of(genes, phenes)

def create_alien_genotype() -> Genotype:
    # Let's make a non-default Caste gene that it gets from a THIRD parent i.e. inheritance_contributors = 3
    # And has a die multiplier of 3
    # Make it a -1 precidence
    # And make the caste_link (arbitrarily) 4 i.e. the fourth caste

    alien_caste_gene = Gene(
        characteristic=Characteristic.by_name("Caste"),
        die_mult=3,
        precidence=-1,
        caste_link=4,
        inheritance_contributors=3
    )

    alien_genes_by_name = [
        "Strength", 
        "Agility", 
        "Stamina",
        "Intelligence",
        "Instinct",
        "Sanity",
        ]
    
    alien_phenes_by_name = [
        "Psionics",
        ]

    alien_genotype = Genotype.by_characteristic_names(alien_genes_by_name, alien_phenes_by_name, custom_genes=[alien_caste_gene])

    return alien_genotype

def create_aslan_genotype() -> Genotype:
    # Let's create a custom Phene for TER that works alongside Social Standing
    # to stress test the underlying model logic and validation. Multiple Genes
    # of the same UPP Index is NOT allowed, but multiple Phenes of the same UPP
    # Index is allowed.

    ATTRIBUTES.characteristics.add_custom_entry(
        alias_map={"ter": ("territory", "territoriality")},
        full_code=(6, 3, 3),
    )
    ter_characteristic = Characteristic.by_name("ter") # This subtype is not in the base mappings.
    ter_phene = Phene(characteristic=ter_characteristic)
    aslan_genes_by_name = [
        "Strength", 
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Sanity",
    ]
    aslan_phenes_by_name = [
        "Education",
        "Social Standing",
    ]
    aslan_genotype = Genotype.by_characteristic_names(
        aslan_genes_by_name,
        aslan_phenes_by_name,
        custom_phenes=[ter_phene]
    )

    return aslan_genotype


def create_species_with_human_genotype() -> Species:
    human_genotype = create_human_genotype()
    human_species = Species(genotype=human_genotype, uuid=HUMAN_UUID)
    return human_species

def create_species_with_random_genotype() -> Species:
    random_genotype = create_random_genotype()
    random_species = Species(genotype=random_genotype, uuid=ALIEN_UUID)
    return random_species

def create_species_with_alien_genotype() -> Species:
    alien_genotype = create_alien_genotype()
    alien_species = Species(genotype=alien_genotype, uuid=ALIEN_UUID)
    return alien_species

def create_species_with_aslan_genotype() -> Species:
    aslan_genotype = create_aslan_genotype()
    aslan_species = Species(genotype=aslan_genotype, uuid=ASLAN_UUID)
    return aslan_species

example_sophont_1 = Sophont(species=create_species_with_human_genotype())
example_sophont_2 = Sophont(species=create_species_with_human_genotype())
example_sophont_3 = Sophont(species=create_species_with_random_genotype())
example_sophont_4 = Sophont(species=create_species_with_aslan_genotype())

CHARACTER_OPTIONS: dict[Sophont, str] = {
    example_sophont_1: "Human Sophont 1",
    example_sophont_3: "Alien Sophont",
    example_sophont_2: "Human Sophont 2",
    example_sophont_4: "Aslan Sophont",
}