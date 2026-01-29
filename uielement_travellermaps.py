from __future__ import annotations

import asyncio
import json

import httpx
from nicegui import events, ui

from game.mappings.world_id import SystemID
from gui import styles

api = httpx.AsyncClient()
running_query: asyncio.Task | None = None
debug_data_container: ui.column | None = None

def _parse_into_system_id(system: dict) -> SystemID:
    """Parse a system dictionary into a SystemID dataclass."""
    return SystemID(
        sector_x=system.get("SectorX", -1),
        sector_y=system.get("SectorY", -1),
        hex_x=system.get("HexX", -1),
        hex_y=system.get("HexY", -1),
        tag=system.get("SectorTags", ""),
    )

def render_system_item(system: dict) -> None:
    """Render a System item card."""
    sys_id = _parse_into_system_id(system)
    with ui.card().classes("w-full q-pa-sm bg-green-9"):
        ui.label(system.get("Name", "Unknown")).classes("text-md font-bold text-green-3")
        with ui.row().classes("gap-4 items-center"):
            # ui.label(f"Sector: {system.get('Sector', '?')}").classes("text-sm")
            ui.label(f"Hex: {sys_id.hex_x:02d}{sys_id.hex_y:02d}").classes("text-sm font-mono")
        with ui.row().classes("gap-2 text-xs text-grey-5"):
            ui.label(f"SectorXY: ({sys_id.sector_x}, {sys_id.sector_y})")
            ui.label(f"Tag: {sys_id.tag}").classes("italic")

def render_world_item(world: dict) -> None:
    """Render a World item card."""
    with ui.card().classes("w-full q-pa-sm bg-blue-grey-9"):
        ui.label(world.get("Name", "Unknown")).classes("text-md font-bold text-light-blue-3")
        with ui.row().classes("gap-4 items-center"):
            ui.label(f"Sector: {world.get('Sector', '?')}").classes("text-sm")
            ui.label(f"Hex: {world.get('HexX', '?'):02d}{world.get('HexY', '?'):02d}").classes(
                "text-sm font-mono"
            )
        ui.label(f"UWP: {world.get('Uwp', '?')}").classes("text-sm font-mono text-amber-4")
        with ui.row().classes("gap-2 text-xs text-grey-5"):
            ui.label(f"SectorXY: ({world.get('SectorX', '?')}, {world.get('SectorY', '?')})")
            ui.label(f"Tags: {world.get('SectorTags', '')}").classes("italic")


def render_subsector_item(subsector: dict) -> None:
    """Render a Subsector item card."""
    with ui.card().classes("w-full q-pa-sm bg-deep-purple-9"):
        ui.label(subsector.get("Name", "Unknown")).classes("text-md font-bold text-purple-3")
        with ui.row().classes("gap-4 items-center"):
            ui.label(f"Sector: {subsector.get('Sector', '?')}").classes("text-sm")
            ui.label(f"Index: {subsector.get('Index', '?')}").classes("text-sm font-mono")
        with ui.row().classes("gap-2 text-xs text-grey-5"):
            ui.label(
                f"SectorXY: ({subsector.get('SectorX', '?')}, {subsector.get('SectorY', '?')})"
            )
            ui.label(f"Tags: {subsector.get('SectorTags', '')}").classes("italic")


def render_label_item(label: dict) -> None:
    """Render a Label item card."""
    with ui.card().classes("w-full q-pa-sm bg-teal-9"):
        ui.label(label.get("Name", "Unknown")).classes("text-md font-bold text-teal-3")
        with ui.row().classes("gap-4 items-center"):
            ui.label(f"Hex: {label.get('HexX', '?'):02d}{label.get('HexY', '?'):02d}").classes(
                "text-sm font-mono"
            )
            ui.label(f"Scale: {label.get('Scale', '?')}").classes("text-sm")
        with ui.row().classes("gap-2 text-xs text-grey-5"):
            ui.label(f"SectorXY: ({label.get('SectorX', '?')}, {label.get('SectorY', '?')})")
            ui.label(f"Tags: {label.get('SectorTags', '')}").classes("italic")


