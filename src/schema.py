"""Output validation and repair."""

from __future__ import annotations

from src import config


def _minimal_caption(style: str, hint: str = "") -> str:
    base = hint.strip() or "A short video clip."
    templates = {
        "formal": f"The footage shows {base.rstrip('.')}.",
        "sarcastic": f"Sure, {base.rstrip('.')} — riveting cinema.",
        "humorous_tech": (
            f"This clip deployed more pixels than my last CI pipeline, "
            f"and with fewer errors."
        ),
        "humorous_non_tech": (
            f"Somehow this is exactly the kind of video you end up watching "
            f"at midnight."
        ),
    }
    return templates.get(style, base)


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
