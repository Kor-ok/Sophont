from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from nicegui import ui

from game.aptitude_package import T
from game.mappings.skills import (
    _NORM_KNOWLEDGE_NAME_TO_CODES,
    _NORM_SKILL_NAME_TO_CODES,
    Table,
    code_to_string,
)
from game.skill import Skill
from gui.initialisation.globals import IS_DEBUG

# https://quasar.dev/layout/grid/flex-playground

def get_type_constraints_for_options_select() -> list[str]:
    list_of_types_str = []
    for t in [t.__name__ for t in T.__constraints__]:
        list_of_types_str.append(t)
    return list_of_types_str

current_aptitude_type: str | None = None
current_skill_code: int | None = None
current_knowledge_code: int | None = None

def render_selector_for_aptitude_type(aptitude_type: str | None) -> None:
    global current_aptitude_type
    aptitude_selection_row.clear()
    if aptitude_type is None:
        current_aptitude_type = None
        with aptitude_selection_row:
            ui.label("No Aptitude Type Selected").classes("text-gray-500 italic")
        return

    current_aptitude_type = aptitude_type
    with aptitude_selection_row:
        if aptitude_type.lower() == "skill":
            aptitude_display_row.clear()
            SkillSelector(
                label="Select Skill",
                on_change=set_active_skill,
            )
        elif aptitude_type.lower() == "knowledge":
            aptitude_display_row.clear()
            KnowledgeSelector(
                label="Select Knowledge",
                on_change=set_active_knowledge,
            )

def set_active_aptitude_type(aptitude_type: str | None) -> None:
    render_selector_for_aptitude_type(aptitude_type)

def render_for_skill(skill_code: int | None) -> None:
    global current_skill_code
    aptitude_display_row.clear()
    if skill_code is None:
        current_skill_code = None
        with aptitude_display_row:
            ui.label("No Skill Selected").classes("text-gray-500 italic")
        return

    current_skill_code = skill_code
    with aptitude_display_row:
        SkillDisplay(skill_code=skill_code)

def render_for_knowledge(knowledge_code: int | None) -> None:
    global current_knowledge_code
    aptitude_display_row.clear()
    if knowledge_code is None:
        current_knowledge_code = None
        with aptitude_display_row:
            ui.label("No Knowledge Selected").classes("text-gray-500 italic")
        return

    current_knowledge_code = knowledge_code
    with aptitude_display_row:
        KnowledgeDisplay(knowledge_code=knowledge_code)

def set_active_skill(skill_code: int | None) -> None:
    render_for_skill(skill_code)

def set_active_knowledge(knowledge_code: int | None) -> None:
    render_for_knowledge(knowledge_code)

class AptitudeTypeSelector(ui.select):
    def __init__(
            self,
            options: list[str] | None = None,
            label: str = "Select Aptitude Type",
            value: str | None = None,
            on_change: Callable[[str | None], None] | None = None,
            ) -> None:
        
        super().__init__(
            label=label, 
            options=options if options is not None else get_type_constraints_for_options_select(), 
            with_input=True,
            on_change=self._handle_selection_change,
            )
        self._external_on_change = on_change
        
    def _handle_selection_change(self, e) -> None:
        selected_type: str | None = getattr(e, "value", None)
        if selected_type is None:
            args = getattr(e, "args", None)
            if isinstance(args, dict):
                selected_type = args.get("value")
            elif isinstance(args, (list, tuple)) and args:
                # Be permissive: some event shapes pass payloads as a list/tuple.
                selected_type = args[-1]

        selected_aptitude_type = (
            selected_type if selected_type is not None else None
        )
        if self._external_on_change is not None:
            self._external_on_change(selected_aptitude_type)

class SkillDisplay(ui.card):
    def __init__(self, skill_code: int | None = None) -> None:
        super().__init__()
        self.classes("")
        if skill_code is None:
            self._build_empty()
            return
        skill = Skill.of(skill_code)
        code = skill.code
        master_category_code = skill.master_category
        sub_category_code = skill.sub_category
        uuid = skill.unique_id

        self._build_display(
            code=code,
            master_category_code=master_category_code,
            sub_category_code=sub_category_code,
            uuid=uuid,
        )
    def _build_empty(self) -> None:
        with self:
            ui.label("No Skill Selected").classes("text-gray-500 italic")
    def _build_display(
        self,
        *,
        code: int,
        master_category_code: int,
        sub_category_code: int,
        uuid: bytes,
    ) -> None:
        with self:
            if IS_DEBUG:
                ui.label(f"Skill Code: {code}")
            ui.label(f"Category: {code_to_string(master_category_code, Table.MASTER_CATEGORY)}")
            ui.label(f"Sub Category: {code_to_string(sub_category_code, Table.SUB_CATEGORY)}")
            if IS_DEBUG:
                ui.label(f"UUID: {uuid.hex()}")

