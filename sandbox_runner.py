from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from watchfiles import awatch

SCRIPT_PATH = "sandbox.py" 

WATCH_FOR_CHANGES_TOP_DIR =  str(Path(__file__).resolve().parent)

async def watcher():
    # Run the target script immediately on start.
    await script_process_handler()

    # After the script finishes, wait for filesystem changes and run again.
    async for changes in awatch(WATCH_FOR_CHANGES_TOP_DIR):
        print(f"Detected changes in: {', '.join(str(change[1]) for change in changes)}")
        await script_process_handler()


async def script_process_handler():
    # Spawn a separate Python process to run the script so each run uses
    # a fresh interpreter and cannot leak in-process state.
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            SCRIPT_PATH,
            cwd=WATCH_FOR_CHANGES_TOP_DIR,
        )
        print(f"Started {SCRIPT_PATH} (pid={proc.pid})")
        returncode = await proc.wait()
        print(f"{SCRIPT_PATH} exited with return code {returncode}")
    except Exception as exc:  # Show exceptions from the launcher and continue
        print(f"Error while running {SCRIPT_PATH}: {exc}")


if __name__ == "__main__":
    asyncio.run(watcher())

