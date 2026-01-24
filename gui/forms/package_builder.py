from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Optional, Union

from nicegui import ui

from game.characteristic import Characteristic
from game.gene import Gene
from game.knowledge import Knowledge
from game.mappings.data import (
    AliasMap,
    AliasMappedFullCode,
    FullCode,
)
from game.mappings.set import ATTRIBUTES
from game.package import AttributePackage, T
from game.phene import Phene
from game.skill import Skill

ItemType = Union[type[Skill], type[Knowledge], type[Gene], type[Phene], type[Characteristic]]

BuiltPackage = Union[
    AttributePackage[Skill],
    AttributePackage[Knowledge],
    AttributePackage[Gene],
    AttributePackage[Phene],
    AttributePackage[Characteristic],
]


def _full_code_key(code: FullCode) -> str:
    a, b, c = code
    return f"{a}.{b}.{c}"


def _canonical_from_alias_map(alias_map: AliasMap) -> str:
    return next(iter(alias_map.keys()), "")


def _call_mapper_and_validation(item_type: ItemType) -> Iterable[AliasMappedFullCode]:
    if item_type is Skill:
        return ATTRIBUTES.skills.get_all()
    if item_type is Knowledge:
        return ATTRIBUTES.knowledges.get_all()
    if item_type in (Gene, Phene, Characteristic):
        return ATTRIBUTES.characteristics.get_all()
    raise TypeError(f"Unsupported item type: {item_type}")


def _event_value(e: object) -> Optional[object]:
    """Extract `value` from NiceGUI's event payload in a permissive way."""
    selected = getattr(e, "value", None)
    if selected is not None:
        return selected

    args = getattr(e, "args", None)
    if isinstance(args, dict):
        return args.get("value")
    if isinstance(args, (list, tuple)) and args:
        return args[-1]
    return None


def _type_key(t: type) -> str:
    # Stable, collision-resistant key that is JSON-safe for the client.
    return f"{t.__module__}.{t.__qualname__}"


class TypeSelector(ui.select):
    def __init__(
        self,
        options: Optional[list[ItemType]] = None,
        label: str = "Select Attribute Type",
        value: Optional[ItemType] = None,
        on_change: Optional[Callable[[Optional[ItemType]], None]] = None,
        **kwargs,
    ) -> None:

        options_list = options if options is not None else []
        self._type_by_key: dict[str, ItemType] = {_type_key(t): t for t in options_list}
        # `ui.select` values must be JSON-serializable, so we send keys.
        str_options: dict[str, str] = {k: self._type_by_key[k].__name__ for k in self._type_by_key}

        super().__init__(
            label=label,
            options=str_options,
            value=_type_key(value) if value is not None else None,
            **kwargs,
            with_input=True,
            on_change=self._handle_selection_change,
        )
        self._external_on_change = on_change

    def _handle_selection_change(self, e) -> None:
        selected_key = _event_value(e)
        selected_type: ItemType | None = None
        if isinstance(selected_key, str):
            selected_type = self._type_by_key.get(selected_key)

        if self._external_on_change is not None:
            self._external_on_change(selected_type)


