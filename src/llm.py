"""OpenAI-compatible chat client with retries, fallback, and robust JSON."""

from __future__ import annotations

import json
import re
import sys
import time
from typing import Any

import requests

from src import config

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _strip_fences(text: str) -> str:
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


def _extract_json_object(text: str) -> str:
    cleaned = _strip_fences(text)
    if cleaned:
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass
    m = _JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError("no JSON object in response")
    return m.group(0)


def _parse_json(text: str) -> dict | list:
    return json.loads(_extract_json_object(text))


def _kimi_extra() -> dict:
    return {}


def _repair_json(raw: str, model: str) -> dict | list:
    messages = [
        {
            "role": "user",
            "content": (
                "Return the same content as strictly valid JSON, nothing else:\n\n"
                + raw[:4000]
            ),
        }
    ]
    result = _post_chat(
        messages,
        model=model,
        json_mode=False,
        max_tokens=1600,
        temperature=0.0,
    )
    return _parse_json(str(result))


def _post_chat(
    messages: list[dict],
    model: str,
    json_mode: bool,
    max_tokens: int,
    temperature: float,
    timeout: int | None = None,
    vision: bool = False,
) -> dict | str:
    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    t0 = time.time()
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout or config.CALL_TIMEOUT,
    )

    if resp.status_code == 400 and json_mode and "response_format" in payload:
        del payload["response_format"]
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout or config.CALL_TIMEOUT,
        )

    latency = time.time() - t0
    if not resp.ok:
        print(
            f"[llm] model={model} latency={latency:.2f}s fail status={resp.status_code}",
            file=sys.stderr,
        )
        resp.raise_for_status()

    data = resp.json()
    choice = data["choices"][0]
    msg = choice["message"]
    content = msg.get("content") or ""
    if not str(content).strip() and msg.get("reasoning_content"):
        # Last resort: some Kimi responses embed JSON only in reasoning tail
        rc = str(msg.get("reasoning_content"))
        try:
            content = _extract_json_object(rc)
        except ValueError:
            content = rc
    finish = choice.get("finish_reason", "")
    if content is None or (isinstance(content, str) and not content.strip()):
        print(
            f"[llm] empty content model={model} finish={finish}",
            file=sys.stderr,
        )
        raise ValueError("empty model response")
    if finish == "length":
        print(f"[llm] truncated model={model} len={len(str(content))}", file=sys.stderr)
    print(f"[llm] model={model} latency={latency:.2f}s ok", file=sys.stderr)
    return content


def chat(
    messages: list[dict],
    model: str | None = None,
    json_mode: bool = True,
    max_tokens: int = 1200,
    temperature: float = 0.7,
    stage: str = "",
    vision: bool = False,
) -> dict | str:
    """Send a chat completion with retries, fallback, and JSON recovery."""
    primary = model or (config.MODEL_VISION if vision else config.MODEL_CAPTION)
    fallback = config.MODEL_VISION if vision else config.MODEL_FALLBACK

    models_to_try: list[str] = [primary]
    if fallback and fallback != primary:
        models_to_try.append(fallback)

    last_err: Exception | None = None

    for current_model in models_to_try:
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                if stage:
                    print(f"[llm] stage={stage} model={current_model}", file=sys.stderr)
                raw = _post_chat(
                    messages,
                    model=current_model,
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    vision=vision,
                )
                if not json_mode:
                    return raw
                try:
                    return _parse_json(str(raw))
                except (json.JSONDecodeError, ValueError):
                    try:
                        raw2 = _post_chat(
                            messages,
                            model=current_model,
                            json_mode=False,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            vision=vision,
                        )
                        return _parse_json(str(raw2))
                    except (json.JSONDecodeError, ValueError):
                        if str(raw).strip():
                            return _repair_json(str(raw), current_model)
                        raise
            except Exception as e:
                last_err = e
                if attempt < config.MAX_RETRIES:
                    time.sleep(1 if attempt == 0 else 2)
                continue

    if last_err:
        raise last_err
    raise RuntimeError("chat failed with no error recorded")


def load_prompt(name: str) -> str:
    import os

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "prompts", name), encoding="utf-8") as f:
        return f.read()
