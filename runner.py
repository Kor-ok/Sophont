from __future__ import annotations

import asyncio
import subprocess
import sys
import threading
from pathlib import Path

from rich import print
from watchfiles import awatch

from utils import get_all_folders_from

INITIAL_SCRIPT = Path("D:\\Projects\\Python\\Sophont\\sandbox.py")

_running_script = INITIAL_SCRIPT
_watch_for_changes_dirs = get_all_folders_from(_running_script.parent)

_scripts: dict[int, Path] = {}

# ---------------------------------------------------------------------------
# Async stdin reader – a single daemon thread reads lines from stdin and
# pushes them into an asyncio.Queue so that awaiting user input is
# cancellable by the event loop.
# ---------------------------------------------------------------------------
# NOTE: On Python 3.9, asyncio primitives (like Queue) are bound to the loop
# they are created with. Since asyncio.run() creates a fresh loop, we must not
# create the Queue at import time.
_input_queue: asyncio.Queue[str] | None = None
_stdin_reader_started = False
_stdin_reader_loop: asyncio.AbstractEventLoop | None = None


def _get_input_queue() -> asyncio.Queue[str]:
    global _input_queue
    if _input_queue is None:
        _input_queue = asyncio.Queue()
    return _input_queue


def _start_stdin_reader(loop: asyncio.AbstractEventLoop):
    """On Windows,  there is a  known  issue where connect_read_pipe does not
    work with sys.stdin due to a bug. As a workaround,  non-blocking input
    can be achieved by calling  sys.stdin.readline() in a separate thread.
    This approach allows the application to  handle input without blocking
    the main thread, ensuring that the application remains responsive even
    while waiting for user input."""

    global _stdin_reader_started, _stdin_reader_loop

    # Ensure we only ever start a single thread that reads from stdin.
    # Starting multiple readers can cause lost/duplicated input and makes
    # cancellation behavior unpredictable.
    if _stdin_reader_started:
        return

    _stdin_reader_started = True
    _stdin_reader_loop = loop

    def _reader():
        while True:
            try:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break
                # Use the loop captured at startup. If the loop is closed,
                # just stop the reader.
                target_loop = _stdin_reader_loop
                if target_loop is None or target_loop.is_closed():
                    break
                queue = _input_queue
                if queue is None:
                    # Queue isn't initialized yet; drop input until the event
                    # loop sets it up.
                    continue
                target_loop.call_soon_threadsafe(
                    queue.put_nowait,
                    line.rstrip("\n"),
                )
            except (EOFError, OSError):
                break

    t = threading.Thread(target=_reader, daemon=True)
    t.start()


async def _async_input(prompt: str = "") -> str:
    """Cancellable replacement for ``input()``."""
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    return await _get_input_queue().get()


async def _drain_input_queue():
    """Discard any stale input sitting in the queue.

    call_soon_threadsafe schedules callbacks on the event loop — we must
    yield first so those callbacks execute and land in the queue before we
    drain it.
    """
    await asyncio.sleep(0)          # let pending threadsafe callbacks run
    queue = _input_queue
    if queue is None:
        return

    while not queue.empty():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break


# ---------------------------------------------------------------------------
# Script selection UI
# ---------------------------------------------------------------------------

async def prompt_script_selection() -> None:
    """Wait for the user to pick a script number.

    This is fully cancellable – if the task is cancelled while waiting for
    input, the CancelledError propagates immediately.
    """
    global _scripts, _running_script
    
    while True:
        selected = await _async_input("run: ")

        if not selected:
            previously_running_script_number: int | None = None
            for number, item in _scripts.items():
                if item == _running_script:
                    previously_running_script_number = number
                    break
            if previously_running_script_number is None:
                print("No previously running script found. Please select a script to run.")
                continue          # keep prompting – don't break without a valid script
            else:
                print(f"No selection made. Defaulting to {_scripts[previously_running_script_number]}.")
            break

        if not selected.isdigit():
            print(f"Invalid input: {selected}. Please enter a number corresponding to the script.")
            continue

        selected_number = int(selected)

        if selected_number in _scripts:
            print(f"Selected script: {_scripts[selected_number]}")
            _running_script = _scripts[selected_number]
            break
        else:
            print(f"Invalid selection: {selected}")
            continue


async def display_scripts() -> None:
    global _scripts

    _scripts.clear()  # Clear previous scripts before repopulating


    print(f"\n[color(232)]Scripts in {_running_script.parent}:[/color(232)]")

    for item in _running_script.parent.iterdir():
        if item.is_file() and item.suffix == ".py":
            if item == Path(__file__):
                continue
            number = len(_scripts) + 1
            _scripts[number] = item

    for number, item in _scripts.items():
        if item == _running_script:
            print(f"     [bold green]{number}: {item.name}[/bold green]")
        else:
            print(f"     {number}: {item.name}")

    await prompt_script_selection()


# ---------------------------------------------------------------------------
# File-watcher helper
# ---------------------------------------------------------------------------

async def _wait_for_change() -> None:
    """Wait for filesystem changes.

    Includes a short settle period so that stale OS-level notifications
    generated during the preceding script run (e.g. .pyc writes, temp
    files) are delivered and discarded *before* we start listening.  A
    fresh ``awatch`` only reports changes that occur after it starts.
    """
    await asyncio.sleep(0.5)
    async for _changes in awatch(*_watch_for_changes_dirs, recursive=False):
        return


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def watcher() -> None:
    global _running_script

    # Start the stdin reader with the running event loop (Windows workaround).
    _get_input_queue()
    _start_stdin_reader(asyncio.get_running_loop())

    while True:
        # 1. Run the currently selected script.
        success = await script_process_handler()

        # Flush any threadsafe callbacks, then discard stale input.
        await _drain_input_queue()

        if not success:
            # Script failed – wait only for a file change before re-running.
            await _wait_for_change()
            print("\n[italic color(232)]File change detected, re-running…[/italic color(232)]")
            continue

        # 2. Script succeeded – race: user selection vs filesystem change.
        previously_running_script = _running_script
        prompt_task: asyncio.Task[None] = asyncio.create_task(display_scripts())
        change_task: asyncio.Task[None] = asyncio.create_task(_wait_for_change())

        done, pending = await asyncio.wait(
            {prompt_task, change_task},
            return_when=asyncio.FIRST_COMPLETED,
        )


        # Cancel whichever task lost the race.
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if change_task in done:
            # A file changed while prompting; cancel the prompt and immediately
            # re-run the previously running script.
            _running_script = previously_running_script
            await _drain_input_queue()
            print("\n[italic color(232)]File change detected, re-running…[/italic color(232)]")
            continue

        # Prompt completed; propagate any exceptions and then re-run (possibly
        # with the newly selected script).
        try:
            await prompt_task
        finally:
            await _drain_input_queue()


async def script_process_handler() -> bool:
    """Run the selected script. Returns True on success (exit code 0)."""

    print("\033c", end="")
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(_running_script),
            cwd=_running_script.parent,
            stdin=subprocess.DEVNULL,  # prevent child from stealing stdin
        )
        print(f"[italic color(232)]Started {_running_script.stem} (pid={proc.pid})[/italic color(232)]")
        returncode = await proc.wait()
        if returncode != 0:
            print(f"[bold red]{_running_script.stem} exited with return code {returncode}[/bold red]")
            return False
        else:
            print(f"[italic color(232)]{_running_script.stem} completed successfully[/italic color(232)]")
            return True

    except Exception as exc:  # Show exceptions from the launcher and continue
        print(f"Error while running {_running_script.stem}: {exc}")
        return False


if __name__ == "__main__":
    asyncio.run(watcher())

