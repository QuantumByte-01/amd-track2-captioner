"""Fact sheet → styled caption candidates via text model."""

from __future__ import annotations

import json
import re

from src import config, llm

_WORD_RE = re.compile(r"\S+")
_META_RE = re.compile(
    r"\b(this (video|clip|footage|caption|image|frame)|the video shows|"
    r"in this scene|as an ai)\b",
    re.IGNORECASE,
)


def _truncate_caption(text: str, style: str) -> str:
    text = text.strip().strip('"').strip("'")
    text = _META_RE.sub("", text).strip()
    limit = 25 if style.startswith("humorous") else config.MAX_CAPTION_WORDS
    words = _WORD_RE.findall(text)
    if len(words) <= limit:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    count = 0
    for sent in sentences:
        sent_words = _WORD_RE.findall(sent)
        if count + len(sent_words) > limit:
            break
        out.append(sent)
        count += len(sent_words)
    if out:
        return " ".join(out).strip()
    return " ".join(words[:limit])


def _post_process(candidates: dict[str, list[str]], styles: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for style in styles:
        raw = candidates.get(style, [])
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            raw = [str(raw)] if raw else []
        cleaned = [_truncate_caption(c, style) for c in raw if c and str(c).strip()]
        out[style] = cleaned
    return out


def _write_batch(fact_sheet: dict, styles: list[str], k: int) -> dict[str, list[str]]:
    system = llm.load_prompt("write.txt")
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"REQUESTED STYLES: {json.dumps(styles)}\n"
        f"CANDIDATES PER STYLE: {k}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        result = llm.chat(
            messages,
            model=config.MODEL_CAPTION,
            json_mode=True,
            temperature=0.6,
            max_tokens=1800,
            stage="write-batch",
        )
        if isinstance(result, dict):
            return _post_process(result, styles)
    except Exception:
        pass
    result = llm.chat(
        messages,
        model=config.MODEL_CAPTION,
        json_mode=False,
        temperature=0.4,
        max_tokens=1800,
        stage="write-batch-text",
    )
    if isinstance(result, str):
        parsed = json.loads(llm._extract_json_object(result))
        if isinstance(parsed, dict):
            return _post_process(parsed, styles)
    raise ValueError("batch write failed")


def _write_one_style(fact_sheet: dict, style: str) -> str:
    system = llm.load_prompt("write.txt")
    definition = config.STYLE_DEFINITIONS[style]
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"Write exactly ONE caption for style '{style}' ({definition}).\n"
        'Return JSON only: {"caption": "..."}'
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    result = llm.chat(
        messages,
        model=config.MODEL_CAPTION,
        json_mode=True,
        temperature=0.7 if style.startswith("humorous") else 0.4,
        max_tokens=400,
        stage=f"write-{style}",
    )
    if isinstance(result, dict):
        cap = result.get("caption") or result.get(style)
        if isinstance(cap, list) and cap:
            cap = cap[0]
        if isinstance(cap, str) and cap.strip():
            return _truncate_caption(cap, style)
    raise ValueError(f"single write failed for {style}")


def generate(
    fact_sheet: dict,
    styles: list[str],
    k: int | None = None,
) -> dict[str, list[str]]:
    """Generate caption candidates; batch first, per-style fallback."""
    k = k or config.CANDIDATES
    processed: dict[str, list[str]] = {}

    try:
        processed = _write_batch(fact_sheet, styles, k)
    except Exception:
        processed = {}

    missing = [s for s in styles if not processed.get(s)]
    for style in missing:
        try:
            processed[style] = [_write_one_style(fact_sheet, style)]
        except Exception:
            subjects = fact_sheet.get("subjects") or []
            actions = fact_sheet.get("actions_in_order") or []
            setting = fact_sheet.get("setting", "")
            stub = (
                f"{', '.join(subjects[:2])} {actions[0] if actions else ''} "
                f"in {setting}".strip()
            )
            processed[style] = [_truncate_caption(stub or setting or "the scene", style)]

    return processed
