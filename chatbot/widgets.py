"""Reusable Tkinter widgets for the chatbot."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from ui.theme import Colors, Fonts


def _lighten(hex_color: str, amount: float = 0.12) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


class PillButton(tk.Canvas):
    """Rounded pill button for actions and examples."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        fill: str = Colors.HEADER,
        hover: str | None = None,
        fg: str = Colors.TEXT,
        accent: bool = False,
        soft: bool = False,
        font: tkfont.Font | None = None,
        padx: int = 16,
        pady: int = 8,
        bg: str = Colors.BACKGROUND,
    ):
        self._command = command
        self._text = text
        if accent:
            self._fill = Colors.ACCENT
            self._hover = _lighten(Colors.ACCENT, 0.12)
            self._fg = "#ffffff"
        elif soft:
            self._fill = Colors.HEADER
            self._hover = Colors.GRID
            self._fg = Colors.TEXT
        else:
            self._fill = fill
            self._hover = _lighten(fill, 0.15) if hover is None else hover
            self._fg = fg
        self._font = font or tkfont.Font(family=Fonts.sans_name, size=11)
        self._padx = padx
        self._pady = pady
        self._enabled = True
        self._bg = bg

        width = self._font.measure(text) + padx * 2
        height = self._font.metrics("linespace") + pady * 2

        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            borderwidth=0,
            bg=bg,
            cursor="hand2",
        )
        self._draw(self._fill)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, fill: str) -> None:
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        r = h // 2
        self.create_oval(0, 0, r * 2, h, fill=fill, outline=fill)
        self.create_oval(w - r * 2, 0, w, h, fill=fill, outline=fill)
        self.create_rectangle(r, 0, w - r, h, fill=fill, outline=fill)
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg, font=self._font)

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self._draw(self._hover)

    def _on_leave(self, _event) -> None:
        if self._enabled:
            self._draw(self._fill)

    def _on_click(self, _event) -> None:
        if self._enabled:
            self._command()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        if not enabled:
            self._draw(Colors.GRID)


class CircleButton(tk.Canvas):
    """Circular send button."""

    def __init__(
        self,
        parent: tk.Misc,
        command: Callable[[], None],
        *,
        size: int = 40,
        fill: str = Colors.ACCENT,
        hover: str | None = None,
        bg: str = Colors.PANEL,
    ):
        self._command = command
        self._fill = fill
        self._hover = hover or _lighten(fill, 0.12)
        self._size = size
        self._enabled = True
        self._font = tkfont.Font(family=Fonts.sans_name, size=15, weight="bold")
        self._bg = bg

        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            borderwidth=0,
            bg=bg,
            cursor="hand2",
        )
        self._draw(self._fill)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, fill: str) -> None:
        self.delete("all")
        s = self._size
        self.create_oval(2, 2, s - 2, s - 2, fill=fill, outline=fill)
        self.create_text(s // 2, s // 2 - 1, text="↑", fill="#ffffff", font=self._font)

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self._draw(self._hover)

    def _on_leave(self, _event) -> None:
        if self._enabled:
            self._draw(self._fill)

    def _on_click(self, _event) -> None:
        if self._enabled:
            self._command()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw(self._fill if enabled else Colors.GRID)


class PromptRow(tk.Frame):
    """Example prompt chips."""

    def __init__(
        self,
        parent: tk.Misc,
        prompts: list[str],
        on_pick: Callable[[str], None],
        *,
        bg: str = Colors.BACKGROUND,
    ):
        super().__init__(parent, bg=bg)
        wrap = tk.Frame(self, bg=bg)
        wrap.pack(fill=tk.X)

        for prompt in prompts:
            PillButton(
                wrap,
                text=prompt,
                command=lambda p=prompt: on_pick(p),
                soft=True,
                padx=14,
                pady=7,
                bg=bg,
            ).pack(side=tk.LEFT, padx=(0, 8), pady=2)


class PlaceholderInput(tk.Text):
    """Multiline input with placeholder text."""

    def __init__(self, parent: tk.Misc, placeholder: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = Colors.MUTED
        self.normal_color = kwargs.get("fg", Colors.TEXT)
        self._showing_placeholder = False
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.show_placeholder()

    def show_placeholder(self) -> None:
        if self.get("1.0", tk.END).strip():
            return
        self._showing_placeholder = True
        self.configure(fg=self.placeholder_color)
        self.insert("1.0", self.placeholder)
        self.mark_set(tk.INSERT, "1.0")

    def _on_focus_in(self, _event) -> None:
        if self._showing_placeholder:
            self.delete("1.0", tk.END)
            self.configure(fg=self.normal_color)
            self._showing_placeholder = False

    def _on_focus_out(self, _event) -> None:
        if not self.get("1.0", tk.END).strip():
            self.show_placeholder()

    def get_text(self) -> str:
        if self._showing_placeholder:
            return ""
        return self.get("1.0", tk.END).strip()

    def clear(self) -> None:
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.show_placeholder()

    def set_writable(self, writable: bool) -> None:
        """Toggle editability without leaving the widget in a broken state."""
        if writable:
            self.configure(state=tk.NORMAL)
            if not self.get("1.0", tk.END).strip() and not self._showing_placeholder:
                self.show_placeholder()
        else:
            self.configure(state=tk.DISABLED)


class StatusDot(tk.Canvas):
    """Small online/offline indicator."""

    def __init__(self, parent: tk.Misc, *, color: str, size: int = 10):
        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            borderwidth=0,
            bg=Colors.BACKGROUND,
        )
        self.create_oval(1, 1, size - 1, size - 1, fill=color, outline=color)
