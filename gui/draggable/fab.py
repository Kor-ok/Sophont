from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal, Optional, Union

from nicegui import ui

from game.gene import Gene
from game.phene import Phene
from gui.styles import (
    COLOUR_GENE,
    COLOUR_PHENE,
    DRAG_DROP_BG_ACTIVE,
    DRAG_DROP_BG_INACTIVE,
    DRAGGABLE_FAB_CLASSES,
    FAB_FLYOUT_COLOUR,
    FAB_FLYOUT_PROP,
)

_HERE = Path(__file__).resolve().parent
_GUI_DIR = _HERE.parent


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding='utf-8')


# Compatibility exports: other modules currently import these from gui.draggable.fab
BG_INACTIVE = DRAG_DROP_BG_INACTIVE
BG_ACTIVE = DRAG_DROP_BG_ACTIVE
FLYOUT_COLOUR = FAB_FLYOUT_COLOUR

dragged: Optional[draggable] = None

_FAB_LAYER_CSS_ADDED = False
_DISABLE_TOOLTIP_JS_TEMPLATE: str | None = None


def _ensure_fab_layer_css() -> None:
    """Ensure FAB action flyouts render above other UI layers."""
    global _FAB_LAYER_CSS_ADDED  # pylint: disable=global-statement
    if _FAB_LAYER_CSS_ADDED:
        return
    _FAB_LAYER_CSS_ADDED = True

    css_path = _HERE / 'fab.css'
    ui.add_css(_read_text_file(css_path))


def _disable_tooltip_js(element_id: int) -> str:
    global _DISABLE_TOOLTIP_JS_TEMPLATE  # pylint: disable=global-statement
    if _DISABLE_TOOLTIP_JS_TEMPLATE is None:
        js_path = _HERE / 'disable_tooltip.js'
        _DISABLE_TOOLTIP_JS_TEMPLATE = _read_text_file(js_path)
    return _DISABLE_TOOLTIP_JS_TEMPLATE.replace('{self.id}', str(element_id))

def _build_fab_flyout(icon: str, label: str, tooltip: str) -> ui.fab_action:
    return ui.fab_action(icon, label=label, color=FLYOUT_COLOUR).props(FAB_FLYOUT_PROP).classes('text-sm').tooltip(tooltip)

class draggable(ui.fab):
    def __init__(
        self,
        gene: Union[Gene, Phene],
        icon: Optional[str] = None,
        color: Optional[str] = None,
        direction: Literal['up', 'down', 'left', 'right'] = 'right',
        on_remove: Optional[Callable[[draggable], None]] = None,
        is_draggable_active: bool = True,
    ) -> None:
        _ensure_fab_layer_css()
        item = gene

        if icon is None:
            icon = '🧬' if isinstance(item, Gene) else 'fingerprint'
        if color is None:
            color = COLOUR_GENE if isinstance(item, Gene) else COLOUR_PHENE

        super().__init__(label=item.characteristic.get_name(), icon=icon, color=color, direction=direction)
        self.item: Union[Gene, Phene] = item
        self.icon = icon
        self.color = color
        self.direction: Literal['up', 'down', 'left', 'right'] = direction
        self.on_remove = on_remove
        # Quasar (NiceGUI) styling tips:
        # - `dense` reduces button height
        # - `padding` controls vertical/horizontal padding (v h)
        # - Tailwind classes handle remaining height/text tweaks
        self.props('draggable dense unelevated size=sm padding="xs sm"').classes(DRAGGABLE_FAB_CLASSES)

        if isinstance(item, Gene):
            with self:
                _build_fab_flyout(icon='casino', label=str(item.die_mult), tooltip='Die Multiplier')
                _build_fab_flyout(icon='low_priority', label=str(item.precidence), tooltip='Precidence')
                _build_fab_flyout(icon='transgender', label=str(item.gender_link), tooltip='Gender Link')
                _build_fab_flyout(icon='line_style', label=str(item.caste_link), tooltip='Caste Link')
                _build_fab_flyout(icon='family_restroom', label=str(item.inheritance_contributors), tooltip='Inheritance Contributors')
        elif isinstance(item, Phene):
            with self:
                _build_fab_flyout(icon='bar_chart', label=str(item.expression_value), tooltip='Expression Value')
                _build_fab_flyout(icon='medical_services', label=str(item.is_grafted), tooltip='Is Grafted')
                if item.contributor_uuid != bytes(16):
                    _build_fab_flyout(icon='baby_changing_station', label=str(item.contributor_uuid), tooltip='Contributor UUID')
        else:
            raise TypeError(f'Unsupported draggable item type: {type(item)!r}')
        with self:
            if is_draggable_active:
                ui.fab_action('delete_forever', label='', color='red').props(FAB_FLYOUT_PROP).classes('text-xs').on('click', lambda _: self.request_remove()).tooltip('Remove')
        
        if is_draggable_active:
            self.on('dragstart', self.handle_dragstart)

    def handle_dragstart(self) -> None:
        # Tooltips can become visually orphaned during HTML5 drag operations
        # because the underlying DOM element gets moved/removed without the
        # usual mouseleave/mouseout events firing. Proactively dismiss any
        # visible tooltips as soon as dragging begins.
        ui.run_javascript(_disable_tooltip_js(self.id))
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        dragged = self

    def request_remove(self) -> None:
        """Requests removal.

        If a callback is provided (e.g. to implement undo), it is invoked.
        Otherwise, the element is removed immediately.
        """
        if self.on_remove is not None:
            self.on_remove(self)
            return
        self.remove_now()

    def remove_now(self) -> None:
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        if dragged is self:
            dragged = None
        if self.parent_slot is not None and self.parent_slot.parent is not None:
            self.parent_slot.parent.remove(self)
        else:
            self.delete()