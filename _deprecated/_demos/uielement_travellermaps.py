from __future__ import annotations

import asyncio
from typing import Any, Literal

from nicegui import events, ui

from _gui import styles
from api.travellermap import TravellerMapAPI

api = TravellerMapAPI()
running_query: asyncio.Task | None = None
search_results_container: ui.column | None = None
selected_items_container: ui.column | None = None

# Persistent storage for selected items: list of (item_type, item_data) tuples
selected_items: list[tuple[str, dict]] = []


def _make_item_key(item_type: str, item: dict) -> str:
    """Generate a unique key for an item to detect duplicates."""
    if item_type == "World":
        return f"world:{item.get('SectorX')}:{item.get('SectorY')}:{item.get('HexX')}:{item.get('HexY')}"
    elif item_type == "Subsector":
        return f"subsector:{item.get('SectorX')}:{item.get('SectorY')}:{item.get('Index')}"
    elif item_type == "Label":
        return f"label:{item.get('SectorX')}:{item.get('SectorY')}:{item.get('HexX')}:{item.get('HexY')}:{item.get('Name')}"
    return f"{item_type}:{item.get('Name', 'unknown')}"


def _is_item_selected(item_type: str, item: dict) -> bool:
    """Check if an item is already in the selected list."""
    key = _make_item_key(item_type, item)
    return any(_make_item_key(t, i) == key for t, i in selected_items)


def select_item(item_type: str, item: dict) -> None:
    """Add an item to the selected list and refresh the display."""
    if not _is_item_selected(item_type, item):
        selected_items.append((item_type, item.copy()))
        refresh_selected_items()


def remove_selected_item(index: int) -> None:
    """Remove an item from the selected list by index."""
    if 0 <= index < len(selected_items):
        selected_items.pop(index)
        refresh_selected_items()


def clear_selected_items() -> None:
    """Clear all selected items."""
    selected_items.clear()
    refresh_selected_items()


def refresh_selected_items() -> None:
    """Re-render the selected items container."""
    if selected_items_container is None:
        return

    selected_items_container.clear()
    with selected_items_container:
        if not selected_items:
            ui.label("Click items from search results to add them here").classes(
                "text-gray-500 italic text-sm"
            )
            return

        # Header with clear button
        with ui.row().classes("w-full justify-between items-center q-mb-sm"):
            ui.label(f"{len(selected_items)} item(s) selected").classes("text-sm text-green-4")
            ui.button("Clear All", on_click=clear_selected_items).props(
                "flat dense size=sm"
            ).classes("text-red-4")

        # Render each selected item with remove button
        for idx, (item_type, item) in enumerate(selected_items):
            render_item_card(item_type, item, mode="selected", index=idx)


def render_item_card(
    item_type: str,
    item: dict,
    mode: Literal["search", "selected"] = "search",
    index: int = -1,
) -> None:
    """Render an item card based on its type.

    Args:
        item_type: One of 'World', 'Subsector', or 'Label'.
        item: The item data dictionary.
        mode: 'search' for clickable search results, 'selected' for removable selected items.
        index: Index in selected_items list (only used when mode='selected').
    """
    if item_type == "World":
        render_world_item(item, mode, index)
    elif item_type == "Subsector":
        render_subsector_item(item, mode, index)
    elif item_type == "Label":
        render_label_item(item, mode, index)


