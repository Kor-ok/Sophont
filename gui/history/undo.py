from __future__ import annotations

# from dataclasses import dataclass
from nicegui import ui


class Command:
    """PLACEHOLDER"""
    def undo(self) -> None:
        """PLACEHOLDER"""
        pass
    pass

def notify_undo(message: str, command: Command, *, timeout_seconds: float = 60.0) -> None:
    state = {'expired': False}

    def on_dismiss() -> None:
        if state['expired']:
            return
        command.undo()

    notification = ui.notification(
        message,
        close_button='Undo',
        timeout=0,  # we control expiry ourselves to avoid undo-on-timeout
        type='ongoing',
        position='bottom',
        on_dismiss=on_dismiss,
    )

    def expire() -> None:
        state['expired'] = True
        try:
            notification.dismiss()
        except Exception:
            pass

    ui.timer(timeout_seconds, expire, once=True)