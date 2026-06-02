"""Launch and close toolkit modules from the chatbot."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass, field

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_lock = threading.Lock()
_registry: dict[int, "TrackedProcess"] = {}


@dataclass(frozen=True)
class LaunchResult:
    module: str
    args: tuple[str, ...]
    pid: int


@dataclass
class TrackedProcess:
    pid: int
    module: str
    args: tuple[str, ...] = field(default_factory=tuple)

    @property
    def command(self) -> str:
        return format_command(self.module, list(self.args))

    @property
    def label(self) -> str:
        arg_text = " ".join(self.args)
        base = self.module.rsplit(".", 1)[-1]
        return f"{base} {arg_text}".strip() if arg_text else base


def launch_module(module: str, args: list[str] | None = None) -> LaunchResult:
    """Launch a tool in a detached process so the chatbot stays responsive."""
    args = args or []
    popen_kwargs: dict = {
        "cwd": PROJECT_ROOT,
        "stdin": subprocess.DEVNULL,
        "env": os.environ.copy(),
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
        # close_fds can break matplotlib/Tk GUI subprocesses on macOS.
        if sys.platform != "darwin":
            popen_kwargs["close_fds"] = True

    process = subprocess.Popen(
        [sys.executable, "-m", module, *args],
        **popen_kwargs,
    )
    tracked = TrackedProcess(pid=process.pid, module=module, args=tuple(args))
    with _lock:
        _registry[process.pid] = tracked
    return LaunchResult(module=module, args=tuple(args), pid=process.pid)


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _prune_dead() -> None:
    with _lock:
        dead = [pid for pid in _registry if not _is_alive(pid)]
        for pid in dead:
            _registry.pop(pid, None)


def list_running() -> list[TrackedProcess]:
    _prune_dead()
    with _lock:
        return sorted(_registry.values(), key=lambda item: item.pid)


def format_running_context() -> str:
    running = list_running()
    if not running:
        return "RUNNING APPLICATIONS: none"
    lines = ["RUNNING APPLICATIONS (chatbot can close these on request):"]
    for proc in running:
        lines.append(f"- pid {proc.pid}: {proc.command}")
    return "\n".join(lines)


def close_process(pid: int) -> bool:
    _prune_dead()
    with _lock:
        if pid not in _registry:
            return False

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture_output=True)
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            with _lock:
                _registry.pop(pid, None)
            return False

    with _lock:
        _registry.pop(pid, None)
    return True


def close_matching(module: str | None = None, args: list[str] | None = None) -> list[int]:
    """Close running tools that match a module and optional args prefix."""
    args = args or []
    closed: list[int] = []
    for proc in list_running():
        if module and proc.module != module:
            continue
        if args and list(proc.args[: len(args)]) != args:
            continue
        if close_process(proc.pid):
            closed.append(proc.pid)
    return closed


def close_all() -> list[int]:
    closed: list[int] = []
    for proc in list_running():
        if close_process(proc.pid):
            closed.append(proc.pid)
    return closed


def format_command(module: str, args: list[str] | None = None) -> str:
    args = args or []
    arg_text = " ".join(args)
    return f"python -m {module}" + (f" {arg_text}" if arg_text else "")
