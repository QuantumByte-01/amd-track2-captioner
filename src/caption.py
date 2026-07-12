"""Fact sheet → styled caption candidates via text model."""

from __future__ import annotations

import json
import re

from src import config, llm

_META_RE = re.compile(
    r"\b(this (video|clip|footage|caption|image|frame)|the video shows|"
    r"in this scene|as an ai)\b",
    re.IGNORECASE,
)
_HEDGE_RE = re.compile(
    r"\b(appears?|seems?|possibly|probably|might|maybe|perhaps|likely)\b",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"\S+")

# Hard ceiling per style (words). Prompts teach target ranges; code enforces ceiling only.
_STYLE_CEILING = {
    "formal": 35,
    "sarcastic": 25,
    "humorous_tech": 25,
    "humorous_non_tech": 25,
}


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _clean_caption(text: str) -> str:
    text = text.strip().strip('"').strip("'")
    text = _META_RE.sub("", text).strip()
    text = _HEDGE_RE.sub("", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _fits_limit(text: str, style: str) -> bool:
    return _word_count(text) <= _STYLE_CEILING.get(style, config.MAX_CAPTION_WORDS)


def _needs_regen(text: str, style: str) -> bool:
    if not text or text.rstrip()[-1] not in ".!?":
        return True
    if _HEDGE_RE.search(text):
        return True
    return not _fits_limit(text, style)


def _sentence_trim(text: str, style: str) -> str | None:
    """Return longest prefix of complete sentences within word limit, or None."""
    limit = _STYLE_CEILING.get(style, config.MAX_CAPTION_WORDS)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    out: list[str] = []
    count = 0
    for sent in sentences:
        if not sent.strip():
            continue
        n = _word_count(sent)
        if count + n > limit:
            break
        out.append(sent.strip())
        count += n
    if not out:
        return None
    result = " ".join(out)
    if result and result[-1] not in ".!?":
        result += "."
    return result


def _finalize_caption(text: str, style: str) -> str:
    text = _clean_caption(text)
    if not text:
        return text
    if _fits_limit(text, style):
        if text[-1] not in ".!?":
            text += "."
        return text
    trimmed = _sentence_trim(text, style)
    if trimmed:
        return trimmed
    return text


def _post_process(candidates: dict[str, list[str]], styles: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for style in styles:
        raw = candidates.get(style, [])
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            raw = [str(raw)] if raw else []
        cleaned = [_finalize_caption(c, style) for c in raw if c and str(c).strip()]
        out[style] = [c for c in cleaned if c]
    return out


def _write_batch(fact_sheet: dict, styles: list[str], k: int) -> dict[str, list[str]]:
    system = llm.load_prompt("write.txt")
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"REQUESTED STYLES: {json.dumps(styles)}\n"
        f"CANDIDATES PER STYLE: {k}\n"
        "Every caption must be a complete sentence within the word limits."
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
            temperature=0.55,
            max_tokens=1600,
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
        temperature=0.35,
        max_tokens=1600,
        stage="write-batch-text",
    )
    if isinstance(result, str):
        parsed = json.loads(llm._extract_json_object(result))
        if isinstance(parsed, dict):
            return _post_process(parsed, styles)
    raise ValueError("batch write failed")


def _write_one_style(fact_sheet: dict, style: str, temperature: float = 0.5) -> str:
    system = llm.load_prompt("write.txt")
    limit = _STYLE_CEILING.get(style, 35)
    definition = config.STYLE_DEFINITIONS[style]
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"Write exactly ONE complete caption for style '{style}' ({definition}).\n"
        f"MAX {limit} words. No hedging words. Return JSON only: {{\"caption\": \"...\"}}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    result = llm.chat(
        messages,
        model=config.MODEL_CAPTION,
        json_mode=True,
        temperature=temperature,
        max_tokens=300,
        stage=f"write-{style}",
    )
    if isinstance(result, dict):
        cap = result.get("caption") or result.get(style)
        if isinstance(cap, list) and cap:
            cap = cap[0]
        if isinstance(cap, str) and cap.strip():
            return _finalize_caption(cap, style)
    raise ValueError(f"single write failed for {style}")


def _regenerate_if_bad(fact_sheet: dict, style: str, caption: str) -> str:
    if not _needs_regen(caption, style):
        return caption
    try:
        return _write_one_style(fact_sheet, style, temperature=0.6)
    except Exception:
        trimmed = _sentence_trim(caption, style)
        return trimmed or caption


def generate(
    fact_sheet: dict,
    styles: list[str],
    k: int | None = None,
) -> dict[str, list[str]]:
    """Generate caption candidates; batch first, per-style fallback + regen."""
    k = k or config.CANDIDATES
    processed: dict[str, list[str]] = {}

    try:
        processed = _write_batch(fact_sheet, styles, k)
    except Exception:
        processed = {}

    for style in styles:
        if not processed.get(style):
            try:
                processed[style] = [_write_one_style(fact_sheet, style)]
            except Exception:
                subjects = fact_sheet.get("subjects") or []
                actions = fact_sheet.get("actions_in_order") or []
                setting = fact_sheet.get("setting", "")
                stub = (
                    f"{', '.join(str(s) for s in subjects[:2])} "
                    f"{actions[0] if actions else ''} in {setting}".strip()
                )
                processed[style] = [_finalize_caption(stub or setting or "the scene", style)]

        fixed = []
        for cap in processed.get(style, []):
            fixed.append(_regenerate_if_bad(fact_sheet, style, cap))
        processed[style] = fixed

    return processed
