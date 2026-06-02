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
        danger: bool = False,
        font: tkfont.Font | None = None,
        padx: int = 16,
        pady: int = 8,
        bg: str = Colors.BACKGROUND,
    ):
        self._command = command
        self._text = text
        if danger:
            self._fill = Colors.BEAR_FILL
            self._hover = _lighten(Colors.BEAR_FILL, 0.18)
            self._fg = Colors.BEAR
        elif accent:
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


class HorizontalScrollRow(tk.Frame):
    """Horizontally scrollable row for pill buttons that overflow the window."""

    def __init__(self, parent: tk.Misc, *, bg: str = Colors.BACKGROUND, height: int = 44):
        super().__init__(parent, bg=bg)
        self._bg = bg

        self.canvas = tk.Canvas(
            self,
            height=height,
            bg=bg,
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.canvas.configure(xscrollcommand=scrollbar.set)

        self.canvas.pack(fill=tk.X, expand=True)
        scrollbar.pack(fill=tk.X)

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_inner_configure(self, _event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, _event) -> None:
        self.canvas.bind("<Shift-MouseWheel>", self._scroll_x)

    def _unbind_mousewheel(self, _event) -> None:
        self.canvas.unbind("<Shift-MouseWheel>")

    def _scroll_x(self, event) -> None:
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        self.canvas.xview_scroll(int(-delta / 120), "units")


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
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<Button-1>", self._on_click, add="+")
        self.show_placeholder()

    def _has_focus(self) -> bool:
        return self.focus_get() is self

    def _clear_placeholder(self) -> None:
        if not self._showing_placeholder:
            return
        self.delete("1.0", tk.END)
        self.configure(fg=self.normal_color)
        self._showing_placeholder = False

    def show_placeholder(self) -> None:
        if self.get("1.0", tk.END).strip():
            return
        if self._has_focus():
            # Keep the box empty while focused so the next keystroke is not appended
            # to placeholder text (FocusIn does not re-fire if focus never left).
            self._clear_placeholder()
            return
        self._showing_placeholder = True
        self.configure(fg=self.placeholder_color)
        self.delete("1.0", tk.END)
        self.insert("1.0", self.placeholder)
        self.mark_set(tk.INSERT, "1.0")

    def _on_focus_in(self, _event) -> None:
        self._clear_placeholder()

    def _on_focus_out(self, _event) -> None:
        if not self.get("1.0", tk.END).strip():
            self.show_placeholder()

    def _on_key_press(self, _event) -> None:
        if self._showing_placeholder:
            self._clear_placeholder()

    def _on_click(self, _event) -> None:
        self.after_idle(self._clear_placeholder)

    def get_text(self) -> str:
        if self._showing_placeholder:
            return ""
        return self.get("1.0", tk.END).strip()

    def clear(self) -> None:
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self._showing_placeholder = False
        self.configure(fg=self.normal_color)
        if not self._has_focus():
            self.show_placeholder()

    def set_writable(self, writable: bool) -> None:
        """Toggle editability without leaving the widget in a broken state."""
        if writable:
            self.configure(state=tk.NORMAL)
            if not self.get("1.0", tk.END).strip() and not self._has_focus():
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
