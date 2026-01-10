"""Centralized UI style tokens for the NiceGUI/Tailwind layer.

Keep this module focused on reusable class-string constants ("design tokens")
so UI modules don't need to hard-code colors or repeatedly retype common class
fragments.
"""

from __future__ import annotations

from typing import Final


def cx(*parts: str) -> str:
    """Join Tailwind/NiceGUI class fragments with spaces."""

    return " ".join(part for part in parts if part)


# Backwards-compatible raw color tokens (avoid using these directly in new code).
COLOUR_GENE: Final[str] = "purple-11"
COLOUR_PHENE: Final[str] = "blue"


# Draggable / drop-container styles.
DRAG_DROP_BG_INACTIVE: Final[str] = "bg-grey-10"
DRAG_DROP_BG_ACTIVE: Final[str] = "bg-blue-grey-10"


# FAB (floating action button) styles.
FAB_FLYOUT_COLOUR: Final[str] = "gray"
DRAGGABLE_FAB_CLASSES: Final[str] = (
    "cursor-grab text-xs leading-none min-h-0 h-5 px-0 py-0 draggable-fab-layer"
)
FAB_FLYOUT_PROP: Final[str] = 'dense size=xs padding="xs"'

# Draggable Card
DRAGGABLE_CARD_CLASSES: Final[str] = 'cursor-grab dense unelevated size=sm padding="xs sm" bg-cyan-10'
UNDRAGGABLE_CARD_CLASSES: Final[str] = 'cursor-pointer dense unelevated size=sm padding="xs sm"'

# Common UPP widget styles.
UPP_ROOT: Final[str] = "w-full"
UPP_GRID: Final[str] = "w-full gap-1"
UPP_INDEX_LABEL: Final[str] = "w-full text-center text-xs font-bold leading-none"
UPP_CELL_LABEL: Final[str] = "w-full text-center text-xs leading-none"

UPP_GENE_CELL_LABEL: Final[str] = cx(UPP_CELL_LABEL, f"bg-{COLOUR_GENE}", "text-grey-10", "font-extrabold")
UPP_PHENE_CELL_LABEL: Final[str] = cx(UPP_CELL_LABEL, f"bg-{COLOUR_PHENE}", "text-grey-10", "font-regular", "italic")


# Tab layout styles.
TAB_PANEL: Final[str] = "w-full h-full"
TAB_ROW: Final[str] = "w-full h-full flex-nowrap gap-4"
TAB_COLUMN_BASE: Final[str] = "flex-1 min-w-0 h-full"

TAB_COLUMN_LEFT: Final[str] = cx(TAB_COLUMN_BASE, "items-start", "text-left")
TAB_COLUMN_CENTER: Final[str] = cx(TAB_COLUMN_BASE, "items-center", "text-center")
TAB_COLUMN_RIGHT: Final[str] = cx(TAB_COLUMN_BASE, "items-end", "text-right")

FIXED_PICKABLES_SCROLLER: Final[str] = "w-full flex-1 overflow-y-auto"

# Expandable Group Style
CATEGORY_EXPANDER: Final[str] = "w-full text-left text-xs leading-none px-1 py-0 q-py-xs padding-0"

# Character card layout styles.
CHARACTER_CARD: Final[str] = "w-full"
CHARACTER_IMAGE_FRAME: Final[str] = "w-32 h-32 flex items-center justify-center mx-auto"
CHARACTER_IMAGE: Final[str] = "max-w-full max-h-full object-contain"

CHARACTER_CARD_SECTION: Final[str] = "w-full px-2"
CHARACTER_GRID: Final[str] = (
    "grid-cols-[max-content_max-content] gap-2 justify-items-start items-start text-left"
)


__all__ = [
    "cx",
    "COLOUR_GENE",
    "COLOUR_PHENE",
    "DRAG_DROP_BG_INACTIVE",
    "DRAG_DROP_BG_ACTIVE",
    "FAB_FLYOUT_COLOUR",
    "FAB_FLYOUT_PROP",
    "DRAGGABLE_FAB_CLASSES",
    "UPP_ROOT",
    "UPP_GRID",
    "UPP_INDEX_LABEL",
    "UPP_CELL_LABEL",
    "UPP_GENE_CELL_LABEL",
    "UPP_PHENE_CELL_LABEL",
    "TAB_PANEL",
    "TAB_ROW",
    "TAB_COLUMN_BASE",
    "TAB_COLUMN_LEFT",
    "TAB_COLUMN_CENTER",
    "TAB_COLUMN_RIGHT",
    "FIXED_PICKABLES_SCROLLER",
    "CATEGORY_EXPANDER",
    "CHARACTER_CARD",
    "CHARACTER_IMAGE_FRAME",
    "CHARACTER_IMAGE",
    "CHARACTER_CARD_SECTION",
    "CHARACTER_GRID",
]
