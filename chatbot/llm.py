"""OpenRouter client for structured assistant responses."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from chatbot.entities import ExtractedEntities

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = """You are the assistant for a Python stock-market toolkit called Trading Data Tools.

Be professional, clear, and concise. Help users navigate the repository confidently.

You help users:
1. Identify which script or tool fits their goal.
2. Explain how tools work using the README context below.
3. Launch or close applications when asked.
4. Answer relevant trading-data questions when possible.

Use ONLY the README context for facts about this repository.

CRITICAL — understanding user intent:
- Users write casually with typos ("i can to see the vwap to hpe" → VWAP for HPE).
- Treat "vwap for hpe", "vwap to hpe", "show hpe vwap", etc. as the same intent.
- **Stock chart / candlestick** → `charts.stockChart` (NOT `charts.vwap`). VWAP is only when the user says VWAP.
- Short follow-ups like "5" or "6 months" complete the previous question (lookback, ticker, etc.) — read recent chat history.
- Extract ticker symbols from meaning, not perfect grammar. Fix obvious typos (APPL → AAPL).
- Populate the "entities" object from the full conversation. Do NOT default to AAPL/MSFT/NVDA unless the user said them.
- If entities contain the required ticker (and lookback when needed), include launch actions — do NOT ask again.
- When the user wants **multiple tools** (e.g. "vwap and rsi for AAPL", "open stock chart and vwap"), return **one launch action per tool** (up to 6).
- Only ask for missing info when the ticker or lookback truly cannot be inferred from the conversation.

Always include an "entities" object in your JSON:
{
  "message": "clear, professional reply",
  "entities": {
    "tickers": ["HPE"],
    "lookback_months": null
  },
  "actions": [ ... ]
}

CRITICAL — required information before launching:
- NEVER invent tickers the user did not mean.
- NEVER invent lookback months.
- If a ticker or lookback is still genuinely unknown, ask in "message", leave entities empty/null, and return NO launch actions.
- Examples in the README are not the user's request.

Closing applications:
- When the user asks to close, quit, stop, or kill an app/window/tool, use close actions.
- Use the RUNNING APPLICATIONS list below. If none are running, say so.
- Close actions may target a specific pid, all running tools, or tools matching a module.

Respond with a single JSON object (no markdown fences):
{
  "message": "clear, professional reply",
  "entities": {
    "tickers": ["HPE"],
    "lookback_months": 6
  },
  "actions": [
    {
      "kind": "launch",
      "label": "VWAP for AAPL",
      "module": "charts.vwap",
      "args": ["AAPL"],
      "reason": "why this tool fits"
    },
    {
      "kind": "close",
      "label": "Close VWAP for AAPL",
      "pid": 12345,
      "reason": "user asked to close this chart"
    },
    {
      "kind": "close",
      "label": "Close all running tools",
      "target": "all",
      "reason": "user asked to close everything"
    },
    {
      "kind": "close",
      "label": "Close AAPL charts",
      "module": "charts.vwap",
      "args": ["AAPL"],
      "reason": "close matching module/args"
    }
  ]
}

Launch action rules:
- "kind" must be "launch".
- "module" must be a runnable module such as "screeners.dailyMovers" or "charts.stockChart".
- Stock chart / candlestick → `charts.stockChart` with args ["TICKER", "LOOKBACK_MONTHS"].
- VWAP → `charts.vwap` with args ["TICKER"] only.
- "args" is a list of CLI argument strings. Use [] when none are needed.
- Include 0-6 actions total (launch + close combined). Use multiple launch actions when the user wants multiple tools.

Close action rules:
- "kind" must be "close".
- Use "pid" to close one running process from RUNNING APPLICATIONS, OR
- "target": "all" to close everything running, OR
- "module" (+ optional "args") to close matching launches.

