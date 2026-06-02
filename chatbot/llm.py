"""OpenRouter client for structured assistant responses."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = """You are the assistant for a Python stock-market toolkit called Trading Data Tools.

Be professional, clear, and concise. Help users navigate the repository confidently.

You help users:
1. Identify which script or tool fits their goal.
2. Explain how tools work using the README context below.
3. Answer relevant trading-data questions when possible.

Use ONLY the README context for facts about this repository.
When the user wants to open, chart, or screen something, recommend concrete tools.
When a ticker symbol is implied or stated, include it in launch actions.

Respond with a single JSON object (no markdown fences):
{
  "message": "clear, professional reply",
  "actions": [
    {
      "label": "short button label, e.g. 'VWAP for AAPL'",
      "module": "charts.vwap",
      "args": ["AAPL"],
      "reason": "why this tool fits"
    }
  ]
}

Rules for actions:
- "module" must be a runnable module such as "screeners.dailyMovers" or "charts.vwap".
- "args" is a list of CLI arguments (strings). Use [] when none are needed.
- Include 0-3 actions. Prefer the most relevant launches only.
- For broad dashboard requests, suggest "launchers.openAllTickerApps".
- For single-ticker chart bundles, suggest "launchers.openSingleTickerApp" with args like ["AAPL", "6"].
- Do not invent tools that are not in the README context.
"""


@dataclass
class LaunchAction:
    label: str
    module: str
    args: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class AssistantReply:
    message: str
    actions: list[LaunchAction] = field(default_factory=list)
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

    def chat(self, user_message: str, readme_context: str, history: list[dict[str, str]] | None = None) -> AssistantReply:
        if not self.available:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add it to chatbot/.env or your environment."
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nREADME CONTEXT:\n{readme_context}"},
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
    actions: list[LaunchAction] = []
    for item in payload.get("actions", []) or []:
        if not isinstance(item, dict):
            continue
        module = str(item.get("module", "")).strip()
        if not module:
            continue
        label = str(item.get("label", module)).strip() or module
        args = [str(arg) for arg in (item.get("args") or [])]
        reason = str(item.get("reason", "")).strip()
        actions.append(LaunchAction(label=label, module=module, args=args, reason=reason))
    return AssistantReply(message=message, actions=actions, used_llm=True)


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
