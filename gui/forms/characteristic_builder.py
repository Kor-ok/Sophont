from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Optional

from nicegui import ui

from game.characteristic import Characteristic
from game.mappings.set import ATTRIBUTES

CanonicalStrKey = str
StringAliases = tuple[str, ...]
AliasMap = Mapping[CanonicalStrKey, StringAliases]

PrimaryCodeInt = int
SecondaryCodeInt = int
TertiaryCodeInt = int
FullCode = tuple[PrimaryCodeInt, SecondaryCodeInt, TertiaryCodeInt]

AliasMappedFullCode = tuple[AliasMap, FullCode]

class CharacteristicBuilder(ui.card):
    """Form to build a Characteristic selection."""

    def __init__(
        self,
        *,
        on_characteristic_built: Optional[Callable[[Characteristic], None]] = None,
    ) -> None:
        super().__init__()
        self.classes("q-pa-md").props("flat outlined")

        collection = ATTRIBUTES.characteristics.get_all()
        upp_options = list(sorted(set(
            code[0]
            for alias_map, code in collection
        )))

        sub_options = list(sorted(set(
            code[1]
            for alias_map, code in collection
        )))

        master_category_options = list(sorted(set(
            code[2]
            for alias_map, code in collection
        )))

        self._upp_index_select = ui.select(
            label="UPP Index",
            options=upp_options,
            value=None,
        ).classes("w-full")

        self._subtype_select = ui.select(
            label="Subtype",
            options=sub_options,
            value=None,
        ).classes("w-full q-mt-md")

        self._master_category_select = ui.select(
            label="Master Category",
            options=master_category_options,
            value=None,
        ).classes("w-full q-mt-md")

        ui.button("Build Characteristic").classes("q-mt-md")