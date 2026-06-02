"""Launch toolkit modules from the chatbot."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class LaunchResult:
    module: str
    args: tuple[str, ...]
    pid: int


def launch_module(module: str, args: list[str] | None = None) -> LaunchResult:
    """Launch a tool in a detached process so the chatbot stays responsive."""
    args = args or []
    popen_kwargs: dict = {
        "cwd": PROJECT_ROOT,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(
        [sys.executable, "-m", module, *args],
        **popen_kwargs,
    )
    return LaunchResult(module=module, args=tuple(args), pid=process.pid)


def format_command(module: str, args: list[str] | None = None) -> str:
    args = args or []
    arg_text = " ".join(args)
    return f"python -m {module}" + (f" {arg_text}" if arg_text else "")
