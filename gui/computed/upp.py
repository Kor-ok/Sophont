from __future__ import annotations

from collections.abc import Mapping

from nicegui import ui

from game.gene import Gene
from game.phene import Phene
from gui import styles
from sophont.character import Sophont


class UPPDisplay(ui.column):
    """Display a simple UPP-style grid for a Sophont's genotype.

    Renders up to three rows:
    - Optional index row (UPP positions)
    - Gene initials
    - Phene initials (with inheritance details when present)
    """

    _NULL_UUID = bytes(16)

    def __init__(self, character: Sophont, display_indices: bool = True) -> None:
        super().__init__()
        self.classes(styles.UPP_ROOT)

        genotype = character.epigenetic_profile.species.genotype
        genes = genotype.get_genes_without_phenes()
        phenes = genotype.get_phenes_without_genes()

        upp_indices = sorted(set(genes).union(phenes))

        self._build_display(
            upp_indices=upp_indices,
            genes=genes,
            phenes=phenes,
            display_indices=display_indices,
        )

    def _build_display(
        self,
        *,
        upp_indices: list[int],
        genes: Mapping[int, Gene],
        phenes: Mapping[int, Phene],
        display_indices: bool,
    ) -> None:
        gene_die_mult_sum, phene_expression_precidence_sum = self._sum_gene_phene_values(genes, phenes)
        columns = gene_die_mult_sum + phene_expression_precidence_sum
        with self:
            with ui.grid(columns=columns).classes(styles.UPP_GRID):
                if display_indices:
                    for upp_index in upp_indices:
                        ui.label(str(upp_index)).classes(styles.UPP_INDEX_LABEL + self._grid_column_span_class_constructor(
                            genes.get(upp_index).die_mult
                            if genes.get(upp_index) is not None
                             else phenes.get(upp_index).expression_precidence
                        ))

                for upp_index in upp_indices:
                    gene = genes.get(upp_index)
                    ui.label(self._initial_for_trait(gene)).classes(
                        styles.UPP_GENE_CELL_LABEL + self._grid_column_span_class_constructor(
                            genes.get(upp_index).die_mult
                            if genes.get(upp_index) is not None
                             else phenes.get(upp_index).expression_precidence
                        )
                    ).tooltip(self._tooltip_for_gene(upp_index, gene))

                for upp_index in upp_indices:
                    phene = phenes.get(upp_index)
                    ui.label(self._initial_for_trait(phene)).classes(
                        styles.UPP_PHENE_CELL_LABEL + self._grid_column_span_class_constructor(
                            genes.get(upp_index).die_mult
                            if genes.get(upp_index) is not None
                             else phenes.get(upp_index).expression_precidence
                        )
                    ).tooltip(self._tooltip_for_phene(upp_index, phene))

    @staticmethod
    def _initial_for_trait(trait: Gene | Phene | None) -> str:
        if trait is None:
            return ""
        name = trait.characteristic.get_name()
        return name[:1].upper() if name else ""
    
    @staticmethod
    def _sum_gene_phene_values(genes: Mapping[int, Gene], phenes: Mapping[int, Phene]) -> tuple[int, int]:
        gene_die_mult_sum = sum(
            gene.die_mult
            for gene in genes.values()
            if gene.characteristic is not None
        )
        phene_expression_precidence_sum = sum(
            phene.expression_precidence
            for phene in phenes.values()
            if phene.characteristic is not None
        )
        return gene_die_mult_sum, phene_expression_precidence_sum
    def _grid_column_span_class_constructor(self, span: int) -> str:
        return f" col-span-{span}"

    def _tooltip_for_gene(self, upp_index: int, gene: Gene | None) -> str:
        if gene is None:
            name = "Non-Genetic"
        else:
            name = gene.characteristic.get_name()
        return f"UPP: {upp_index} - {name}"

    def _tooltip_for_phene(self, upp_index: int, phene: Phene | None) -> str:
        if phene is None:
            return f"UPP: {upp_index}"

        name = phene.characteristic.get_name()
        inherited = (
            f" Inherited from {phene.contributor_uuid.hex()}"
            if phene.contributor_uuid != self._NULL_UUID
            else ""
        )
        return f"UPP: {upp_index} - {name}{inherited}"
