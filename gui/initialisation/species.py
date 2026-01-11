from __future__ import annotations

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

def create_species_with_alien_genotype() -> Species:
    alien_genotype = create_alien_genotype()
    alien_species = Species(genotype=alien_genotype, uuid=ALIEN_UUID)
    return alien_species

def create_species_with_aslan_genotype() -> Species:
    aslan_genotype = create_aslan_genotype()
    aslan_species = Species(genotype=aslan_genotype, uuid=ASLAN_UUID)
    return aslan_species

example_sophont_1 = Sophont(species_genotype=create_species_with_human_genotype())
example_sophont_2 = Sophont(species_genotype=create_species_with_human_genotype())
example_sophont_3 = Sophont(species_genotype=create_species_with_alien_genotype())
example_sophont_4 = Sophont(species_genotype=create_species_with_aslan_genotype())

CHARACTER_OPTIONS: dict[Sophont, str] = {
    example_sophont_1: "Human Sophont 1",
    example_sophont_2: "Human Sophont 2",
    example_sophont_3: "Alien Sophont",
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