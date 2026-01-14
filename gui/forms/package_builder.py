from __future__ import annotations

from collections.abc import Callable, Mapping
from re import M
from typing import Any, Optional, Union

from nicegui import ui

from game.aptitude_package import AptitudePackage
from game.aptitude_package import T as Apt_Types
from game.characteristic import Characteristic
from game.characteristic_package import CharacteristicPackage
from game.characteristic_package import T as Char_Types
from game.gene import Gene
from game.knowledge import Knowledge
from game.mappings.characteristics import (
    _NORM_GENE_NAME_TO_CODES,
    _NORM_PHENE_NAME_TO_CODES,
    codes_to_name,
)
from game.mappings.skills import (
    _NORM_KNOWLEDGE_NAME_TO_CODES,
    _NORM_SKILL_NAME_TO_CODES,
    Table,
    code_to_string,
)
from game.phene import Phene
from game.skill import Skill

ItemType = Union[type[Skill], type[Knowledge], type[Gene], type[Phene]]
AttributeValue = Union[int, tuple[int, int]]
BuiltPackage = Union[
    AptitudePackage[Skill],
    AptitudePackage[Knowledge],
    CharacteristicPackage[Gene],
    CharacteristicPackage[Phene],
]
ReturnedMapping = Mapping[Any, Any]
MAPPING_PATTERN = r'_NORM_{{ItemType.upper}}_NAME_TO_CODES'


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


def _parse_characteristic_key(key: str) -> Optional[tuple[int, int]]:
    try:
        pos_str, sub_str = key.split(":", 1)
        return (int(pos_str), int(sub_str))
    except Exception:
        return None

def _call_mapper_and_validation(item_type: ItemType) -> ReturnedMapping:
    mapping_call = globals().get(MAPPING_PATTERN.replace('{{ItemType.upper}}', item_type.__name__.upper()))
    if mapping_call is None:
        raise ValueError(f"No mapping found for item type: {item_type.__name__}")
    return mapping_call

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
        on_change: Optional[Callable[[Optional[AttributeValue]], None]] = None,
    ) -> None:
        self._item_type: Optional[ItemType] = item_type
        self._characteristic_by_key: dict[str, tuple[int, int]] = {}

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

        value: Optional[AttributeValue] = None
        if isinstance(selected, int):
            value = selected
        elif isinstance(selected, str):
            parsed = _parse_characteristic_key(selected)
            if parsed is not None:
                value = parsed

        if self._external_on_change is not None:
            self._external_on_change(value)

    def set_item_type(self, item_type: Optional[ItemType]) -> None:
        self._item_type = item_type
        self._characteristic_by_key = {}
        label = self._label_for_item_type(item_type)
        self.props(f'label="{label}"')
        # NiceGUI supports updating `options` after creation.
        self.options = self._compile_attribute_options(item_type)
        self.set_value(None)

    @staticmethod
    def _label_for_item_type(item_type: Optional[ItemType]) -> str:
        if item_type is None:
            return "Select Attribute"
        return f"Select {item_type.__name__}"

    def _compile_attribute_options(
        self, item_type: Optional[ItemType]
    ) -> Union[dict[int, str], dict[str, str]]:
        if item_type is None:
            return {}
        
        mapping_call = _call_mapper_and_validation(item_type)
        
        if item_type is Skill or item_type is Knowledge:
            return {
                code: name_norm.title() for name_norm, code in mapping_call.items()
            }
        
        # else Gene/Phene select a characteristic target.
        options: dict[str, str] = {}
        for _, codes in mapping_call.items():
            pos, sub = codes
            key = f"{pos}:{sub}"
            self._characteristic_by_key[key] = (pos, sub)
            options[key] = codes_to_name(pos, sub)
            
        return options