def render_world_item(
    world: dict,
    mode: Literal["search", "selected"] = "search",
    index: int = -1,
) -> None:
    """Render a World item card."""
    is_selected = _is_item_selected("World", world) if mode == "search" else False
    cursor_class = (
        "cursor-pointer hover:bg-blue-grey-8" if mode == "search" and not is_selected else ""
    )
    opacity_class = "opacity-50" if is_selected else ""

    def on_click() -> None:
        if mode == "search" and not is_selected:
            select_item("World", world)

    def on_remove() -> None:
        if mode == "selected":
            remove_selected_item(index)

    with (
        ui.card()
        .classes(f"w-full q-pa-sm bg-blue-grey-9 {cursor_class} {opacity_class}")
        .on("click", on_click if mode == "search" else lambda: None)
    ):
        with ui.row().classes("w-full justify-between items-start"):
            with ui.column().classes("gap-1"):
                ui.label(world.get("Name", "Unknown")).classes(
                    "text-md font-bold text-light-blue-3"
                )
                with ui.row().classes("gap-4 items-center"):
                    ui.label(f"Sector: {world.get('Sector', '?')}").classes("text-sm")
                    ui.label(
                        f"Hex: {world.get('HexX', '?'):02d}{world.get('HexY', '?'):02d}"
                    ).classes("text-sm font-mono")
                ui.label(f"UWP: {world.get('Uwp', '?')}").classes("text-sm font-mono text-amber-4")
                with ui.row().classes("gap-2 text-xs text-grey-5"):
                    ui.label(
                        f"SectorXY: ({world.get('SectorX', '?')}, {world.get('SectorY', '?')})"
                    )
                    ui.label(f"Tags: {world.get('SectorTags', '')}").classes("italic")
            if mode == "selected":
                ui.button(icon="close", on_click=on_remove).props(
                    "flat dense round size=sm"
                ).classes("text-red-4")
            elif is_selected:
                ui.icon("check_circle").classes("text-green-4")


def render_subsector_item(
    subsector: dict,
    mode: Literal["search", "selected"] = "search",
    index: int = -1,
) -> None:
    """Render a Subsector item card."""
    is_selected = _is_item_selected("Subsector", subsector) if mode == "search" else False
    cursor_class = (
        "cursor-pointer hover:bg-deep-purple-8" if mode == "search" and not is_selected else ""
    )
    opacity_class = "opacity-50" if is_selected else ""

    def on_click() -> None:
        if mode == "search" and not is_selected:
            select_item("Subsector", subsector)

    def on_remove() -> None:
        if mode == "selected":
            remove_selected_item(index)

    with (
        ui.card()
        .classes(f"w-full q-pa-sm bg-deep-purple-9 {cursor_class} {opacity_class}")
        .on("click", on_click if mode == "search" else lambda: None)
    ):
        with ui.row().classes("w-full justify-between items-start"):
            with ui.column().classes("gap-1"):
                ui.label(subsector.get("Name", "Unknown")).classes(
                    "text-md font-bold text-purple-3"
                )
                with ui.row().classes("gap-4 items-center"):
                    ui.label(f"Sector: {subsector.get('Sector', '?')}").classes("text-sm")
                    ui.label(f"Index: {subsector.get('Index', '?')}").classes("text-sm font-mono")
                with ui.row().classes("gap-2 text-xs text-grey-5"):
                    ui.label(
                        f"SectorXY: ({subsector.get('SectorX', '?')}, {subsector.get('SectorY', '?')})"
                    )
                    ui.label(f"Tags: {subsector.get('SectorTags', '')}").classes("italic")
            if mode == "selected":
                ui.button(icon="close", on_click=on_remove).props(
                    "flat dense round size=sm"
                ).classes("text-red-4")
            elif is_selected:
                ui.icon("check_circle").classes("text-green-4")


def render_label_item(
    label: dict,
    mode: Literal["search", "selected"] = "search",
    index: int = -1,
) -> None:
    """Render a Label item card."""
    is_selected = _is_item_selected("Label", label) if mode == "search" else False
    cursor_class = "cursor-pointer hover:bg-teal-8" if mode == "search" and not is_selected else ""
    opacity_class = "opacity-50" if is_selected else ""

    def on_click() -> None:
        if mode == "search" and not is_selected:
            select_item("Label", label)

    def on_remove() -> None:
        if mode == "selected":
            remove_selected_item(index)

    with (
        ui.card()
        .classes(f"w-full q-pa-sm bg-teal-9 {cursor_class} {opacity_class}")
        .on("click", on_click if mode == "search" else lambda: None)
    ):
        with ui.row().classes("w-full justify-between items-start"):
            with ui.column().classes("gap-1"):
                ui.label(label.get("Name", "Unknown")).classes("text-md font-bold text-teal-3")
                with ui.row().classes("gap-4 items-center"):
                    ui.label(
                        f"Hex: {label.get('HexX', '?'):02d}{label.get('HexY', '?'):02d}"
                    ).classes("text-sm font-mono")
                    ui.label(f"Scale: {label.get('Scale', '?')}").classes("text-sm")
                with ui.row().classes("gap-2 text-xs text-grey-5"):
                    ui.label(
                        f"SectorXY: ({label.get('SectorX', '?')}, {label.get('SectorY', '?')})"
                    )
                    ui.label(f"Tags: {label.get('SectorTags', '')}").classes("italic")
            if mode == "selected":
                ui.button(icon="close", on_click=on_remove).props(
                    "flat dense round size=sm"
                ).classes("text-red-4")
            elif is_selected:
                ui.icon("check_circle").classes("text-green-4")


