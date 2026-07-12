"""Fact sheet → styled caption candidates."""

from __future__ import annotations

import json
import re

from src import config, llm

_WORD_RE = re.compile(r"\S+")


def _truncate_caption(text: str) -> str:
    text = text.strip().strip('"').strip("'")
    words = _WORD_RE.findall(text)
    if len(words) <= config.MAX_CAPTION_WORDS:
        return text

    sentences = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    count = 0
    for sent in sentences:
        sent_words = _WORD_RE.findall(sent)
        if count + len(sent_words) > config.MAX_CAPTION_WORDS:
            break
        out.append(sent)
        count += len(sent_words)
    if out:
        return " ".join(out).strip()

    return " ".join(words[: config.MAX_CAPTION_WORDS])


def _post_process(candidates: dict[str, list[str]], styles: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for style in styles:
        raw = candidates.get(style, [])
        if not isinstance(raw, list):
            raw = [str(raw)] if raw else []
        cleaned = [_truncate_caption(c) for c in raw if c and str(c).strip()]
        out[style] = cleaned
    return out


def generate(
    fact_sheet: dict,
    styles: list[str],
    k: int | None = None,
) -> dict[str, list[str]]:
    """Generate k caption candidates per requested style."""
    k = k or config.CANDIDATES
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
    result = llm.chat(
        messages,
        json_mode=True,
        temperature=0.9,
        max_tokens=1600,
        stage="write",
    )
    if not isinstance(result, dict):
        raise ValueError("write returned non-dict")

    processed = _post_process(result, styles)

    missing = [s for s in styles if not processed.get(s)]
    if missing:
        retry_user = user + f"\n\nRegenerate non-empty captions for: {missing}"
        retry_messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": retry_user},
        ]
        retry = llm.chat(
            retry_messages,
            json_mode=True,
            temperature=0.7,
            max_tokens=1600,
            stage="write-retry",
        )
        if isinstance(retry, dict):
            retry_processed = _post_process(retry, missing)
            for style in missing:
                if retry_processed.get(style):
                    processed[style] = retry_processed[style]

    for style in styles:
        if not processed.get(style):
            processed[style] = [f"A scene showing {fact_sheet.get('setting', 'the video')}."]

    return processed
