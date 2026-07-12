#!/usr/bin/env python3
"""Local eval harness: run pipeline on 8 public clips and self-judge vs references."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config, llm  # noqa: E402

STYLES = config.STYLE_ORDER


def build_tasks(refs: dict) -> list[dict]:
    return [
        {
            "task_id": tid,
            "video_url": data["url"],
            "styles": STYLES,
        }
        for tid, data in refs.items()
    ]


def score_caption(
    fact_sheet: dict,
    style: str,
    caption_text: str,
    reference: str,
) -> tuple[float, float]:
    system = llm.load_prompt("judge.txt")
    user = (
        f"FACT SHEET:\n{json.dumps(fact_sheet, ensure_ascii=False)}\n\n"
        f"STYLE: {style}\n"
        f"DEFINITION: {config.STYLE_DEFINITIONS[style]}\n\n"
        f"REFERENCE (tone anchor, not ground truth):\n{reference}\n\n"
        f"CANDIDATES:\n0. {caption_text}"
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
            max_tokens=400,
            stage=f"eval-{style}",
        )
        if isinstance(result, dict) and result.get("scores"):
            s = result["scores"][0]
            return float(s.get("accuracy", 0)), float(s.get("style", 0))
    except Exception as e:
        print(f"eval judge failed: {e}", file=sys.stderr)
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
                {"setting": ref["desc"], "subjects": [], "actions_in_order": [],
                 "camera": "", "on_screen_text": [], "notable_details": [], "uncertain": []},
                style,
                cap,
                ref[style],
            )
            mean = (acc + sty) / 2
            acc_sum += acc
            sty_sum += sty
            n += 1
            rows.append({"task_id": tid, "style": style, "accuracy": acc, "style_score": sty, "mean": mean})
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
