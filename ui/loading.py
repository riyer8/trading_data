"""Background loading UI for Tk table tools."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from ui.theme import Colors, Fonts


def build_loading_panel(parent: tk.Misc, title: str = "Loading…"):
    frame = tk.Frame(parent, bg=Colors.BACKGROUND)
    frame.pack(fill=tk.X, pady=(0, 8))

    status = tk.Label(
        frame,
        text=title,
        bg=Colors.BACKGROUND,
        fg=Colors.TEXT,
        font=(Fonts.sans_name, 13),
        anchor=tk.W,
    )
    status.pack(fill=tk.X)

    detail = tk.Label(
        frame,
        text="Fetching market data in the background.",
        bg=Colors.BACKGROUND,
        fg=Colors.MUTED,
        font=(Fonts.sans_name, 11),
        anchor=tk.W,
    )
    detail.pack(fill=tk.X, pady=(4, 0))

    progress = ttk.Progressbar(frame, mode="determinate")
    progress.pack(fill=tk.X, pady=(10, 0))
    return frame, status, detail, progress


def run_in_background(root, worker, on_done, on_error=None):
    def _run():
        try:
            result = worker()
            root.after(0, lambda: on_done(result))
        except Exception as exc:
            if on_error:
                root.after(0, lambda: on_error(exc))
            else:
                root.after(0, lambda: on_done(None, str(exc)))

    threading.Thread(target=_run, daemon=True).start()


def show_empty_state(status, detail, progress, title: str, message: str):
    progress.pack_forget()
    status.configure(text=title, fg=Colors.ACCENT_5)
    detail.configure(text=message, fg=Colors.ACCENT_5, wraplength=900, justify=tk.LEFT)


def attach_tree_scrollbar(parent, tree):
    """Pack a Treeview with a vertical scrollbar into parent."""
    container = tk.Frame(parent, bg=Colors.BACKGROUND)
    container.pack(fill=tk.BOTH, expand=True)
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return container
