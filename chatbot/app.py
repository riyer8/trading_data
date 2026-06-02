"""Trading Data chatbot — professional UI with clear message roles."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import font as tkfont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

from chatbot.launcher import (
    close_all,
    close_matching,
    close_process,
    format_command,
    format_running_context,
    launch_module,
)
from chatbot.llm import AssistantReply, OpenRouterClient, ToolAction, fallback_reply
from chatbot.entities import (
    gather_conversation_context,
    gather_user_messages,
    normalize_action_args,
    resolve_entities,
    build_launch_args,
    missing_requirement,
)
from chatbot.tool_specs import module_requires_args
from chatbot.intent import enhance_reply, finalize_launch_actions
from chatbot.rag import ReadmeIndex
from chatbot.widgets import CircleButton, HorizontalScrollRow, PillButton, PlaceholderInput, PromptRow, StatusDot
from ui.theme import Colors, Fonts

CHATBOT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CHATBOT_DIR, ".env"))

EXAMPLE_PROMPTS = [
    "VWAP for AAPL",
    "Daily movers",
    "Open screeners",
]

# Bubble fills — distinct but cohesive with the trading-desk palette
USER_BUBBLE = "#1a2744"       # blue — user input
ASSISTANT_BUBBLE = "#1b3d3a"  # teal — assistant replies
SYSTEM_BUBBLE = "#2a2418"     # amber tint — system notices

ROLE_LABELS = {
    "user": "You",
    "assistant": "Assistant",
    "system": "System",
}


class ChatbotApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Trading Data Assistant")
        self.root.geometry("520x580")
        self.root.minsize(440, 480)
        self.root.configure(bg=Colors.BACKGROUND)

        self.index = ReadmeIndex()
        self.llm = OpenRouterClient()
        self.history: list[dict[str, str]] = []
        self.busy = False
        self._typing_index: str | None = None
        self._typing_frame = 0
        self._typing_job: str | None = None
        self._starters_visible = True
        self._session_entities = None

        self._configure_fonts()
        self._build_layout()
        self._show_welcome()
        self.root.after(100, self.input_box.focus_set)

    def _configure_fonts(self) -> None:
        self.font_body = tkfont.Font(family=Fonts.sans_name, size=12)
        self.font_title = tkfont.Font(family=Fonts.sans_name, size=14, weight="bold")
        self.font_subtitle = tkfont.Font(family=Fonts.sans_name, size=10)
        self.font_small = tkfont.Font(family=Fonts.sans_name, size=9)
        self.font_role = tkfont.Font(family=Fonts.sans_name, size=9, weight="bold")

    def _build_layout(self) -> None:
        outer = tk.Frame(self.root, bg=Colors.BACKGROUND, padx=12, pady=10)
        outer.pack(fill=tk.BOTH, expand=True)

        # Pin input area to the bottom first so it never gets pushed off-screen.
        self._build_compose(outer)

        self.actions_frame = tk.Frame(outer, bg=Colors.BACKGROUND)
        self.actions_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 8))

        self.starters_frame = tk.Frame(outer, bg=Colors.BACKGROUND)
        self.starters_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 8))
        self.prompt_row = PromptRow(
            self.starters_frame,
            EXAMPLE_PROMPTS,
            self._send_prompt,
            bg=Colors.BACKGROUND,
        )
        self.prompt_row.pack(fill=tk.X)

        self._build_header(outer)

        chat_shell = tk.Frame(outer, bg=Colors.PANEL, highlightthickness=1, highlightbackground=Colors.GRID)
        chat_shell.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        self.chat = scrolledtext.ScrolledText(
            chat_shell,
            wrap=tk.WORD,
            bg=Colors.PANEL,
            fg=Colors.TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=8,
            font=self.font_body,
            state=tk.DISABLED,
            spacing2=2,
            takefocus=False,
            cursor="arrow",
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self._configure_chat_tags()

    def _build_header(self, parent: tk.Frame) -> None:
        header = tk.Frame(parent, bg=Colors.BACKGROUND)
        header.pack(fill=tk.X, side=tk.TOP)

        row = tk.Frame(header, bg=Colors.BACKGROUND)
        row.pack(fill=tk.X)

        dot_color = Colors.BULL if self.llm.available else Colors.ACCENT_2
        StatusDot(row, color=dot_color).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            row,
            text="Trading Data Assistant",
            bg=Colors.BACKGROUND,
            fg=Colors.TEXT,
            font=self.font_title,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        legend = tk.Frame(row, bg=Colors.BACKGROUND)
        legend.pack(side=tk.RIGHT)
        for label, color in (
            ("You", Colors.ACCENT_4),
            ("Asst", Colors.BULL),
            ("Sys", Colors.ACCENT_5),
        ):
            item = tk.Frame(legend, bg=Colors.BACKGROUND)
            item.pack(side=tk.LEFT, padx=(8, 0))
            swatch = tk.Canvas(item, width=8, height=8, bg=Colors.BACKGROUND, highlightthickness=0)
            swatch.pack(side=tk.LEFT, padx=(0, 4))
            swatch.create_oval(1, 1, 7, 7, fill=color, outline=color)
            tk.Label(item, text=label, bg=Colors.BACKGROUND, fg=Colors.MUTED, font=self.font_small).pack(side=tk.LEFT)

        status = "Ready" if self.llm.available else "Offline"
        tk.Label(
            header,
            text=status,
            bg=Colors.BACKGROUND,
            fg=Colors.MUTED,
            font=self.font_subtitle,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(2, 0), padx=(18, 0))

    def _build_compose(self, parent: tk.Frame) -> None:
        compose = tk.Frame(parent, bg=Colors.BACKGROUND)
        compose.pack(fill=tk.X, side=tk.BOTTOM)

        dock = tk.Frame(compose, bg=Colors.HEADER, padx=2, pady=2)
        dock.pack(fill=tk.X)

        inner = tk.Frame(dock, bg=Colors.PANEL, padx=10, pady=8)
        inner.pack(fill=tk.X)

        input_row = tk.Frame(inner, bg=Colors.PANEL)
        input_row.pack(fill=tk.X)

        self.input_box = PlaceholderInput(
            input_row,
            placeholder="Type a message…",
            height=1,
            wrap=tk.WORD,
            bg=Colors.PANEL,
            fg=Colors.TEXT,
            insertbackground=Colors.ACCENT_4,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            font=self.font_body,
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.input_box.bind("<Return>", self._on_return)
        self.input_box.bind("<Button-1>", lambda _e: self.input_box.focus_set(), add="+")

        self.send_button = CircleButton(input_row, self._on_send, size=34, bg=Colors.PANEL)
        self.send_button.pack(side=tk.RIGHT, padx=(8, 0))

    def _scroll_chat_to_end(self) -> None:
        """Scroll transcript without stealing keyboard focus from other apps."""
        input_had_focus = self.root.focus_get() is self.input_box
        self.chat.yview_moveto(1.0)
        if input_had_focus:
            self.input_box.focus_set()

    def _configure_chat_tags(self) -> None:
        self.chat.tag_configure("gap", spacing3=10)

        # Role labels — color-coded, aligned with their bubble
        self.chat.tag_configure(
            "role_user",
            foreground=Colors.ACCENT_4,
            font=self.font_role,
            lmargin1=60,
            rmargin=12,
            justify=tk.RIGHT,
            spacing1=2,
        )
        self.chat.tag_configure(
            "role_assistant",
            foreground=Colors.BULL,
            font=self.font_role,
            lmargin1=12,
            rmargin=60,
            justify=tk.LEFT,
            spacing1=2,
        )
        self.chat.tag_configure(
            "role_system",
            foreground=Colors.ACCENT_5,
            font=self.font_role,
            lmargin1=12,
            rmargin=60,
            justify=tk.LEFT,
            spacing1=2,
        )

        # Message bubbles
        self.chat.tag_configure(
            "user_bubble",
            background=USER_BUBBLE,
            foreground=Colors.TEXT,
            lmargin1=56,
            lmargin2=56,
            rmargin=12,
            spacing1=8,
            spacing3=8,
        )
        self.chat.tag_configure(
            "assistant_bubble",
            background=ASSISTANT_BUBBLE,
            foreground=Colors.TEXT,
            lmargin1=12,
            lmargin2=12,
            rmargin=56,
            spacing1=8,
            spacing3=8,
        )
        self.chat.tag_configure(
            "system_bubble",
            background=SYSTEM_BUBBLE,
            foreground=Colors.TEXT,
            lmargin1=12,
            lmargin2=12,
            rmargin=56,
            spacing1=8,
            spacing3=8,
        )
        self.chat.tag_configure(
            "typing_body",
            background=ASSISTANT_BUBBLE,
            foreground=Colors.MUTED,
            lmargin1=12,
            lmargin2=12,
            rmargin=56,
            spacing1=6,
            spacing3=6,
            font=(Fonts.sans_name, 11, "italic"),
        )

    def _append_message(self, role: str, text: str) -> None:
        role_tag = f"role_{role}"
        bubble_tag = f"{role}_bubble"
        label = ROLE_LABELS[role]

        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n", "gap")
        self.chat.insert(tk.END, f"{label}\n", role_tag)
        self.chat.insert(tk.END, f"{text}\n", bubble_tag)
        self.chat.configure(state=tk.DISABLED)
        self._scroll_chat_to_end()

    def _show_welcome(self) -> None:
        self._append_message(
            "assistant",
            "Ask about tools, charts, or screeners — or tap an example below.",
        )

    def _hide_starters(self) -> None:
        if not self._starters_visible:
            return
        self._starters_visible = False
        self.starters_frame.pack_forget()

    def _send_prompt(self, prompt: str) -> None:
        if self.busy:
            return
        self._submit(prompt)

    def _on_return(self, event) -> str | None:
        if event.state & 0x0001:
            return None
        self._on_send()
        return "break"

    def _clear_actions(self) -> None:
        for child in self.actions_frame.winfo_children():
            child.destroy()

    def _render_actions(self, actions: list[ToolAction]) -> None:
        self._clear_actions()
        if not actions:
            return

        launches = [action for action in actions if action.kind == "launch"]
        closes = [action for action in actions if action.kind == "close"]

        if launches:
            header = tk.Frame(self.actions_frame, bg=Colors.BACKGROUND)
            header.pack(fill=tk.X, pady=(0, 6))
            tk.Label(
                header,
                text="Suggested tools",
                bg=Colors.BACKGROUND,
                fg=Colors.MUTED,
                font=self.font_small,
            ).pack(side=tk.LEFT)

            if len(launches) > 1:
                PillButton(
                    header,
                    text="Launch all",
                    command=lambda items=launches: self._launch_all(items),
                    accent=True,
                    padx=12,
                    pady=6,
                    bg=Colors.BACKGROUND,
                ).pack(side=tk.RIGHT)

            row = HorizontalScrollRow(self.actions_frame, bg=Colors.BACKGROUND)
            row.pack(fill=tk.X, pady=(0, 6 if closes else 0))

            for action in launches:
                PillButton(
                    row.inner,
                    text=action.label,
                    command=lambda a=action: self._run_action(a),
                    accent=True,
                    padx=14,
                    pady=7,
                    bg=Colors.BACKGROUND,
                ).pack(side=tk.LEFT, padx=(0, 8), pady=2)

        if closes:
            tk.Label(
                self.actions_frame,
                text="Close applications",
                bg=Colors.BACKGROUND,
                fg=Colors.MUTED,
                font=self.font_small,
            ).pack(anchor=tk.W, pady=(0, 6))

            row = HorizontalScrollRow(self.actions_frame, bg=Colors.BACKGROUND)
            row.pack(fill=tk.X)

            for action in closes:
                PillButton(
                    row.inner,
                    text=action.label,
                    command=lambda a=action: self._run_action(a),
                    danger=True,
                    padx=14,
                    pady=7,
                    bg=Colors.BACKGROUND,
                ).pack(side=tk.LEFT, padx=(0, 8), pady=2)

    def _launch_all(self, actions: list[ToolAction]) -> None:
        for action in actions:
            self._run_action(action)

    def _run_action(self, action: ToolAction) -> None:
        if action.kind == "close":
            threading.Thread(target=self._close_worker, args=(action,), daemon=True).start()
        else:
            threading.Thread(target=self._launch_worker, args=(action,), daemon=True).start()

    def _launch_worker(self, action: ToolAction) -> None:
        try:
            args = normalize_action_args(action.module, list(action.args))

            if module_requires_args(action.module) and not args:
                context = gather_conversation_context(self.history, "")
                user_only = gather_user_messages(self.history, "")
                entities = resolve_entities(context, self._session_entities, user_text=user_only)
                args = build_launch_args(action.module, entities)
                if not args:
                    prompt = missing_requirement(action.module, entities)
                    message = prompt or f"Missing information to launch {action.label}."
                    self.root.after(0, lambda m=message: self._append_message("assistant", m))
                    return

            result = launch_module(action.module, args)
            cmd = format_command(action.module, args)
            self.root.after(
                0,
                lambda c=cmd, pid=result.pid: self._append_message(
                    "system", f"Launched {c} (pid {pid})"
                ),
            )
        except Exception as exc:
            self.root.after(0, lambda e=exc: messagebox.showerror("Launch failed", str(e)))

    def _close_worker(self, action: ToolAction) -> None:
        try:
            if action.target == "all":
                closed = close_all()
                if closed:
                    msg = f"Closed {len(closed)} running tool(s)."
                else:
                    msg = "No running tools to close."
            elif action.pid is not None:
                if close_process(action.pid):
                    msg = f"Closed pid {action.pid}."
                else:
                    msg = f"Could not close pid {action.pid} — it may have already exited."
            elif action.module:
                closed = close_matching(action.module, action.args)
                if closed:
                    msg = f"Closed {len(closed)} matching tool(s)."
                else:
                    msg = f"No running tools matched {action.module}."
            else:
                msg = "Nothing to close — specify a running app or use close all."
            self.root.after(0, lambda: self._append_message("system", msg))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Close failed", str(exc)))

    def _show_typing(self) -> None:
        self.chat.configure(state=tk.NORMAL)
        self._typing_index = self.chat.index(tk.END)
        self._typing_frame = 0
        self.chat.insert(tk.END, "\n", "gap")
        self.chat.insert(tk.END, "Assistant\n", "role_assistant")
        self.chat.insert(tk.END, "…\n", "typing_body")
        self.chat.configure(state=tk.DISABLED)
        self._scroll_chat_to_end()
        self._animate_typing()

    def _animate_typing(self) -> None:
        if not self._typing_index or not self.busy:
            return
        dots = ["", ".", "..", "..."][self._typing_frame % 4]
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete(self._typing_index, tk.END)
        self.chat.insert(tk.END, "\n", "gap")
        self.chat.insert(tk.END, "Assistant\n", "role_assistant")
        self.chat.insert(tk.END, f"{dots}\n", "typing_body")
        self.chat.configure(state=tk.DISABLED)
        self._scroll_chat_to_end()
        self._typing_frame += 1
        self._typing_job = self.root.after(420, self._animate_typing)

    def _hide_typing(self) -> None:
        if self._typing_job:
            self.root.after_cancel(self._typing_job)
            self._typing_job = None
        if not self._typing_index:
            return
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete(self._typing_index, tk.END)
        self._typing_index = None
        self.chat.configure(state=tk.DISABLED)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.send_button.set_enabled(not busy)
        # Keep the input box writable so you can draft the next message while waiting.

    def _on_send(self, _event=None) -> None:
        if self.busy:
            return
        text = self.input_box.get_text()
        if not text:
            return
        self.input_box.clear()
        self._submit(text)

    def _submit(self, text: str) -> None:
        self._hide_starters()
        self._append_message("user", text)
        self._clear_actions()
        self._set_busy(True)
        self._show_typing()
        threading.Thread(target=self._handle_query, args=(text,), daemon=True).start()

    def _handle_query(self, user_message: str) -> None:
        try:
            retrieved = self.index.search(user_message, top_k=5)
            context = self.index.format_context(retrieved)
            running_context = format_running_context()
            if self.llm.available:
                reply = self.llm.chat(
                    user_message,
                    context,
                    self.history,
                    running_context=running_context,
                )
                user_context = gather_conversation_context(self.history, user_message)
                user_only = gather_user_messages(self.history, user_message)
                rag_modules = [item.chunk.module for item in retrieved if item.chunk.module]
                reply = enhance_reply(reply, user_message, user_context, user_only, rag_modules)
                reply = finalize_launch_actions(reply, user_context, user_only, rag_modules)
                self._session_entities = reply.entities
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": reply.message})
            else:
                labels = [item.chunk.title for item in retrieved]
                reply = fallback_reply(user_message, context, labels)
        except Exception as exc:
            reply = AssistantReply(
                message=f"An error occurred while processing your request:\n{exc}",
                actions=[],
                used_llm=False,
            )

        self.root.after(0, lambda: self._finish_query(reply))

    def _finish_query(self, reply: AssistantReply) -> None:
        self._hide_typing()
        self._append_message("assistant", reply.message)
        self._render_actions(reply.actions)
        self._set_busy(False)
        self.input_box.focus_set()


def _detach_from_terminal() -> bool:
    """Re-launch the UI detached so the shell stays free for other commands."""
    if os.environ.get("CHATBOT_DETACHED") == "1":
        return False
    if not sys.stdin.isatty():
        return False

    env = os.environ.copy()
    env["CHATBOT_DETACHED"] = "1"
    subprocess.Popen(
        [sys.executable, "-m", "chatbot"],
        cwd=PROJECT_ROOT,
        env=env,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    print("Trading Data Assistant opened.")
    return True


def main() -> None:
    if _detach_from_terminal():
        return
    root = tk.Tk()
    ChatbotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
