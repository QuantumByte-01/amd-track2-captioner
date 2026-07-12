"""Output validation, repair, and fact-derived fallbacks."""

from __future__ import annotations

from src import config


def fact_hint(sheet: dict | None) -> str:
    if not isinstance(sheet, dict):
        return ""
    parts: list[str] = []
    subjects = sheet.get("subjects") or []
    actions = sheet.get("actions_in_order") or []
    setting = str(sheet.get("setting", "")).strip()
    details = sheet.get("notable_details") or []
    if subjects:
        parts.append(", ".join(str(s) for s in subjects[:3]))
    if actions:
        parts.append(str(actions[0]))
    if setting:
        parts.append(setting)
    elif details:
        parts.append(str(details[0]))
    return "; ".join(p for p in parts if p)


def _minimal_caption(style: str, hint: str = "", sheet: dict | None = None) -> str:
    hint = hint.strip() or fact_hint(sheet) or "a short video scene"
    hint = hint.rstrip(".")
    templates = {
        "formal": f"The footage shows {hint}.",
        "sarcastic": f"Fascinating — {hint}, and somehow still the highlight of the day.",
        "humorous_tech": (
            f"My build pipeline processes {hint} with fewer retries than this clip has frames."
        ),
        "humorous_non_tech": (
            f"This is exactly the kind of moment where {hint.split(';')[0].lower()} steals the show."
        ),
    }
    return templates.get(style, f"The footage shows {hint}.")


def validate_and_repair(
    results: list[dict | None],
    tasks: list[dict],
) -> list[dict]:
    """Ensure output matches the required schema; never raises."""
    repaired: list[dict] = []

    for i, task in enumerate(tasks):
        task_id = task["task_id"]
        styles = task.get("styles") or list(config.STYLE_ORDER)
        styles = [s for s in styles if s in config.VALID_STYLES]

        entry = None
        if i < len(results):
            entry = results[i]
        if entry is None and isinstance(results, dict):
            entry = results.get(task_id)  # type: ignore[union-attr]

        if not isinstance(entry, dict):
            entry = {"task_id": task_id, "captions": {}}

        if entry.get("task_id") != task_id:
            entry["task_id"] = task_id

        captions = entry.get("captions")
        if not isinstance(captions, dict):
            captions = {}

        for style in styles:
            val = captions.get(style)
            if not isinstance(val, str) or not val.strip():
                captions[style] = _minimal_caption(style)

        entry["captions"] = {s: captions[s] for s in styles}
        repaired.append(entry)

    return repaired