class SkillSelector(ui.select):
    def __init__(
            self,
            options: dict[int, str] | None = None,
            label: str = "Select Skill",
            value: int | None = None,
            on_change: Callable[[int | None], None] | None = None,
            ) -> None:
        
        super().__init__(
            label=label, 
            options=self._compile_skill_name_options(), 
            with_input=True,
            on_change=self._handle_selection_change,
            )
        self._external_on_change = on_change
        
    def _handle_selection_change(self, e) -> None:
        selected_skill_code: int | None = getattr(e, "value", None)
        if selected_skill_code is None:
            args = getattr(e, "args", None)
            if isinstance(args, dict):
                selected_skill_code = args.get("value")
            elif isinstance(args, (list, tuple)) and args:
                # Be permissive: some event shapes pass payloads as a list/tuple.
                selected_skill_code = args[-1]

        selected_skill = (
            selected_skill_code if selected_skill_code is not None else None
        )
        if self._external_on_change is not None:
            self._external_on_change(selected_skill)

    @staticmethod
    def _compile_skill_name_options() -> dict[int, str]:
        skill_name_options: dict[int, str] = {}
        for name_norm, code in _NORM_SKILL_NAME_TO_CODES.items():
            skill_name_options[code] = name_norm.title()
        return skill_name_options

class KnowledgeDisplay(ui.card):
    def __init__(self, knowledge_code: int | None = None) -> None:
        super().__init__()
        self.classes("")
        if knowledge_code is None:
            self._build_empty()
            return
        # knowledge_instance = Knowledge.of(knowledge_code)
        code = knowledge_code
        focus = ""
        associated_skill = -99
        uuid = uuid4().bytes

        self._build_display(
            code=code,
            focus=focus,
            associated_skill=associated_skill,
            uuid=uuid,
        )
    def _build_empty(self) -> None:
        with self:
            ui.label("No Knowledge Selected").classes("text-gray-500 italic")
    def _build_display(
        self,
        *,
        code: int,
        focus: str,
        associated_skill: int,
        uuid: bytes,
    ) -> None:
        with self:
            if IS_DEBUG:
                ui.label(f"Knowledge Code: {code}")
            ui.input("Focus:", placeholder="e.g. 'Anglic', 'Trokh', 'Archeological Actuary', etc.")
            associated_skill_selector = SkillSelector(label="Select Skill to Associate")
            if IS_DEBUG:
                ui.label(f"UUID: {uuid.hex()}")

class KnowledgeSelector(ui.select):
    def __init__(
            self,
            options: dict[int, str] | None = None,
            label: str = "Select Knowledge",
            value: int | None = None,
            on_change: Callable[[int | None], None] | None = None,
            ) -> None:
        
        super().__init__(
            label=label, 
            options=self._compile_knowledge_name_options(), 
            with_input=True,
            on_change=self._handle_selection_change,
            )
        self._external_on_change = on_change
        
    def _handle_selection_change(self, e) -> None:
        selected_knowledge_code: int | None = getattr(e, "value", None)
        if selected_knowledge_code is None:
            args = getattr(e, "args", None)
            if isinstance(args, dict):
                selected_knowledge_code = args.get("value")
            elif isinstance(args, (list, tuple)) and args:
                # Be permissive: some event shapes pass payloads as a list/tuple.
                selected_knowledge_code = args[-1]

        selected_knowledge = (
            selected_knowledge_code if selected_knowledge_code is not None else None
        )
        if self._external_on_change is not None:
            self._external_on_change(selected_knowledge)

    @staticmethod
    def _compile_knowledge_name_options() -> dict[int, str]:
        knowledge_name_options: dict[int, str] = {}
        for name_norm, code in _NORM_KNOWLEDGE_NAME_TO_CODES.items():
            knowledge_name_options[code] = name_norm.title()
        return knowledge_name_options

with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Package Builder Development").classes("text-sm font-thin q-ma-none")

with ui.column().classes("w-128 q-pa-md items-center justify-center") as package_builder_container:
    with ui.card():
        with ui.row() as aptitude_type_selection_row:
            aptitude_type_selector = AptitudeTypeSelector(
                label="Aptitude Type",
                on_change=set_active_aptitude_type,
            )
        with ui.row() as aptitude_selection_row:
            if current_aptitude_type is not None:
                
                skill_selector = SkillSelector(
                    label="Select Skill",
                    on_change=set_active_skill,
                )
                knowledge_selector = KnowledgeSelector(
                    label="Select Knowledge",
                    on_change=set_active_knowledge,
                )

        with ui.row() as aptitude_display_row:
            if current_aptitude_type is None:
                ui.label("No Aptitude Type Selected").classes("text-gray-500 italic")
            if current_aptitude_type is not None:
                set_active_skill(current_skill_code)
                set_active_knowledge(current_knowledge_code)

        ui.number(label="Level Modifier", value=None, validation={'Cannot be 0': lambda v: v != 0})
        ui.input(label="Context (optional)", placeholder="E.g. Event name or source")
        with ui.row(wrap=False, align_items='end') as action_button_row:
            ui.button("Save", on_click=lambda: None, color='dark').classes("q-mr-sm")



ui.run(dark=True)
