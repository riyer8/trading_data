"""Shared chart heading and pointer interaction.

Scroll zooms around the cursor, drag pans, double-click resets.
A crosshair snaps to the nearest bar and a readout describes it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ui.theme import Colors, Fonts


def as_datetimes(index) -> pd.DatetimeIndex:
    dates = pd.DatetimeIndex(index)
    if dates.tz is not None:
        dates = dates.tz_localize(None)
    return dates


def place_heading(fig, title: str, note: str, *, hint: str | None = None, title_color: str | None = None) -> None:
    """Title, one-line explanation, and an optional control hint in the margins."""
    fig.suptitle(
        title,
        x=0.055,
        y=0.975,
        ha="left",
        va="top",
        fontsize=Fonts.TITLE,
        fontweight="bold",
        color=title_color or Colors.TEXT,
    )
    fig.text(
        0.055,
        0.935,
        note,
        ha="left",
        va="top",
        color=Colors.MUTED,
        fontsize=Fonts.TICK,
    )
    if hint:
        fig.text(
            0.985,
            0.012,
            hint,
            ha="right",
            va="bottom",
            color=Colors.MUTED,
            fontsize=Fonts.TICK,
        )
    fig.subplots_adjust(left=0.07, right=0.97, top=0.86, bottom=0.10)


def format_price(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    number = float(value)
    if abs(number) >= 1000:
        return f"${number:,.0f}"
    return f"${number:,.2f}"


def format_volume(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    number = float(value)
    magnitude = abs(number)
    if magnitude >= 1e9:
        return f"{number / 1e9:.2f}B"
    if magnitude >= 1e6:
        return f"{number / 1e6:.2f}M"
    if magnitude >= 1e3:
        return f"{number / 1e3:.1f}K"
    return f"{number:.0f}"


class ChartNavigator:
    """Zoom, pan, and a snapped readout for charts that share one x index."""

    HINT = "Scroll to zoom   ·   drag to pan   ·   double-click to reset"

    def __init__(self, fig, axes, dates, y_series: dict, describe):
        self.fig = fig
        self.axes = list(axes)
        self.dates = as_datetimes(dates)
        self.n = len(self.dates)
        self.y_series = y_series
        self.describe = describe
        self.full = (-0.65, max(self.n - 0.35, 0.65))
        self.min_width = float(min(10, max(self.n, 1)))
        self._press = None
        self._dragging = False
        self._background = None
        self._index = None
        self._painting = False

        self.vlines = [
            ax.axvline(0, color=Colors.MUTED, linewidth=0.7, alpha=0.85, animated=True, visible=False)
            for ax in self.axes
        ]
        self.hlines = {
            ax: ax.axhline(0, color=Colors.MUTED, linewidth=0.7, alpha=0.55, animated=True, visible=False)
            for ax in self.axes
        }
        self.readout = self.axes[0].text(
            0.012,
            0.98,
            "",
            transform=self.axes[0].transAxes,
            va="top",
            ha="left",
            animated=True,
            fontsize=Fonts.TICK,
            fontfamily="monospace",
            color=Colors.TEXT,
            linespacing=1.35,
            zorder=6,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=Colors.HEADER, edgecolor=Colors.GRID, alpha=0.94),
        )
        self._format_x_axis()
        for ax in self.axes[:-1]:
            ax.tick_params(labelbottom=False)

    def attach(self) -> ChartNavigator:
        canvas = self.fig.canvas
        canvas.mpl_connect("scroll_event", self._on_scroll)
        canvas.mpl_connect("button_press_event", self._on_press)
        canvas.mpl_connect("button_release_event", self._on_release)
        canvas.mpl_connect("motion_notify_event", self._on_motion)
        canvas.mpl_connect("axes_leave_event", self._on_leave)
        canvas.mpl_connect("draw_event", self._on_draw)
        self.reset()
        return self

    def reset(self) -> None:
        self._set_xlim(*self.full)

    def _format_x_axis(self) -> None:
        import matplotlib.pyplot as plt

        def _fmt(value, _pos):
            index = int(round(value))
            if index < 0 or index >= self.n:
                return ""
            stamp = self.dates[index]
            left, right = self.axes[0].get_xlim()
            if right - left > 420:
                return stamp.strftime("%b '%y")
            return stamp.strftime("%b %d")

        axis = self.axes[-1]
        axis.xaxis.set_major_formatter(plt.FuncFormatter(_fmt))
        axis.xaxis.set_major_locator(plt.MaxNLocator(8, integer=True, min_n_ticks=4))

    def _view_bounds(self) -> tuple[int, int]:
        left, right = self.axes[0].get_xlim()
        start = max(0, int(np.floor(left)))
        stop = min(self.n - 1, int(np.ceil(right)))
        if stop < start:
            stop = start
        return start, stop

    def _autoscale_y(self) -> None:
        start, stop = self._view_bounds()
        sl = slice(start, stop + 1)
        for ax in self.axes:
            spec = self.y_series.get(ax)
            if not spec:
                continue
            if spec.get("lock") is not None:
                ax.set_ylim(*spec["lock"])
                continue
            chunks = []
            for series in spec.get("arrays", ()):
                values = np.asarray(series, dtype=float)[sl]
                values = values[np.isfinite(values)]
                if len(values):
                    chunks.append(values)
            if not chunks:
                continue
            merged = np.concatenate(chunks)
            low = float(np.min(merged))
            high = float(np.max(merged))
            if spec.get("floor") is not None:
                low = min(low, float(spec["floor"]))
            span = high - low
            pad = span * 0.08 if span else max(abs(high) * 0.04, 1.0)
            ax.set_ylim(low - pad, high + pad)

    def _set_xlim(self, left: float, right: float) -> None:
        width = right - left
        full_left, full_right = self.full
        full_width = full_right - full_left
        width = min(max(width, self.min_width), full_width)
        if abs((right - left) - width) > 1e-6:
            mid = (left + right) / 2
            left, right = mid - width / 2, mid + width / 2
        if left < full_left:
            right += full_left - left
            left = full_left
        if right > full_right:
            left -= right - full_right
            right = full_right
        left = max(left, full_left)
        right = min(right, full_right)
        for ax in self.axes:
            ax.set_xlim(left, right)
        self._autoscale_y()
        self.fig.canvas.draw_idle()

    def _on_scroll(self, event) -> None:
        if event.inaxes not in self.axes or event.xdata is None or self._dragging:
            return
        step = event.step if event.step else (1 if event.button == "up" else -1)
        left, right = self.axes[0].get_xlim()
        scale = 0.82 ** step
        self._set_xlim(
            event.xdata - (event.xdata - left) * scale,
            event.xdata + (right - event.xdata) * scale,
        )

    def _on_press(self, event) -> None:
        if getattr(event, "dblclick", False):
            self._press = None
            self._dragging = False
            self.reset()
            return
        if event.button != 1 or event.inaxes not in self.axes or event.x is None:
            return
        self._press = (event.x, self.axes[0].get_xlim())
        self._dragging = False

    def _on_release(self, _event) -> None:
        self._press = None
        self._dragging = False

    def _on_motion(self, event) -> None:
        if self._press is not None and event.x is not None:
            origin_x, (left, right) = self._press
            if not self._dragging and abs(event.x - origin_x) < 4:
                self._hover(event)
                return
            self._dragging = True
            transform = self.axes[0].transData.inverted()
            x_now = transform.transform((event.x, 0))[0]
            x_then = transform.transform((origin_x, 0))[0]
            self._set_xlim(left + (x_then - x_now), right + (x_then - x_now))
            return
        self._hover(event)

    def _on_leave(self, _event) -> None:
        if self._dragging:
            return
        self._index = None
        self._paint_overlay()

    def _hover(self, event) -> None:
        if event.inaxes not in self.axes or event.xdata is None:
            self._index = None
        else:
            self._index = int(np.clip(round(event.xdata), 0, self.n - 1))
        self._hover_axes = event.inaxes
        self._hover_y = event.ydata
        self._paint_overlay()

    def _on_draw(self, _event) -> None:
        if self._painting:
            return
        self._background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self._paint_overlay()

    def _paint_overlay(self) -> None:
        if self._background is None or self._painting:
            return
        self._painting = True
        try:
            canvas = self.fig.canvas
            canvas.restore_region(self._background)
            index = self.n - 1 if self._index is None else self._index
            self.readout.set_text(self.describe(index) if self.n else "")
            show_hair = self._index is not None
            for line in self.vlines:
                line.set_visible(show_hair)
                if show_hair:
                    line.set_xdata([self._index, self._index])
            hovered = getattr(self, "_hover_axes", None)
            for ax, line in self.hlines.items():
                active = show_hair and ax is hovered and getattr(self, "_hover_y", None) is not None
                line.set_visible(active)
                if active:
                    line.set_ydata([self._hover_y, self._hover_y])
            for artist in (*self.vlines, *self.hlines.values(), self.readout):
                self.fig.draw_artist(artist)
            canvas.blit(self.fig.bbox)
        finally:
            self._painting = False
