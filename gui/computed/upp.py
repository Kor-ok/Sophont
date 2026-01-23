from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from nicegui import ui

from game.gene import Gene
from game.phene import Phene
from gui import styles
from sophont.character import Sophont


class UPPDisplay(ui.column):
    """Display a UPP-style grid for a Sophont's genotype.

    Renders up to three rows where columns are sized
    according to gene die multiplier value:
    - Optional index row (UPP positions)
    - Gene initials
    - Phene initials (with inheritance details when present)
    """

    _NULL_UUID: int = -1

    def __init__(self, character: Sophont, display_indices: bool = True) -> None:
        super().__init__()
        self.classes(styles.UPP_ROOT)

        genotype = character.epigenetics.species.genotype
        genes = {gene.characteristic.upp_index: gene for gene in genotype.genes}
        phenes = self._phenes_by_upp_index(genotype)

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
        phenes: Mapping[int, Sequence[Phene]],
        display_indices: bool,
    ) -> None:
        columns = sum(self._span_for_upp_index(upp_index, genes) for upp_index in upp_indices)
        with self:
            with ui.grid(columns=columns).classes(styles.UPP_GRID):
                if display_indices:
                    for upp_index in upp_indices:
                        ui.label(str(upp_index)).classes(
                            styles.UPP_INDEX_LABEL
                            + self._grid_column_span_class_constructor(
                                self._span_for_upp_index(upp_index, genes)
                            )
                        )

                for upp_index in upp_indices:
                    gene = genes.get(upp_index)
                    ui.label(self._initial_for_trait(gene)).classes(
                        styles.UPP_GENE_CELL_LABEL
                        + self._grid_column_span_class_constructor(
                            self._span_for_upp_index(upp_index, genes)
                        )
                    ).tooltip(self._tooltip_for_gene(upp_index, gene))

                for upp_index in upp_indices:
                    upp_phenes = list(phenes.get(upp_index, ()))
                    ui.label(self._initials_for_traits(upp_phenes)).classes(
                        styles.UPP_PHENE_CELL_LABEL
                        + self._grid_column_span_class_constructor(
                            self._span_for_upp_index(upp_index, genes)
                        )
                    ).tooltip(self._tooltip_for_phenes(upp_index, upp_phenes))

    @staticmethod
    def _initial_for_trait(trait: Gene | Phene | None) -> str:
        if trait is None:
            return ""
        name, _ = trait.characteristic.get_name()
        return name.upper() if name else ""

    @classmethod
    def _initials_for_traits(cls, traits: Sequence[Gene | Phene]) -> str:
        initials = [cls._initial_for_trait(trait) for trait in traits]
        initials = [initial for initial in initials if initial]
        return " / ".join(initials)

    @staticmethod
    def _span_for_upp_index(
        upp_index: int,
        genes: Mapping[int, Gene],
    ) -> int:
        gene = genes.get(upp_index)
        if gene is not None:
            return gene.die_mult
        return 1

    def _grid_column_span_class_constructor(self, span: int) -> str:
        return f" col-span-{span}"

    def _tooltip_for_gene(self, upp_index: int, gene: Gene | None) -> str:
        if gene is None:
            name = "Non-Genetic"
        else:
            name, _ = gene.characteristic.get_name()
        return f"UPP: {upp_index} - {name}"

    def _tooltip_for_phene(self, upp_index: int, phene: Phene | None) -> str:
        if phene is None:
            return f"UPP: {upp_index}"

        name, _ = phene.characteristic.get_name()
        inherited = (
            f" Inherited from {phene.contributor_uuid}"
            if phene.contributor_uuid != self._NULL_UUID
            else ""
        )
        return f"UPP: {upp_index} - {name}{inherited}"

    def _tooltip_for_phenes(self, upp_index: int, phenes: Sequence[Phene]) -> str:
        if not phenes:
            return f"UPP: {upp_index}"

        parts = [self._tooltip_for_phene(upp_index, phene) for phene in phenes]
        return "\n".join(parts)

    @staticmethod
    def _phenes_by_upp_index(genotype) -> dict[int, list[Phene]]:
        phenes_by_index: dict[int, list[Phene]] = defaultdict(list)
        if genotype.phenes is None:
            return {}

        for phene in genotype.phenes:
            upp_index = phene.characteristic.upp_index
            phenes_by_index[upp_index].append(phene)

        return dict(phenes_by_index)
