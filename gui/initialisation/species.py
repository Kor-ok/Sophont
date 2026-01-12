from __future__ import annotations

from random import randint
from uuid import uuid4

from nicegui import ui

import gui.draggable.fab as d_fab
from game.characteristic import Characteristic
from game.gene import Gene
from game.genotype import Genotype
from game.phene import Phene
from game.species import Species
from gui.draggable.drop_container import (
    handle_remove_requested,
    species_genotype_widget,
)
from sophont.character import Sophont

HUMAN_UUID = uuid4().bytes
ALIEN_UUID = uuid4().bytes
ASLAN_UUID = uuid4().bytes

SPECIES_MAP: dict[str, bytes] = {
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
        "Endurance"
        ] # Purposefully disordered compared to classical Traveller UPP indices.
    
    human_phenes_by_name = [
        "Education",
        "Social Standing",
        "Psionics",
        "Sanity"
        ]

    human_genotype = Genotype.by_characteristic_names(human_genes_by_name, human_phenes_by_name)

    return human_genotype

def create_random_genotype() -> Genotype:
    from game.mappings.characteristics import codes_to_name

    collection = []
    for i in range(1, 9):
        char_name = codes_to_name(i, randint(0, 2))
        # if char_name == "Undefined": try again
        if char_name == "Undefined":
            i -= 1
            continue
        collection.append(char_name)

    _inheritance_contributors = randint(0, 10)

    def _create_random_gene(name: str) -> Gene:
        characteristic = Characteristic.by_name(name)
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
            inheritance_contributors=inheritance_contributors
        )
    bisect_at = randint(4, 6)
    genes = [_create_random_gene(name) for name in collection[:bisect_at]]
    phenes = [Phene.by_characteristic_name(name) for name in collection[bisect_at:]]
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
        ]
    
    alien_phenes_by_name = [
        "Psionics",
        "Sanity",
        ]

    alien_genotype = Genotype.by_characteristic_names(alien_genes_by_name, alien_phenes_by_name, custom_genes=[alien_caste_gene])

    return alien_genotype

def create_aslan_genotype() -> Genotype:
    # Let's create a custom Phene for TER that works alongside Social Standing
    # to stress test the underlying model logic and validation. Multiple Genes
    # of the same UPP Index is NOT allowed, but multiple Phenes of the same UPP
    # Index is allowed.

    ter_characteristic = Characteristic.of(upp_index=6, subtype=3, category_code=3) # This subtype is not in the base mappings.
    ter_phene = Phene(characteristic=ter_characteristic)
    aslan_genes_by_name = [
        "Strength", 
        "Dexterity",
        "Endurance",
        "Intelligence",
    ]
    aslan_phenes_by_name = [
        "Education",
        "Social Standing",
        "Psionics",
        "Sanity",
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
    example_sophont_3: "Alien Sophont",
    example_sophont_1: "Human Sophont 1",
    example_sophont_2: "Human Sophont 2",
    example_sophont_4: "Aslan Sophont",
}

class premade_non_editable_species_card(ui.column):
    def __init__(self, species_name: str, genotype: Genotype) -> None:
        super().__init__()
        self.genotype = genotype
        with self:
            widget = species_genotype_widget(name=species_name, is_instantiated=True, genotype=genotype)
            for gene in genotype.genes:
                with widget.collection:
                    d_fab.draggable(gene=gene, on_remove=handle_remove_requested, is_draggable_active=False).tooltip('Gene')
            for phene in genotype.phenes:
                with widget.collection:
                    d_fab.draggable(gene=phene, on_remove=handle_remove_requested, is_draggable_active=False).tooltip('Phene')