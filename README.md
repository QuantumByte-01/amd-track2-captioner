# AMD Track 2 — Video Captioning Agent

Containerized video captioning agent for **AMD Developer Hackathon ACT II, Track 2**.

## Architecture

```
tasks.json → parallel downloads → per clip (4 workers):
  ffmpeg uniform-seek frames (8 @ 768px)
    → GROUND: 1 vision call → strict JSON fact sheet
    → WRITE:  1 call → 2 candidates × each requested style
    → JUDGE:  1 call per style → picks best candidate
  → watchdog flush at T+8min → /output/results.json
```

**Graded path (leaderboard):** Fireworks serverless `kimi-k2p6` (vision-capable; Qwen3-VL is on-demand-only on Fireworks as of May 2026).

**Gemma path (demo / Best Use of Gemma):** Same pipeline via pod vLLM serving `google/gemma-3-12b-it` on AMD MI300X — switch with env vars below. The graded container intentionally uses serverless Qwen3-VL because Fireworks Gemma is on-demand-only and won't be deployed during post-deadline re-scoring.

## Quick start

```bash
# Build (supply API key at build time — baked into image per Track 2 rules)
docker build --build-arg FIREWORKS_API_KEY=$FIREWORKS_API_KEY -t amd-track2-captioner .

# Run
mkdir -p input output
cp work/input/tasks.json input/tasks.json   # or your own tasks.json
docker run --rm -v $PWD/input:/input -v $PWD/output:/output amd-track2-captioner
cat output/results.json
```

## Input / Output contract

**Input** (`/input/tasks.json`):
```json
[{"task_id": "v1", "video_url": "https://...", "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]}]
```

**Output** (`/output/results.json`):
```json
[{"task_id": "v1", "captions": {"formal": "...", "sarcastic": "...", "humorous_tech": "...", "humorous_non_tech": "..."}}]
```

## Environment profiles

| Variable | Graded default | Pod / Gemma dev |
|---|---|---|
| `LLM_BASE_URL` | `https://api.fireworks.ai/inference/v1` | `http://localhost:8000/v1` |
| `MODEL_PRIMARY` | `accounts/fireworks/models/kimi-k2p6` | `google/gemma-3-12b-it` |
| `MODEL_FALLBACK` | `accounts/fireworks/models/kimi-k2p6` | same as primary |
| `FIREWORKS_API_KEY` | baked at build | `dummy` for local vLLM |

```bash
# Gemma on MI300X (vLLM must be running)
export LLM_BASE_URL=http://localhost:8000/v1
export MODEL_PRIMARY=google/gemma-3-12b-it
export MODEL_FALLBACK=google/gemma-3-12b-it
export FIREWORKS_API_KEY=dummy
python run.py
```

## Local evaluation

```bash
pip install -r requirements.txt
# set FIREWORKS_API_KEY or Gemma profile above
python eval/eval.py
```

Scores 8 public validation clips against reference captions (directional self-judge).

## CI / submission image

Push to `main` → GitHub Actions builds `linux/amd64` and pushes:

```
ghcr.io/<OWNER>/amd-track2-captioner:v<N>
```

Set repo secret `FIREWORKS_API_KEY`. Make the GHCR package **public** before submitting.

## License

MIT