class PackageBuilder(ui.card):
    def __init__(
        self,
        on_package_built: Callable[[BuiltPackage], None],
    ) -> None:
        super().__init__()
        self.on_package_built = on_package_built

        self._selected_item_type: Optional[ItemType] = None
        self._selected_attribute: Optional[AttributeValue] = None

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
                validation={"Cannot be 0": lambda v: v != 0},
            )
            self._context_input = ui.input(
                label="Context (optional)",
                placeholder="E.g. Event name or source",
            )

            with ui.row(wrap=False, align_items="end") as action_button_row:  # noqa: F841
                ui.button("Save", on_click=self._on_save_clicked, color="dark").classes("q-mr-sm")

    def _on_item_type_changed(self, item_type: Optional[ItemType]) -> None:
        self._selected_item_type = item_type
        self._selected_attribute = None

        if self._attribute_selector is not None:
            self._attribute_selector.set_item_type(item_type)
        self._render_attribute_display()

    def _on_attribute_changed(self, attribute: Optional[AttributeValue]) -> None:
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
            if item_type is Skill and isinstance(attribute, int):
                ui.label(f"Skill: {code_to_string(attribute, Table.BASE, capitalise=True)}")
            elif item_type is Knowledge and isinstance(attribute, int):
                ui.label(
                    f"Knowledge: {code_to_string(attribute, Table.KNOWLEDGES, capitalise=True)}"
                )
            elif item_type in (Gene, Phene) and isinstance(attribute, tuple):
                pos, sub = attribute
                ui.label(f"Characteristic: {codes_to_name(pos, sub)}")
            else:
                ui.label("Invalid selection").classes("text-negative")

    def _on_save_clicked(self) -> None:
        if self._selected_item_type is None:
            ui.notify("Pick an attribute type first")
            return
        if self._selected_attribute is None:
            ui.notify("Pick an attribute first")
            return

        level = int(self._level_input.value or 0) if self._level_input is not None else 0
        if level == 0:
            ui.notify("Level modifier cannot be 0")
            return

        context = (self._context_input.value or "") if self._context_input is not None else ""
        context = context.strip() or None

        try:
            package = self._build_package(
                item_type=self._selected_item_type,
                attribute=self._selected_attribute,
                level=level,
                context=context,
            )
        except Exception as exc:  # NiceGUI callback boundary
            ui.notify(f"Failed to build package: {exc}")
            return

        self.on_package_built(package)
        ui.notify("Package built")

    @staticmethod
    def _build_package(
        *,
        item_type: ItemType,
        attribute: AttributeValue,
        level: int,
        context: Optional[str],
    ) -> BuiltPackage:
        if item_type is Skill:
            if not isinstance(attribute, int):
                raise TypeError("Skill attribute must be an int code")
            item = Skill.of(attribute)
            return AptitudePackage(item=item, level=level, context=context)

        if item_type is Knowledge:
            if not isinstance(attribute, int):
                raise TypeError("Knowledge attribute must be an int code")
            item = Knowledge.of(attribute)
            return AptitudePackage(item=item, level=level, context=context)

        if not isinstance(attribute, tuple):
            raise TypeError("Gene/Phene attribute must be a (pos, sub) tuple")
        pos, sub = attribute
        characteristic = Characteristic.of(pos, sub)

        if item_type is Gene:
            item = Gene(characteristic=characteristic)
            return CharacteristicPackage(item=item, level=level, context=context)

        if item_type is Phene:
            item = Phene(characteristic=characteristic)
            return CharacteristicPackage(item=item, level=level, context=context)

        raise TypeError(f"Unsupported item type: {item_type}")

    @staticmethod
    def _get_item_types_from_constraints() -> list[ItemType]:
        item_types: list[ItemType] = []
        for t in Apt_Types.__constraints__:
            if isinstance(t, type):
                item_types.append(t)  # type: ignore[arg-type]
        for t in Char_Types.__constraints__:
            if isinstance(t, type):
                item_types.append(t)  # type: ignore[arg-type]
        return item_types
