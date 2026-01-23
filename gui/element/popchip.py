from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

from nicegui import ui

import gui.styles as styles
from game.gene import Gene
from game.phene import Phene

_HERE = Path(__file__).resolve().parent

def _read_text_file(path: Path) -> str:
    return path.read_text(encoding='utf-8')

_POPCHIP_LAYER_CSS_ADDED = False

def _ensure_popchip_css() -> None:
    """Ensure FAB action flyouts render above other UI layers."""
    global _POPCHIP_LAYER_CSS_ADDED  # pylint: disable=global-statement
    if _POPCHIP_LAYER_CSS_ADDED:
        return
    _POPCHIP_LAYER_CSS_ADDED = True

    css_path = _HERE / 'popchip.css'
    ui.add_css(_read_text_file(css_path))

def _build_fab_flyout(icon: str, label: str, tooltip: str) -> ui.fab_action:
    return ui.fab_action(icon, label=label, color=styles.FAB_FLYOUT_COLOUR).props(styles.FAB_FLYOUT_PROP).classes('text-sm').tooltip(tooltip)

class Popchip(ui.fab):
    def __init__(
        self,
        item: Union[Gene, Phene],
        icon: Optional[str] = None,
        color: Optional[str] = None,
        direction: Literal['up', 'down', 'left', 'right'] = 'right',
    ) -> None:
        _ensure_popchip_css()
        if icon is None:
            icon = '🧬' if isinstance(item, Gene) else 'fingerprint'
        if color is None:
            color = styles.COLOUR_GENE if isinstance(item, Gene) else styles.COLOUR_PHENE
        
        super().__init__(label=item.characteristic.get_name()[0], icon=icon, color=color, direction=direction)
        self.item: Union[Gene, Phene] = item
        self.icon = icon
        self.color = color
        self.direction: Literal['up', 'down', 'left', 'right'] = direction
        self.props('draggable dense unelevated size=sm padding="xs sm"').classes(styles.DRAGGABLE_FAB_CLASSES)

        if isinstance(item, Gene):
            with self:
                _build_fab_flyout(icon='casino', label=str(item.die_mult), tooltip='Die Multiplier')
                _build_fab_flyout(icon='low_priority', label=str(item.precidence), tooltip='Precidence')
                _build_fab_flyout(icon='transgender', label=str(item.gender_link), tooltip='Gender Link')
                _build_fab_flyout(icon='line_style', label=str(item.caste_link), tooltip='Caste Link')
                _build_fab_flyout(icon='family_restroom', label=str(item.inheritance_contributors), tooltip='Inheritance Contributors')
        elif isinstance(item, Phene):
            with self:
                _build_fab_flyout(icon='bar_chart', label=str(item.expression_precidence), tooltip='Expression Value')
                _build_fab_flyout(icon='medical_services', label=str(item.is_grafted), tooltip='Is Grafted')
                if item.contributor_uuid != bytes(16):
                    _build_fab_flyout(icon='baby_changing_station', label=str(item.contributor_uuid), tooltip='Contributor UUID')
        else:
            raise TypeError(f'Unsupported draggable item type: {type(item)!r}')