class CharacterAttributeSelector(ui.select):
    def __init__(
        self,
        item_type: Optional[ItemType] = None,
        on_change: Optional[Callable[[Optional[AliasMappedFullCode]], None]] = None,
    ) -> None:
        self._item_type: Optional[ItemType] = item_type
        self._attribute_by_key: dict[str, AliasMappedFullCode] = {}

        super().__init__(
            label=self._label_for_item_type(item_type),
            options=self._compile_attribute_options(item_type),
            with_input=True,
            on_change=self._handle_selection_change,
        )
        self.props("clearable")
        self._external_on_change = on_change

    def _handle_selection_change(self, e) -> None:
        selected = _event_value(e)
        attribute: AliasMappedFullCode | None = None
        if isinstance(selected, str):
            attribute = self._attribute_by_key.get(selected)
        if self._external_on_change is not None:
            self._external_on_change(attribute)

    def set_item_type(self, item_type: Optional[ItemType]) -> None:
        self._item_type = item_type
        self._attribute_by_key = {}
        label = self._label_for_item_type(item_type)
        self.props(f'label="{label}"')
        # When changing the option set, clear the selection first.
        self.set_value(None)
        # NiceGUI supports updating `options` after creation, but the client
        # won't refresh reliably unless we trigger an update.
        self.options = self._compile_attribute_options(item_type)
        self.update()

    @staticmethod
    def _label_for_item_type(item_type: Optional[ItemType]) -> str:
        if item_type is None:
            return "Select Attribute"
        return f"Select {item_type.__name__}"

    def _compile_attribute_options(self, item_type: Optional[ItemType]) -> dict[str, str]:
        options: dict[str, str] = {}
        if item_type is None:
            return {}

        mapping_call = _call_mapper_and_validation(item_type)
        for alias_map, full_code in mapping_call:
            key = _full_code_key(full_code)
            canonical = _canonical_from_alias_map(alias_map)
            label = canonical if canonical else str(full_code)
            options[key] = label
            self._attribute_by_key[key] = (alias_map, full_code)

        return options


class PackageBuilder(ui.card):
    def __init__(
        self,
        on_package_built: Callable[[BuiltPackage], None],
    ) -> None:
        super().__init__()
        self.on_package_built = on_package_built

        self._selected_item_type: Optional[ItemType] = None
        self._selected_attribute: Optional[AliasMappedFullCode] = None

        self._type_options: list[ItemType] = self._get_item_types_from_constraints()

        self._attribute_selector: Optional[CharacterAttributeSelector] = None
        self._attribute_display_row: Optional[ui.row] = None
        self._level_input: Optional[ui.number] = None
        self._context_input: Optional[ui.input] = None

        self._build_form()

    def _build_form(self) -> None:
        with self:
            with ui.row() as _attribute_type_selection_row:
                TypeSelector(
                    options=self._type_options,
                    on_change=self._on_item_type_changed,
                )

            with ui.row() as _attribute_selection_row:
                self._attribute_selector = CharacterAttributeSelector(
                    item_type=None,
                    on_change=self._on_attribute_changed,
                )

            with ui.row() as attribute_display_row:
                self._attribute_display_row = attribute_display_row
                ui.label("No Attribute Selected").classes("text-gray-500 italic")

            self._level_input = ui.number(
                label="Level Modifier",
                value=None,
            )
            self._context_input = ui.input(
                label="Context (optional)",
                placeholder="E.g. Event name or source",
            )

            with ui.row(wrap=False, align_items="end") as action_button_row:  # noqa: F841
                ui.button("Save", color="dark").classes("q-mr-sm")

    def _on_item_type_changed(self, item_type: Optional[ItemType]) -> None:
        self._selected_item_type = item_type
        self._selected_attribute = None

        if self._attribute_selector is not None:
            self._attribute_selector.set_item_type(item_type)
        self._render_attribute_display()

    def _on_attribute_changed(self, attribute: Optional[AliasMappedFullCode]) -> None:
        self._selected_attribute = attribute
        self._render_attribute_display()

    def _render_attribute_display(self) -> None:
        if self._attribute_display_row is None:
            return

        self._attribute_display_row.clear()
        if self._selected_item_type is None or self._selected_attribute is None:
            with self._attribute_display_row:
                ui.label("No Attribute Selected").classes("text-gray-500 italic")
            return

        item_type = self._selected_item_type
        attribute = self._selected_attribute

        with self._attribute_display_row:
            alias_map, full_code = attribute
            canonical = _canonical_from_alias_map(alias_map)
            display_name = canonical if canonical else str(full_code)
            ui.label(f"{item_type.__name__}: {display_name} ({full_code})")

    @staticmethod
    def _get_item_types_from_constraints() -> list[ItemType]:
        item_types: list[ItemType] = []
        for t in T.__constraints__:
            if isinstance(t, type):
                item_types.append(t)  # type: ignore[arg-type]

        return item_types
