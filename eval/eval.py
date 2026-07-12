#!/usr/bin/env python3
"""Local eval harness: run pipeline on 8 public clips and self-judge vs references."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, llm  # noqa: E402

_EVAL_MODEL = "accounts/fireworks/routers/glm-5p2-fast"
_SCORE_RE = re.compile(
    r'"accuracy"\s*:\s*([\d.]+).*?"style"\s*:\s*([\d.]+)',
    re.IGNORECASE | re.DOTALL,
)

STYLES = config.STYLE_ORDER

_EVAL_JUDGE_SYSTEM = """You score ONE video caption against a fact sheet and style definition.
A REFERENCE caption shows the target tone/register (not ground truth for facts).

Return JSON only, no markdown:
{"accuracy": 0.0, "style": 0.0}

accuracy 0.0-1.0: every claim must be supported by the fact sheet. Unsupported claims cap at 0.3.
Generic captions that could fit many videos cap at 0.6. Specific grounded detail scores higher.

style 0.0-1.0: tone, register, and length match the STYLE definition and REFERENCE cadence."""


def build_tasks(refs: dict) -> list[dict]:
    return [
        {
            "task_id": tid,
            "video_url": data["url"],
            "styles": STYLES,
        }
        for tid, data in refs.items()
    ]


def _parse_eval_scores(raw: object) -> tuple[float, float]:
    if isinstance(raw, dict):
        if "accuracy" in raw and "style" in raw:
            return float(raw["accuracy"]), float(raw["style"])
        if raw.get("scores") and isinstance(raw["scores"], list) and raw["scores"]:
            s = raw["scores"][0]
            if isinstance(s, dict):
                return float(s.get("accuracy", 0)), float(s.get("style", 0))
    text = str(raw)
    m = _SCORE_RE.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    for mobj in reversed(list(re.finditer(r"\{[^{}]*\}", text))):
        try:
            parsed = json.loads(mobj.group(0))
            acc, sty = _parse_eval_scores(parsed)
            if acc or sty:
                return acc, sty
        except json.JSONDecodeError:
            continue
    try:
        parsed = json.loads(llm._extract_json_object(text))
        return _parse_eval_scores(parsed)
    except (json.JSONDecodeError, ValueError):
        pass
    return 0.0, 0.0


def _reference_fact_sheet(ref: dict) -> dict:
    """Approximate fact sheet for local scoring (pipeline fact sheets not persisted)."""
    formal = ref.get("formal", "")
    desc = ref.get("desc", "")
    return {
        "setting": desc,
        "subjects": [s.strip() for s in desc.split(",") if s.strip()],
        "actions_in_order": [],
        "camera": "",
        "on_screen_text": [],
        "notable_details": [desc, formal],
        "uncertain": [],
    }


def score_caption(
    fact_sheet: dict,
    style: str,
    caption_text: str,
    reference: str,
) -> tuple[float, float]:
    user = (
        f"STYLE: {style} ({config.STYLE_DEFINITIONS[style]})\n"
        f"FACT HINT: {fact_sheet.get('setting', '')}\n"
        f"REFERENCE TONE:\n{reference}\n\n"
        f"CAPTION:\n{caption_text}\n\n"
        "Return only JSON: {\"accuracy\":0.0,\"style\":0.0}"
    )
    messages = [
        {"role": "system", "content": _EVAL_JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ]
    try:
        raw = llm.chat(
            messages,
            model=_EVAL_MODEL,
            json_mode=False,
            temperature=0.0,
            max_tokens=2000,
            stage=f"eval-{style}",
        )
        acc, sty = _parse_eval_scores(raw)
        if acc or sty:
            return acc, sty
    except Exception as e:
        print(f"eval judge failed ({style}): {e}", file=sys.stderr)
    return 0.0, 0.0


def main() -> None:
    refs_path = ROOT / "eval" / "references.json"
    with open(refs_path, encoding="utf-8") as f:
        refs = json.load(f)

    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    input_path = work / "input" / "tasks.json"
    output_path = work / "output" / "results.json"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tasks = build_tasks(refs)
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

    env = os.environ.copy()
    env["INPUT_PATH"] = str(input_path)
    env["OUTPUT_PATH"] = str(output_path)

    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run.py")],
        cwd=str(ROOT),
        env=env,
        capture_output=False,
    )
    elapsed = time.time() - t0
    if proc.returncode != 0:
        print("pipeline failed", file=sys.stderr)
        sys.exit(1)

    with open(output_path, encoding="utf-8") as f:
        results = json.load(f)
    by_id = {r["task_id"]: r for r in results}

    rows: list[dict] = []
    acc_sum = sty_sum = n = 0

    print(f"\n{'clip':<6} {'style':<18} {'acc':>5} {'sty':>5}")
    print("-" * 40)

    for tid, ref in refs.items():
        captions = by_id.get(tid, {}).get("captions", {})
        for style in STYLES:
            cap = captions.get(style, "")
            acc, sty = score_caption(
                _reference_fact_sheet(ref),
                style,
                cap,
                ref[style],
            )
            mean = (acc + sty) / 2
            acc_sum += acc
            sty_sum += sty
            n += 1
            rows.append(
                {
                    "task_id": tid,
                    "style": style,
                    "accuracy": acc,
                    "style_score": sty,
                    "mean": mean,
                }
            )
            print(f"{tid:<6} {style:<18} {acc:5.2f} {sty:5.2f}")

    global_mean = (acc_sum + sty_sum) / (2 * n) if n else 0
    print("-" * 40)
    print(f"Global mean: {global_mean:.3f}  wall clock: {elapsed:.1f}s")

    history = work / "eval_history.jsonl"
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "global_mean": global_mean,
        "elapsed_sec": elapsed,
        "rows": rows,
    }
    with open(history, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main()
