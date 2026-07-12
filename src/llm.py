"""OpenAI-compatible chat client with retries, fallback, and JSON mode."""

from __future__ import annotations

import json
import re
import sys
import time
from typing import Any

import requests

from src import config

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


def _parse_json(text: str) -> dict | list:
    cleaned = _strip_fences(text)
    if not cleaned:
        raise json.JSONDecodeError("empty content", text, 0)
    return json.loads(cleaned)


def _repair_json(raw: str, model: str) -> dict | list:
    messages = [
        {
            "role": "user",
            "content": (
                "Return the same content as strictly valid JSON, nothing else:\n\n"
                + raw
            ),
        }
    ]
    result = _post_chat(messages, model=model, json_mode=True, max_tokens=1200, temperature=0.0)
    if isinstance(result, dict):
        return result
    return _parse_json(str(result))


def _post_chat(
    messages: list[dict],
    model: str,
    json_mode: bool,
    max_tokens: int,
    temperature: float,
    timeout: int | None = None,
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
    content = data["choices"][0]["message"]["content"]
    if content is None or (isinstance(content, str) and not content.strip()):
        raise ValueError("empty model response")
    print(
        f"[llm] model={model} latency={latency:.2f}s ok",
        file=sys.stderr,
    )
    return content


def chat(
    messages: list[dict],
    model: str | None = None,
    json_mode: bool = True,
    max_tokens: int = 1200,
    temperature: float = 0.7,
    stage: str = "",
) -> dict | str:
    """Send a chat completion request with retries and model fallback."""
    primary = model or config.MODEL_PRIMARY
    fallback = config.MODEL_FALLBACK

    models_to_try: list[str] = []
    if config.TRY_GEMMA_FIRST and config.GEMMA_MODEL:
        models_to_try.append(config.GEMMA_MODEL)
    models_to_try.append(primary)
    if fallback and fallback != primary:
        models_to_try.append(fallback)

    last_err: Exception | None = None

    for idx, current_model in enumerate(models_to_try):
        retries = 1 if (
            config.TRY_GEMMA_FIRST
            and config.GEMMA_MODEL
            and current_model == config.GEMMA_MODEL
        ) else config.MAX_RETRIES
        timeout = 8 if (
            config.TRY_GEMMA_FIRST
            and config.GEMMA_MODEL
            and current_model == config.GEMMA_MODEL
        ) else config.CALL_TIMEOUT

        for attempt in range(retries + 1):
            try:
                if stage:
                    print(f"[llm] stage={stage} model={current_model}", file=sys.stderr)
                raw = _post_chat(
                    messages,
                    model=current_model,
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                )
                if not json_mode:
                    return raw
                try:
                    return _parse_json(str(raw))
                except (json.JSONDecodeError, ValueError):
                    try:
                        return _repair_json(str(raw), current_model)
                    except Exception:
                        if attempt < retries:
                            time.sleep(1 if attempt == 0 else 2)
                            continue
                        raise
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(1 if attempt == 0 else 3)
                continue

        if idx == 0 and config.TRY_GEMMA_FIRST and config.GEMMA_MODEL:
            continue

    if last_err:
        raise last_err
    raise RuntimeError("chat failed with no error recorded")


def load_prompt(name: str) -> str:
    """Load a prompt file from the prompts directory."""
    import os

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "prompts", name), encoding="utf-8") as f:
        return f.read()
