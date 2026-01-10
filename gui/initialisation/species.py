from __future__ import annotations

from nicegui import ui

import gui.draggable.fab as d_fab
from game.genotype import Genotype
from gui.draggable.drop_container import (
    handle_remove_requested,
    species_genotype_widget,
)


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
class premade_species_card(ui.column):
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