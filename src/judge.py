"""Candidate selection via internal judge."""

from __future__ import annotations

import json

from src import config, llm


def _judge_style(
    fact_sheet: dict,
    style: str,
    candidates: list[str],
) -> str:
    if not candidates:
        return ""
    if len(candidates) == 1:
        return candidates[0]

    definition = config.STYLE_DEFINITIONS.get(style, style)
    numbered = "\n".join(f"{i}. {c}" for i, c in enumerate(candidates))
    system = llm.load_prompt("judge.txt")
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"STYLE: {style}\n"
        f"DEFINITION: {definition}\n\n"
        f"CANDIDATES:\n{numbered}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        result = llm.chat(
            messages,
            json_mode=True,
            temperature=0.0,
            max_tokens=800,
            stage=f"judge-{style}",
        )
        if isinstance(result, dict) and "best" in result:
            idx = int(result["best"])
            if 0 <= idx < len(candidates):
                return candidates[idx]
    except Exception:
        pass
    return candidates[0]


def pick_best(
    fact_sheet: dict,
    candidates: dict[str, list[str]],
    styles: list[str],
) -> dict[str, str]:
    """Pick the best caption per style; fall back to candidate 0 on failure."""
    out: dict[str, str] = {}
    for style in styles:
        cands = candidates.get(style, [])
        out[style] = _judge_style(fact_sheet, style, cands)
    return out