Do not invent tools that are not in the README context.
"""


@dataclass
class ToolAction:
    label: str
    kind: str = "launch"  # launch | close
    module: str = ""
    args: list[str] = field(default_factory=list)
    pid: int | None = None
    target: str = ""
    reason: str = ""


# Backwards-compatible alias
LaunchAction = ToolAction


@dataclass
class AssistantReply:
    message: str
    actions: list[ToolAction] = field(default_factory=list)
    entities: ExtractedEntities = field(default_factory=ExtractedEntities)
    model: str = ""
    used_llm: bool = True


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        site_url: str = "https://github.com/trading_data",
        app_name: str = "Trading Data Chatbot",
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip()
        self.site_url = site_url
        self.app_name = app_name

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        user_message: str,
        readme_context: str,
        history: list[dict[str, str]] | None = None,
        running_context: str = "",
    ) -> AssistantReply:
        if not self.available:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add it to chatbot/.env or your environment."
            )

        system_content = f"{SYSTEM_PROMPT}\n\nREADME CONTEXT:\n{readme_context}"
        if running_context:
            system_content += f"\n\n{running_context}"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content},
        ]
        if history:
            messages.extend(history[-8:])
        messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _parse_reply_json(content)
        parsed.model = self.model
        return parsed


def _parse_reply_json(content: str) -> AssistantReply:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return AssistantReply(message=content.strip(), used_llm=True)
        payload = json.loads(match.group(0))

    message = str(payload.get("message", "")).strip() or "I couldn't generate a response."

    entities_raw = payload.get("entities") or {}
    tickers: list[str] = []
    if isinstance(entities_raw, dict):
        for item in entities_raw.get("tickers") or []:
            symbol = str(item).strip().upper()
            if symbol:
                tickers.append(symbol)
        lookback_raw = entities_raw.get("lookback_months")
        lookback = (
            int(lookback_raw)
            if lookback_raw is not None and str(lookback_raw).strip().isdigit()
            else None
        )
    else:
        lookback = None
    entities = ExtractedEntities(tickers=tickers, lookback_months=lookback)

    actions: list[ToolAction] = []
    for item in payload.get("actions", []) or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind", "launch")).strip().lower()
        label = str(item.get("label", "")).strip()
        reason = str(item.get("reason", "")).strip()

        if kind == "close":
            pid_raw = item.get("pid")
            pid = int(pid_raw) if pid_raw is not None and str(pid_raw).strip().isdigit() else None
            target = str(item.get("target", "")).strip().lower()
            module = str(item.get("module", "")).strip()
            args = [str(arg) for arg in (item.get("args") or [])]
            if not label:
                if pid is not None:
                    label = f"Close pid {pid}"
                elif target == "all":
                    label = "Close all running tools"
                elif module:
                    label = f"Close {module}"
                else:
                    continue
            actions.append(
                ToolAction(
                    label=label,
                    kind="close",
                    module=module,
                    args=args,
                    pid=pid,
                    target=target,
                    reason=reason,
                )
            )
            continue

        module = str(item.get("module", "")).strip()
        if not module:
            continue
        if not label:
            label = module
        args = [str(arg) for arg in (item.get("args") or [])]
        actions.append(
            ToolAction(label=label, kind="launch", module=module, args=args, reason=reason)
        )
    return AssistantReply(message=message, actions=actions, entities=entities, used_llm=True)


def fallback_reply(user_message: str, readme_context: str, retrieved_labels: list[str]) -> AssistantReply:
    """RAG-only response when no API key is configured."""
    lines = [
        "The assistant is running in offline mode without an API key.",
        "Add OPENROUTER_API_KEY to chatbot/.env for full responses.",
        "",
    ]
    if retrieved_labels:
        lines.append("Based on the README, these tools may be relevant:")
        lines.extend(f"· {label}" for label in retrieved_labels[:4])
    else:
        lines.append("Try asking about a specific chart, screener, or ticker symbol.")
    return AssistantReply(message="\n".join(lines), actions=[], used_llm=False)
