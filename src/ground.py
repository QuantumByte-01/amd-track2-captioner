"""Frames → evidence-locked fact sheet."""

from __future__ import annotations

import json

from src import llm, video

REQUIRED_KEYS = {
    "subjects",
    "actions_in_order",
    "setting",
    "camera",
    "on_screen_text",
    "notable_details",
    "uncertain",
}


def _build_messages(frame_paths: list[str]) -> list[dict]:
    system = llm.load_prompt("ground.txt")
    content: list[dict] = [
        {
            "type": "text",
            "text": "Frames are in chronological order from one clip.",
        }
    ]
    for fp in frame_paths:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{video.b64(fp)}",
                },
            }
        )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]


def _validate(sheet: dict) -> bool:
    return isinstance(sheet, dict) and REQUIRED_KEYS.issubset(sheet.keys())


def ground(frame_paths: list[str]) -> dict:
    """Extract a fact sheet from frame images."""
    messages = _build_messages(frame_paths)
    result = llm.chat(
        messages,
        json_mode=True,
        temperature=0.2,
        max_tokens=1200,
        stage="ground",
    )
    if not isinstance(result, dict) or not _validate(result):
        result = llm.chat(
            messages,
            json_mode=True,
            temperature=0.0,
            max_tokens=1200,
            stage="ground-retry",
        )
    if not isinstance(result, dict):
        raise ValueError("ground returned non-dict")
    for key in REQUIRED_KEYS:
        result.setdefault(key, [] if key != "setting" and key != "camera" else "")
    return result
