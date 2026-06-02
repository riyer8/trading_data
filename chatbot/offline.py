"""Local fallback when OpenRouter is unavailable."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from chatbot.entities import (
    ExtractedEntities,
    gather_conversation_context,
    gather_user_messages,
    module_label,
    resolve_entities,
)
from chatbot.intent import enhance_reply, finalize_launch_actions
from chatbot.llm import AssistantReply, ToolAction
from chatbot.rag import RetrievedChunk

ENV_HINT = "Add OPENROUTER_API_KEY to chatbot/.env for full AI answers."

REASON_COPY = {
    "missing_key": "Running offline — no API key configured.",
    "auth_failed": "OpenRouter rejected the API key.",
    "rate_limited": "OpenRouter rate limit reached.",
    "network": "Could not reach OpenRouter.",
    "server": "OpenRouter is temporarily unavailable.",
    "unknown": "The AI assistant is unavailable right now.",
}

SYSTEM_NOTICES = {
    "auth_failed": "OpenRouter rejected the API key — switched to local tool matching.",
    "rate_limited": "OpenRouter rate limit hit — using local tool matching for now.",
    "network": "Network error — using local tool matching for now.",
    "server": "OpenRouter is unavailable — using local tool matching for now.",
    "unknown": "AI unavailable — using local tool matching for now.",
}


@dataclass
class OfflineContext:
    reason: str = "missing_key"
    detail: str = ""


def classify_api_error(exc: Exception) -> OfflineContext:
    if isinstance(exc, requests.HTTPError):
        resp = exc.response
        if resp is not None:
            code = resp.status_code
            if code in (401, 403):
                return OfflineContext("auth_failed")
            if code == 429:
                return OfflineContext("rate_limited")
            if code >= 500:
                return OfflineContext("server")
        return OfflineContext("unknown", str(exc))
    if isinstance(exc, requests.Timeout):
        return OfflineContext("network", "Request timed out")
    if isinstance(exc, requests.ConnectionError):
        return OfflineContext("network")
    if isinstance(exc, requests.RequestException):
        return OfflineContext("network", str(exc))

    msg = str(exc)
    if "OPENROUTER_API_KEY" in msg:
        return OfflineContext("missing_key", msg)
    return OfflineContext("unknown", msg)


def system_notice(ctx: OfflineContext) -> str:
    return SYSTEM_NOTICES.get(ctx.reason, SYSTEM_NOTICES["unknown"])


def _format_tool_hints(retrieved: list[RetrievedChunk], limit: int = 3) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for item in retrieved:
        module = item.chunk.module
        if not module or module in seen:
            continue
        seen.add(module)
        lines.append(f"· {module_label(module)} — {item.chunk.title}")
        if len(lines) >= limit:
            break
    return lines


def _resume_hint(ctx: OfflineContext) -> str:
    if ctx.reason in ("missing_key", "auth_failed"):
        return ENV_HINT
    return "Full AI answers will resume when OpenRouter is available again."


def _compose_message(
    prompt: str,
    actions: list[ToolAction],
    retrieved: list[RetrievedChunk],
    ctx: OfflineContext,
) -> str:
    launches = [action for action in actions if action.kind == "launch"]
    closes = [action for action in actions if action.kind == "close"]
    prompt = prompt.strip()

    if prompt and not launches and not closes:
        return f"{prompt}\n\n{_resume_hint(ctx)}"

    parts: list[str] = []

    if launches or closes:
        if len(launches) == 1:
            parts.append(f"I matched {launches[0].label} from the README.")
        elif len(launches) > 1:
            parts.append(f"I found {len(launches)} matching tools — pick one below.")
        elif closes:
            parts.append("I can close the matching tools locally.")

        parts.append("")
        parts.append(_resume_hint(ctx))
        return "\n".join(parts)

    parts.append(REASON_COPY.get(ctx.reason, REASON_COPY["unknown"]))
    hints = _format_tool_hints(retrieved)
    if hints:
        parts.append("")
        parts.append("These README tools look relevant:")
        parts.extend(hints)
    else:
        parts.append("")
        parts.append('Try something like "VWAP for AAPL", "daily movers", or "close all".')

    parts.append("")
    parts.append(_resume_hint(ctx))
    return "\n".join(parts)


def offline_reply(
    user_message: str,
    history: list[dict[str, str]],
    retrieved: list[RetrievedChunk],
    *,
    reason: str = "missing_key",
    detail: str = "",
) -> AssistantReply:
    ctx = OfflineContext(reason=reason, detail=detail)
    user_context = gather_conversation_context(history, user_message)
    user_only = gather_user_messages(history, user_message)
    rag_modules = [item.chunk.module for item in retrieved if item.chunk.module]

    entities = resolve_entities(user_context, ExtractedEntities(), user_text=user_only)
    reply = AssistantReply(message="", actions=[], entities=entities, used_llm=False)
    reply = enhance_reply(reply, user_message, user_context, user_only, rag_modules)
    reply = finalize_launch_actions(reply, user_context, user_only, rag_modules)

    prompt = reply.message
    reply.message = _compose_message(prompt, reply.actions, retrieved, ctx)
    return reply
