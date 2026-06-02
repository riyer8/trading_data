"""Post-process LLM replies: correct tools, args, and support multi-launch."""

from __future__ import annotations

from chatbot.entities import (
    ExtractedEntities,
    build_launch_args,
    gather_user_messages,
    infer_modules_from_context,
    missing_requirement,
    module_label,
    normalize_action_args,
    resolve_entities,
)
from chatbot.llm import AssistantReply, ToolAction


def _action_label(module: str, args: list[str]) -> str:
    if module == "charts.stockChart" and len(args) >= 2:
        return f"Stock chart — {args[0]} ({args[1]} mo)"
    if module == "charts.vwap" and args:
        return f"VWAP for {args[0]}"
    if module == "charts.rsi_trend" and args:
        return f"RSI for {args[0]}"
    if module == "charts.ema" and args:
        return f"EMA for {args[0]}"
    short = module_label(module)
    return f"{short} — {' '.join(args)}" if args else short


def _pick_modules(context_text: str, rag_modules: list[str], limit: int = 6) -> list[str]:
    return infer_modules_from_context(context_text, rag_modules)[:limit]


def _correct_launch_action(
    action: ToolAction,
    context_text: str,
    user_text: str,
    rag_modules: list[str],
    entities: ExtractedEntities,
) -> ToolAction | None:
    """Align module/args with conversation intent and required CLI shape."""
    inferred = _pick_modules(context_text, rag_modules)
    module = action.module

    if inferred:
        if module not in inferred:
            module = inferred[0]

    per_action = resolve_entities(context_text, entities, action.args, user_text=user_text)
    missing = missing_requirement(module, per_action)
    if missing:
        return None

    args = build_launch_args(module, per_action)
    if not args:
        args = normalize_action_args(module, action.args)
    else:
        args = normalize_action_args(module, args)

    if module in {"charts.stockChart", "launchers.openSingleTickerApp"} and len(args) < 2:
        return None

    action.module = module
    action.args = args
    action.label = _action_label(module, args)
    return action


def enhance_reply(
    reply: AssistantReply,
    user_message: str,
    context_text: str,
    user_text: str,
    rag_modules: list[str],
) -> AssistantReply:
    merged = resolve_entities(context_text, reply.entities, user_text=user_text)
    reply.entities = merged

    launch_actions = [action for action in reply.actions if action.kind == "launch"]
    if launch_actions:
        return reply

    modules = _pick_modules(context_text, rag_modules)
    if not modules:
        return reply

    added = 0
    for module in modules:
        missing = missing_requirement(module, merged)
        if missing:
            if added == 0 and not reply.message.strip():
                reply.message = missing
            continue

        args = build_launch_args(module, merged)
        if module in {"charts.stockChart", "launchers.openSingleTickerApp"} and not args:
            continue
        if module not in {"charts.stockChart", "launchers.openSingleTickerApp"} and not args and TOOL_NEEDS_TICKER(module):
            continue

        reply.actions.append(
            ToolAction(
                label=_action_label(module, args),
                kind="launch",
                module=module,
                args=args,
            )
        )
        added += 1

    if added and any(
        phrase in reply.message.lower()
        for phrase in ("provide the ticker", "which ticker", "lookback", "how many months")
    ):
        names = ", ".join(action.label for action in reply.actions if action.kind == "launch")
        reply.message = f"I'll open {names}."

    return reply


def finalize_launch_actions(
    reply: AssistantReply,
    context_text: str,
    user_text: str,
    rag_modules: list[str] | None = None,
) -> AssistantReply:
    rag_modules = rag_modules or []
    merged = resolve_entities(context_text, reply.entities, user_text=user_text)
    reply.entities = merged

    kept: list[ToolAction] = []
    prompts: list[str] = []

    for action in reply.actions:
        if action.kind == "close":
            kept.append(action)
            continue

        corrected = _correct_launch_action(action, context_text, user_text, rag_modules, merged)
        if corrected is None:
            missing = missing_requirement(action.module, merged)
            if missing and missing not in prompts:
                prompts.append(missing)
            continue
        kept.append(corrected)

    if prompts and not kept:
        reply.message = prompts[0] if len(prompts) == 1 else "\n".join(prompts)
    elif prompts:
        reply.message = f"{reply.message}\n\n{prompts[0]}"

    reply.actions = kept
    return reply


def TOOL_NEEDS_TICKER(module: str) -> bool:
    from chatbot.tool_specs import TOOL_SPECS

    spec = TOOL_SPECS.get(module)
    return bool(spec and spec.min_tickers)
