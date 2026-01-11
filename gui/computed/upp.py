from __future__ import annotations

from nicegui import ui

from gui import styles
from sophont.character import Sophont


class UPPDisplay(ui.grid):
    """Displays the a grid of Genes/Phenes of a Sophont character.

    """
    def __init__(self, character: Sophont, display_indices: bool = True) -> None:
        self.genotype = character.epigenetic_profile.species_genotype.genotype
        self.genes = self.genotype.get_genes_without_phenes()
        self.phenes = self.genotype.get_phenes_without_genes()
        self.upp_indexes = sorted(
            set(self.genotype.get_genes_without_phenes().keys())
            .union(set(self.genotype.get_phenes_without_genes().keys()))
        )
        super().__init__(columns=len(self.upp_indexes) if self.upp_indexes else 1)
        self.classes(styles.UPP_GRID)
        self.character = character
        self.display_indices = display_indices
        self._build_display()

    def _build_display(self) -> None:
        with ui.column().classes(styles.UPP_ROOT):
                with ui.grid(columns=len(self.upp_indexes) if self.upp_indexes else 1).classes(styles.UPP_GRID):
                    # Row 1: UPP indices
                    if self.display_indices:
                        for upp_index in self.upp_indexes:
                            ui.label(str(upp_index)).classes(styles.UPP_INDEX_LABEL)

                    # Row 2: Gene initial (purple-11)
                    for upp_index in self.upp_indexes:
                        gene = self.genes.get(upp_index)
                        tooltip_UPP = f"UPP: {upp_index} - "
                        tooltip_name = gene.characteristic.get_name() if gene is not None else "Non-Genetic"
                        ui.label(
                            gene.characteristic.get_name()[:1].upper() if gene is not None else ""
                        ).classes(styles.UPP_GENE_CELL_LABEL).tooltip(
                            tooltip_UPP + tooltip_name
                        )

                    # Row 3: Phene initial (blue)
                    for upp_index in self.upp_indexes:
                        phene = self.phenes.get(upp_index)
                        tooltip_UPP = f"UPP: {upp_index} - "
                        tooltip_name = ""
                        tooltip_inheritance = ""
                        if phene is not None:
                            tooltip_name = phene.characteristic.get_name()
                            if phene.contributor_uuid != bytes(16):
                                tooltip_inheritance = f" Inherited from {phene.contributor_uuid.hex()}"
                        ui.label(
                            phene.characteristic.get_name()[:1].upper() if phene is not None else ""
                        ).classes(styles.UPP_PHENE_CELL_LABEL).tooltip(
                            tooltip_UPP + tooltip_name + tooltip_inheritance
                        )