from __future__ import annotations

from typing import Callable

from nicegui import ui

import gui.draggable.fab as d_fab
from game.gene import Gene
from game.genotype import Genotype
from game.mappings.characteristics import (
    _CATEGORY_MAP,
)
from game.phene import Phene
from gui.draggable.drop_container import (
    categorised_drop_column,
    handle_remove_requested,
    species_genotype_widget,
)
from gui.forms.gene import gene_form
from gui.forms.phene import phene_form
from gui.initialisation.pickables import (
    CHARACTERISTICS,
    build_initial_categorised_gene_and_phene_list_section,
    item_type_for_characteristic_name,
)
from gui.initialisation.species import premade_species_card

# https://quasar.dev/layout/grid/flex-playground

def _make_category_acceptor(category_columns: dict[int, ui.element]) -> Callable[[Gene | Phene], None]:
    def accept(item: Gene | Phene) -> None:
        from game.mappings.characteristics import char_name_to_category_code

        try:
            # Gene/Phene both expose `.characteristic.get_name()`.
            cat_code = char_name_to_category_code(item.characteristic.get_name())
        except Exception:
            cat_code = 0

        target = category_columns.get(cat_code)
        if target is None:
            ui.notify('No category target for this item')
            return
        with target:
            d_fab.draggable(gene=item, on_remove=handle_remove_requested).tooltip(type(item).__name__)

    return accept


# This is an initial load of the default Genes and Phenes available to pick from.
# There will be separate logic to order the pickable items when the items are dragged and dropped
# Which will ensure that the items remain in the correct category according to the Characteristic of the
# Gene or Phene instance.
# ============================== Widget to Pick from a Default List of Genes and Phenes ==============================
def _pickable_gene_list_section():
    item_type_by_category, characteristic_names_by_category = build_initial_categorised_gene_and_phene_list_section()

    category_columns: dict[int, ui.element] = {}
    with categorised_drop_column('Standard Characteristics', category_targets=category_columns, default_target=None):
        for cat_code in sorted(_CATEGORY_MAP.keys()):
            cat_name = _CATEGORY_MAP[cat_code]
            if cat_code == 0:
                continue
            with ui.expansion(cat_name, value=True).classes('w-auto text-xs leading-none px-1 py-0 q-py-xs'):
                target: ui.element = ui.column().classes('')
                category_columns[cat_code] = target

                for characteristic_name in characteristic_names_by_category.get(cat_code, []):
                    item_type = item_type_for_characteristic_name(characteristic_name)
                    # If a mapping/table drift introduces an unknown name, avoid taking down
                    # the whole UI; just skip the invalid entry.
                    try:
                        item = item_type.by_characteristic_name(characteristic_name)
                    except ValueError:
                        continue
                    with target:
                        # Need classes to make the buttons as thin as possible
                        d_fab.draggable(gene=item, on_remove=handle_remove_requested) \
                            .tooltip(type(item).__name__)


# ============================== Widget to Define a Species Genotype ==============================    
def _species_genotype_widget(category_columns: dict[int, ui.element]) -> None:
    with species_genotype_widget(
        name = '',
        placeholder= 'Homo Sapiens',
        on_drop=lambda item, loc: ui.notify(f'Dropped: {item.characteristic.get_name()}'),
    ):
        # `genotype_drop_column` is a self-contained widget:
        # - Name input
        # - Collation layer placeholder
        # - Collection area where dropped items appear
        pass


# ============================== Widgets to Create Genes and Phenes ==============================
def _input_form_section(*, on_add_item: Callable[[Gene | Phene], None]) -> None:
    gene_form(options=CHARACTERISTICS, on_add=on_add_item)
    phene_form(options=CHARACTERISTICS, on_add=on_add_item)

def _create_standard_genotype() -> Genotype:
    
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

def species_tab(tab):
    with ui.tab_panel(tab):
        genotype_category_columns: dict[int, ui.element] = {}
        acceptor = _make_category_acceptor(genotype_category_columns)

        with ui.row().classes(''):
            with ui.column(wrap=False).classes('w-46 q-mr-md'):
                _input_form_section(on_add_item=acceptor)
            with ui.column(wrap=False).classes('w-32 q-mr-xl'):
                _pickable_gene_list_section()
            with ui.column(wrap=False).classes('q-ml-xl'):
                _species_genotype_widget(genotype_category_columns)
                ui.label('Premade Species').classes('text-lg font-bold q-mt-md')
                premade_species_card('Homo Sapiens', _create_standard_genotype())