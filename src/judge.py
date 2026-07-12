"""Candidate selection via internal judge (batched per clip)."""

from __future__ import annotations

import json

from src import config, llm


def pick_best(
    fact_sheet: dict,
    candidates: dict[str, list[str]],
    styles: list[str],
) -> dict[str, str]:
    """Pick the best caption per style; skip judge when only one candidate."""
    out: dict[str, str] = {}
    needs_judge: dict[str, list[str]] = {}

    for style in styles:
        cands = candidates.get(style, [])
        if len(cands) <= 1:
            out[style] = cands[0] if cands else ""
        else:
            needs_judge[style] = cands

    if not needs_judge:
        return out

    numbered_blocks = []
    for style, cands in needs_judge.items():
        definition = config.STYLE_DEFINITIONS.get(style, style)
        lines = "\n".join(f"  {i}. {c}" for i, c in enumerate(cands))
        numbered_blocks.append(f"STYLE: {style}\nDEFINITION: {definition}\nCANDIDATES:\n{lines}")

    system = llm.load_prompt("judge.txt") + (
        "\n\nWhen multiple STYLE blocks are provided, return JSON:"
        '\n{"results":{"formal":{"best":0,"scores":[...]}, ...}}'
        " with one entry per style."
    )
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        + "\n\n".join(numbered_blocks)
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
            max_tokens=1200,
            stage="judge-batch",
        )
        if isinstance(result, dict):
            batch = result.get("results", result)
            for style, cands in needs_judge.items():
                entry = batch.get(style, {})
                if isinstance(entry, dict) and "best" in entry:
                    idx = int(entry["best"])
                    if 0 <= idx < len(cands):
                        out[style] = cands[idx]
                        continue
                out[style] = cands[0]
            return out
    except Exception:
        pass

    for style, cands in needs_judge.items():
        out[style] = cands[0]
    return out