def render_debug_view(raw_json: str | None) -> None:
    """Render the debug/data view for the search results."""
    if debug_data_container is None:
        return

    debug_data_container.clear()
    with debug_data_container:
        if raw_json is None:
            ui.label("No Results").classes("text-gray-500 italic")
            return

        # ===== PARSE JSON =====
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            ui.label("Failed to parse JSON").classes("text-red-500")
            ui.label(str(e)).classes("text-xs text-grey-5")
            return

        # ===== EXTRACT RESULTS =====
        results_data = data.get("Results")
        if results_data is None:
            ui.label("No 'Results' key in response").classes("text-orange-500 italic")
            return

        count = results_data.get("Count", 0)
        items = results_data.get("Items", [])

        # ===== HEADER =====
        ui.label(f"Found {count} result(s)").classes("text-lg font-medium text-green-4 q-mb-sm")

        # ===== CATEGORIZE ITEMS =====
        systems = [item["World"] for item in items if "World" in item]
        worlds = [item["World"] for item in items if "World" in item]
        subsectors = [item["Subsector"] for item in items if "Subsector" in item]
        labels = [item["Label"] for item in items if "Label" in item]
        # ===== RENDER SYSTEMS =====
        if systems:
            with (
                ui.expansion(f"Systems ({len(systems)})", icon="public")
                .classes("w-full text-green-3")
                .props("default-opened")
            ):
                for system in systems:
                    render_system_item(system)
        # ===== RENDER WORLDS =====
        if worlds:
            with (
                ui.expansion(f"Worlds ({len(worlds)})", icon="public")
                .classes("w-full text-light-blue-3")
                .props("default-opened")
            ):
                for world in worlds:
                    render_world_item(world)

        # ===== RENDER SUBSECTORS =====
        if subsectors:
            with ui.expansion(f"Subsectors ({len(subsectors)})", icon="grid_view").classes(
                "w-full text-purple-3"
            ):
                for subsector in subsectors:
                    render_subsector_item(subsector)

        # ===== RENDER LABELS =====
        if labels:
            with ui.expansion(f"Labels ({len(labels)})", icon="label").classes(
                "w-full text-teal-3"
            ):
                for label in labels:
                    render_label_item(label)


async def search(e: events.ValueChangeEventArguments) -> None:
    """Search TravellerMap as you type."""
    global running_query  # pylint: disable=global-statement # noqa: PLW0603
    if running_query:
        running_query.cancel()  # cancel the previous query; happens when you type fast
    search_field.classes("mt-2", remove="mt-24")  # move the search field up
    results.clear()
    # store the http coroutine in a task so we can cancel it later if needed
    running_query = asyncio.create_task(api.get(f"https://travellermap.com/api/search?q={e.value}"))
    response = await running_query
    if response.text == "":
        return
    with results:
        render_debug_view(response.text)

    running_query = None


with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Map Development").classes("text-sm font-thin q-ma-none")


with ui.row().classes(styles.TAB_ROW):
    # LEFT COLUMN ===================== MAP SEARCH & DISPLAY
    with ui.column().classes(styles.TAB_COLUMN_LEFT) as map_container:
        with ui.column().classes(
            "w-128 q-pa-md items-center justify-center"
        ) as map_search_container:
            # create a search field which is initially focused and leaves space at the top
            search_field = (
                ui.input(on_change=search)
                .props('autofocus outlined rounded item-aligned input-class="ml-3"')
                .classes("w-96 self-center mt-24 transition-all")
            )
            results = ui.row()

        with ui.column().classes(
            "w-128 q-pa-md items-center justify-center"
        ) as map_display_container:
            pass

    # RIGHT COLUMN ==================== MAP DEBUG / DATA VIEW
    with ui.column().classes(styles.TAB_COLUMN_RIGHT) as right_column:
        with ui.card().classes("w-128 q-pa-md"):
            ui.label("Debug / Data View").classes("text-lg font-medium q-mb-md")
            debug_data_container = ui.column().classes("q-pa-none gap-1")

ui.run(dark=True)
