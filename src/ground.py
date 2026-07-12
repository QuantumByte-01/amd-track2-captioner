"""Frames → evidence-locked fact sheet via vision model."""

from __future__ import annotations

from src import config, llm, video

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
    if not isinstance(sheet, dict) or not REQUIRED_KEYS.issubset(sheet.keys()):
        return False
    has_subjects = bool(sheet.get("subjects"))
    has_actions = bool(sheet.get("actions_in_order"))
    has_setting = bool(str(sheet.get("setting", "")).strip())
    has_details = bool(sheet.get("notable_details"))
    return has_subjects or has_actions or has_setting or has_details


def ground(frame_paths: list[str]) -> dict:
    """Extract a fact sheet from frame images."""
    for n in (len(frame_paths), max(4, len(frame_paths) // 2)):
        frames = frame_paths[:n]
        messages = _build_messages(frames)
        for stage, temp in (("ground", 0.2), ("ground-retry", 0.0)):
            try:
                result = llm.chat(
                    messages,
                    model=config.MODEL_VISION,
                    json_mode=True,
                    temperature=temp,
                    max_tokens=2048,
                    stage=stage,
                    vision=True,
                )
                if isinstance(result, dict) and _validate(result):
                    for key in REQUIRED_KEYS:
                        result.setdefault(key, [] if key not in ("setting", "camera") else "")
                    return result
            except Exception:
                continue
    raise ValueError("ground fact sheet unusable")
