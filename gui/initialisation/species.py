from __future__ import annotations

from nicegui import ui

import gui.draggable.fab as d_fab
from game.genotype import Genotype
from gui.draggable.drop_container import (
    handle_remove_requested,
    species_genotype_widget,
)


class premade_species_card(ui.column):
    def __init__(self, species_name: str, genotype: Genotype) -> None:
        super().__init__()
        self.genotype = genotype
        with self:
            widget = species_genotype_widget(name=species_name, is_instantiated=True)
            for gene in genotype.genes:
                with widget.collection:
                    d_fab.draggable(gene=gene, on_remove=handle_remove_requested, is_draggable_active=False).tooltip('Gene')
            for phene in genotype.phenes:
                with widget.collection:
                    d_fab.draggable(gene=phene, on_remove=handle_remove_requested, is_draggable_active=False).tooltip('Phene')