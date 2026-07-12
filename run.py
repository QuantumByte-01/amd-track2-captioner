#!/usr/bin/env python3
"""Track 2 video captioning orchestrator with watchdog and graceful degradation."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src import caption, config, ground, judge, schema, video

T0 = time.monotonic()
RESULTS: dict[str, dict | None] = {}
RESULTS_LOCK = threading.Lock()
CLIPS_DIR = "/tmp/clips"


def elapsed() -> float:
    return time.monotonic() - T0


def past_soft_deadline() -> bool:
    return elapsed() >= config.SOFT_DEADLINE_SEC


def _load_tasks() -> list[dict]:
    with open(config.INPUT_PATH, encoding="utf-8") as f:
        tasks = json.load(f)
    if not isinstance(tasks, list):
        raise ValueError("tasks.json must be a JSON array")
    return tasks


def _store(task_id: str, result: dict) -> None:
    with RESULTS_LOCK:
        RESULTS[task_id] = result


def _minimal_from_hint(styles: list[str], hint: str = "") -> dict[str, str]:
    return {s: schema._minimal_caption(s, hint) for s in styles}


def _direct_captions(frame_paths: list[str], styles: list[str]) -> dict[str, str]:
    """Ladder rung: one vision call → all styles."""
    from src import llm

    system = llm.load_prompt("write.txt")
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Infer a fact sheet from these frames, then write ONE caption per "
                f"requested style: {json.dumps(styles)}. Return JSON "
                '{"formal":"...", ...} with only the requested keys.'
            ),
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
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    result = llm.chat(
        messages,
        json_mode=True,
        temperature=0.7,
        max_tokens=1200,
        stage="direct",
    )
    out: dict[str, str] = {}
    if isinstance(result, dict):
        for style in styles:
            val = result.get(style)
            if isinstance(val, list) and val:
                val = val[0]
            if isinstance(val, str) and val.strip():
                out[style] = val.strip()
    for style in styles:
        if style not in out:
            out[style] = schema._minimal_caption(style)
    return out


def process_clip(task: dict, video_path: str | None) -> dict:
    """Process one clip through the pipeline with degradation ladder."""
    task_id = task["task_id"]
    styles = [s for s in task.get("styles", config.STYLE_ORDER) if s in config.VALID_STYLES]
    if not styles:
        styles = list(config.STYLE_ORDER)

    frame_dir = f"/tmp/frames/{task_id}"
    fact_sheet: dict | None = None
    frame_paths: list[str] = []

    try:
        if past_soft_deadline():
            raise TimeoutError("soft deadline reached")

        if video_path and os.path.exists(video_path):
            frame_paths = video.extract_frames(video_path, frame_dir)
        else:
            frame_paths = video.fetch_frames_direct(task["video_url"], frame_dir)

        if not frame_paths:
            raise RuntimeError("no frames extracted")

        fact_sheet = ground.ground(frame_paths)
        candidates = caption.generate(fact_sheet, styles)
        best = judge.pick_best(fact_sheet, candidates, styles)
        return {"task_id": task_id, "captions": best}

    except Exception as e1:
        print(f"[clip] {task_id} full pipeline failed: {e1}", file=sys.stderr)

        if fact_sheet and not past_soft_deadline():
            try:
                candidates = caption.generate(fact_sheet, styles, k=1)
                best = {
                    s: (candidates.get(s) or [schema._minimal_caption(s)])[0]
                    for s in styles
                }
                return {"task_id": task_id, "captions": best}
            except Exception as e2:
                print(f"[clip] {task_id} write-only fallback failed: {e2}", file=sys.stderr)

    try:
        if past_soft_deadline():
            raise TimeoutError("soft deadline reached")
        if not frame_paths:
            if video_path and os.path.exists(video_path):
                frame_paths = video.extract_frames(video_path, frame_dir)
            else:
                frame_paths = video.fetch_frames_direct(task["video_url"], frame_dir)
        if frame_paths:
            best = _direct_captions(frame_paths, styles)
            return {"task_id": task_id, "captions": best}
    except Exception as e3:
        print(f"[clip] {task_id} direct fallback failed: {e3}", file=sys.stderr)

    hint = ""
    if isinstance(fact_sheet, dict):
        hint = str(fact_sheet.get("setting", ""))
    return {"task_id": task_id, "captions": _minimal_from_hint(styles, hint)}


def download_all(tasks: list[dict]) -> dict[str, str]:
    """Download all clips in parallel; return task_id → path map."""
    os.makedirs(CLIPS_DIR, exist_ok=True)
    paths: dict[str, str] = {}

    def _dl(task: dict) -> tuple[str, str | None]:
        task_id = task["task_id"]
        dest = os.path.join(CLIPS_DIR, f"{task_id}.mp4")
        try:
            video.download(task["video_url"], dest)
            return task_id, dest
        except Exception as e:
            print(f"[dl] {task_id} failed: {e}", file=sys.stderr)
            return task_id, None

    with ThreadPoolExecutor(max_workers=config.DL_WORKERS) as pool:
        futures = {pool.submit(_dl, t): t["task_id"] for t in tasks}
        for fut in as_completed(futures):
            tid, path = fut.result()
            if path:
                paths[tid] = path
    return paths


def finalize_and_write(tasks: list[dict]) -> bool:
    """Fill gaps, validate, and atomically write results.json."""
    ordered: list[dict | None] = []
    for task in tasks:
        tid = task["task_id"]
        with RESULTS_LOCK:
            entry = RESULTS.get(tid)
        if entry is None:
            styles = [s for s in task.get("styles", config.STYLE_ORDER) if s in config.VALID_STYLES]
            entry = {
                "task_id": tid,
                "captions": _minimal_from_hint(styles or list(config.STYLE_ORDER)),
            }
        ordered.append(entry)

    repaired = schema.validate_and_repair(ordered, tasks)

    out_dir = os.path.dirname(config.OUTPUT_PATH) or "/output"
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = config.OUTPUT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(repaired, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, config.OUTPUT_PATH)
    print(f"[done] wrote {config.OUTPUT_PATH} ({len(repaired)} tasks)", file=sys.stderr)
    return True


def main() -> None:
    global T0
    T0 = time.monotonic()
    tasks = _load_tasks()

    for task in tasks:
        with RESULTS_LOCK:
            RESULTS[task["task_id"]] = None

    wrote = False
    try:
        paths = download_all(tasks)

        def _work(task: dict) -> None:
            tid = task["task_id"]
            result = process_clip(task, paths.get(tid))
            _store(tid, result)

        with ThreadPoolExecutor(max_workers=config.CLIP_WORKERS) as pool:
            futures = [pool.submit(_work, t) for t in tasks]
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as e:
                    print(f"[clip] worker error: {e}", file=sys.stderr)

    finally:
        wrote = finalize_and_write(tasks)

    sys.exit(0 if wrote else 1)


if __name__ == "__main__":
    main()