def render_search_results(data: dict[str, Any] | None) -> None:
    """Render the search results in the results container."""
    if search_results_container is None:
        return

    search_results_container.clear()
    with search_results_container:
        if data is None:
            ui.label("No Results").classes("text-gray-500 italic")
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
        ui.label("Click to select").classes("text-xs text-grey-5 q-mb-sm")

        # ===== CATEGORIZE ITEMS =====
        worlds = [item["World"] for item in items if "World" in item]
        subsectors = [item["Subsector"] for item in items if "Subsector" in item]
        labels = [item["Label"] for item in items if "Label" in item]

        # ===== RENDER WORLDS =====
        if worlds:
            with (
                ui.expansion(f"Worlds ({len(worlds)})", icon="public")
                .classes("w-full text-light-blue-3")
                .props("default-opened")
            ):
                for world in worlds:
                    render_item_card("World", world, mode="search")

        # ===== RENDER SUBSECTORS =====
        if subsectors:
            with ui.expansion(f"Subsectors ({len(subsectors)})", icon="grid_view").classes(
                "w-full text-purple-3"
            ):
                for subsector in subsectors:
                    render_item_card("Subsector", subsector, mode="search")

        # ===== RENDER LABELS =====
        if labels:
            with ui.expansion(f"Labels ({len(labels)})", icon="label").classes(
                "w-full text-teal-3"
            ):
                for label in labels:
                    render_item_card("Label", label, mode="search")


async def search(e: events.ValueChangeEventArguments) -> None:
    """Search TravellerMap as you type."""
    global running_query  # pylint: disable=global-statement # noqa: PLW0603
    if running_query:
        running_query.cancel()  # cancel the previous query; happens when you type fast
    search_field.classes("mt-2", remove="mt-24")  # move the search field up

    # Skip empty queries
    if not e.value or not e.value.strip():
        running_query = None
        if search_results_container:
            search_results_container.clear()
        return

    # Store the http coroutine in a task so we can cancel it later if needed
    running_query = asyncio.create_task(api.search_async(e.value))
    try:
        search_results = await running_query
    except asyncio.CancelledError:
        return  # Query was cancelled by a newer search
    except Exception as ex:
        if search_results_container:
            search_results_container.clear()
            with search_results_container:
                ui.label(f"Search error: {ex}").classes("text-red-500")
        running_query = None
        return

    render_search_results(search_results)
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

        with ui.column().classes(
            "w-128 q-pa-md items-center justify-center"
        ) as map_display_results_container:
            search_results_container = ui.column().classes("w-full q-pa-none gap-1")

    # RIGHT COLUMN ==================== SELECTED ITEMS
    with ui.column().classes(styles.TAB_COLUMN_RIGHT) as right_column:
        with ui.card().classes("w-128 q-pa-md"):
            ui.label("Selected Items").classes("text-lg font-medium q-mb-md")
            selected_items_container = ui.column().classes("w-full q-pa-none gap-1")
            # Initial placeholder
            with selected_items_container:
                ui.label("Click items from search results to add them here").classes(
                    "text-gray-500 italic text-sm"
                )

ui.run(dark=True)
