from __future__ import annotations

# from dataclasses import dataclass
from typing import Callable, Literal, Optional, Union  # Protocol

from nicegui import ui

from game.gene import Gene
from game.phene import Phene

dna_icon_path = 'gui/icons/dna.svg'
# read svg content as plain text
with open(dna_icon_path, encoding='utf-8') as f:
    dna_icon_svg = f.read()


BG_INACTIVE = 'bg-grey-10'
BG_ACTIVE = 'bg-blue-grey-10'

dragged: Optional[draggable] = None

class draggable(ui.fab):
    def __init__(
        self,
        gene: Union[Gene, Phene],
        icon: Optional[str] = None,
        color: Optional[str] = None,
        direction: Literal['up', 'down', 'left', 'right'] = 'right',
        on_remove: Optional[Callable[[draggable], None]] = None,
    ) -> None:
        item = gene

        if icon is None:
            icon = '🧬' if isinstance(item, Gene) else 'fingerprint'
        if color is None:
            color = 'purple-11' if isinstance(item, Gene) else 'blue'

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
        self.props('draggable dense unelevated size=sm padding="xs sm"').classes(
            'cursor-grab text-xs leading-none min-h-0 h-7 px-1 py-0'
        )

        if isinstance(item, Gene):
            with self:
                ui.fab_action('casino', label=str(item.die_mult), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Die Multiplier')
                ui.fab_action('low_priority', label=str(item.precidence), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Precidence')
                ui.fab_action('transgender', label=str(item.gender_link), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Gender Link')
                ui.fab_action('line_style', label=str(item.caste_link), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Caste Link')
                ui.fab_action('family_restroom', label=str(item.inheritance_contributors), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Inheritance Contributors')
        elif isinstance(item, Phene):
            with self:
                ui.fab_action('bar_chart', label=str(item.expression_value), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Expression Value')
                ui.fab_action('medical_services', label=str(item.is_grafted), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Is Grafted')
                ui.fab_action('baby_changing_station', label=str(item.contributor_uuid), color='gray').props('dense size=xs padding="xs"').classes('text-xs').tooltip('Contributor UUID')
        else:
            raise TypeError(f'Unsupported draggable item type: {type(item)!r}')
        with self:
            ui.fab_action('delete_forever', label='Remove', color='gray').props('dense size=xs padding="xs"').classes('text-xs').on('click', lambda _: self.request_remove()).tooltip('Remove')
        self.on('dragstart', self.handle_dragstart)

    def handle_dragstart(self) -> None:
        # Tooltips can become visually orphaned during HTML5 drag operations
        # because the underlying DOM element gets moved/removed without the
        # usual mouseleave/mouseout events firing. Proactively dismiss any
        # visible tooltips as soon as dragging begins.
        ui.run_javascript(
            f"""(() => {{
    try {{
        const el = getHtmlElement({self.id});
        if (el) {{
            el.dispatchEvent(new MouseEvent('mouseleave', {{ bubbles: true, cancelable: true }}));
            el.dispatchEvent(new MouseEvent('mouseout', {{ bubbles: true, cancelable: true }}));
        }}

        // Safety net: ensure any currently-visible Quasar tooltips are hidden.
        // This avoids stale tooltips lingering when a drag starts mid-hover.
        document.querySelectorAll('.q-tooltip').forEach((tip) => {{
            try {{
                tip.style.display = 'none';
            }} catch (_) {{
                // ignore
            }}
        }});
    }} catch (_) {{
        // ignore
    }}
}})();""",
        )
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