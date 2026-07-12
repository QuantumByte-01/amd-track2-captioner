"""Configuration from environment variables with sensible defaults."""

import os

STYLE_ORDER = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
VALID_STYLES = set(STYLE_ORDER)

LLM_BASE_URL = os.environ.get(
    "LLM_BASE_URL", "https://api.fireworks.ai/inference/v1"
)
MODEL_VISION = os.environ.get(
    "MODEL_VISION", "accounts/fireworks/models/kimi-k2p6"
)
MODEL_CAPTION = os.environ.get(
    "MODEL_CAPTION", "accounts/fireworks/models/glm-5p2"
)
MODEL_PRIMARY = os.environ.get("MODEL_PRIMARY", MODEL_VISION)
MODEL_FALLBACK = os.environ.get(
    "MODEL_FALLBACK", "accounts/fireworks/routers/glm-5p2-fast"
)
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")

FRAMES_PER_CLIP = int(os.environ.get("FRAMES_PER_CLIP", "6"))
CANDIDATES = int(os.environ.get("CANDIDATES", "2"))
CLIP_WORKERS = int(os.environ.get("CLIP_WORKERS", "6"))
DL_WORKERS = int(os.environ.get("DL_WORKERS", "6"))
CALL_TIMEOUT = int(os.environ.get("CALL_TIMEOUT", "90"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
SOFT_DEADLINE_SEC = int(os.environ.get("SOFT_DEADLINE_SEC", "540"))
PER_CLIP_BUDGET_SEC = int(os.environ.get("PER_CLIP_BUDGET_SEC", "90"))
MAX_CAPTION_WORDS = int(os.environ.get("MAX_CAPTION_WORDS", "35"))
TRY_GEMMA_FIRST = os.environ.get("TRY_GEMMA_FIRST", "0") == "1"
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "")

STYLE_DEFINITIONS = {
    "formal": (
        "professional, objective, factual. 1-2 sentences, present tense, no humor."
    ),
    "sarcastic": (
        "dry, ironic, lightly mocking. ONE sentence. Mock something actually in the "
        "video; the facts must stay accurate."
    ),
    "humorous_tech": (
        "funny via a programming/technology metaphor mapped to a REAL detail from "
        "the fact sheet. ONE sentence. If the joke could fit any random video, it fails."
    ),
    "humorous_non_tech": (
        "relatable everyday humor about what actually happens. ONE sentence. "
        "Zero technical vocabulary."
    ),
}
