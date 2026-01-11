from __future__ import annotations

from nicegui import ui

from game.gene import Gene
from game.genotype import Genotype
from game.phene import Phene
from gui.styles import (
    UPP_CELL_LABEL,
    UPP_GENE_CELL_LABEL,
    UPP_GRID,
    UPP_INDEX_LABEL,
    UPP_PHENE_CELL_LABEL,
    UPP_ROOT,
)
from sophont.character import Sophont


def characteristics_collation_layer(genotype: Genotype | None = None, display_indices: bool = True) -> ui.element:
    from warnings import warn
    warn("characteristics_collation_layer is deprecated; use UPPDisplay instead", DeprecationWarning)

    """(DEPRECATED: Use UPPDisplay instead) Build a 3-row summary grid from a genotype phenotype mapping.

    Row 1: UPP index for each phenotype entry (sorted by upp_index)
    Row 2: Gene initial (first capitalised letter) or blank if no Gene; background 'purple-11'
    Row 3: Phene initial (first capitalised letter) or blank if no Phene; background 'blue'
    """

    def _initial_from_characteristic_name(name: str) -> str:
        name = name.strip()
        return name[:1].upper() if name else ""

    def _gene_initial(gene: Gene | None) -> str:
        if gene is None:
            return ""
        return _initial_from_characteristic_name(gene.characteristic.get_name())

    explicit_phene_upp_indexes: set[int]
    if genotype is None or genotype.phenes is None:
        explicit_phene_upp_indexes = set()
    else:
        explicit_phene_upp_indexes = {phene.characteristic.upp_index for phene in genotype.phenes}

    def _is_placeholder_phene_from_gene(
        upp_index: int, gene: Gene | None, phene: Phene | None
    ) -> bool:
        """Genotype.get_phenotype currently synthesizes a 'placeholder' phene for each gene.

        For the UPP display we treat that placeholder as "no phene" so the Phene row stays blank
        unless an explicit phene was supplied.
        """
        if upp_index in explicit_phene_upp_indexes:
            return False
        if gene is None or phene is None:
            return False
        return (
            phene.expression_value == 0
            and phene.contributor_uuid == bytes(16)
            and phene.is_grafted is False
        )

    def _phene_initial(upp_index: int, gene: Gene | None, phene: Phene | None) -> str:
        if phene is None or _is_placeholder_phene_from_gene(upp_index, gene, phene):
            return ""
        return _initial_from_characteristic_name(phene.characteristic.get_name())

    if genotype is None:
        with ui.column().classes(UPP_ROOT) as root:
            with ui.grid(columns=8).classes(UPP_GRID):
                for upp_index in range(1, 9):
                    ui.label(str(upp_index)).classes(UPP_INDEX_LABEL)
                for _ in range(1, 9):
                    ui.label("").classes(UPP_CELL_LABEL)
                for _ in range(1, 9):
                    ui.label("").classes(UPP_CELL_LABEL)
        return root

    phenotype = genotype.get_phenotype()
    upp_indexes = sorted(phenotype.keys())
    columns = max(len(upp_indexes), 1)

    with ui.column().classes(UPP_ROOT) as root:
        with ui.grid(columns=columns).classes(UPP_GRID):
            # Row 1: UPP indices
            if display_indices:
                for upp_index in upp_indexes:
                    ui.label(str(upp_index)).classes(UPP_INDEX_LABEL)

            # Row 2: Gene initial (purple-11)
            for upp_index in upp_indexes:
                gene, phene = phenotype[upp_index]
                tooltip_UPP = f"UPP: {upp_index} - "
                tooltip_name = gene.characteristic.get_name() if gene is not None else "Non-Genetic"
                ui.label(_gene_initial(gene)).classes(UPP_GENE_CELL_LABEL).tooltip(
                    tooltip_UPP + tooltip_name
                )

            # Row 3: Phene initial (blue)
            for upp_index in upp_indexes:
                gene, phene = phenotype[upp_index]
                tooltip_UPP = f"UPP: {upp_index} - "
                tooltip_name = ""
                tooltip_inheritance = ""
                if phene is not None:
                    tooltip_name = phene.characteristic.get_name()
                    if phene.contributor_uuid != bytes(16):
                        tooltip_inheritance = f" Inherited from {phene.contributor_uuid.hex()}"
                ui.label(_phene_initial(upp_index, gene, phene)).classes(UPP_PHENE_CELL_LABEL).tooltip(
                    tooltip_UPP + tooltip_name + tooltip_inheritance
                )

    return root

class UPPDisplay(ui.grid):
    def __init__(self, character: Sophont, display_indices: bool = True) -> None:
        self.genotype = character.epigenetic_profile.species_genotype.genotype
        self.genes = self.genotype.get_genes_without_phenes()
        self.phenes = self.genotype.get_phenes_without_genes()
        self.upp_indexes = sorted(
            set(self.genotype.get_genes_without_phenes().keys())
            .union(set(self.genotype.get_phenes_without_genes().keys()))
        )
        super().__init__(columns=len(self.upp_indexes) if self.upp_indexes else 1)
        self.classes(UPP_GRID)
        self.character = character
        self.display_indices = display_indices
        self._build_display()

    def _build_display(self) -> None:
        with ui.column().classes(UPP_ROOT) as root:
                with ui.grid(columns=len(self.upp_indexes) if self.upp_indexes else 1).classes(UPP_GRID):
                    # Row 1: UPP indices
                    if self.display_indices:
                        for upp_index in self.upp_indexes:
                            ui.label(str(upp_index)).classes(UPP_INDEX_LABEL)

                    # Row 2: Gene initial (purple-11)
                    for upp_index in self.upp_indexes:
                        gene = self.genes.get(upp_index)
                        tooltip_UPP = f"UPP: {upp_index} - "
                        tooltip_name = gene.characteristic.get_name() if gene is not None else "Non-Genetic"
                        ui.label(
                            gene.characteristic.get_name()[:1].upper() if gene is not None else ""
                        ).classes(UPP_GENE_CELL_LABEL).tooltip(
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
                        ).classes(UPP_PHENE_CELL_LABEL).tooltip(
                            tooltip_UPP + tooltip_name + tooltip_inheritance
                        )