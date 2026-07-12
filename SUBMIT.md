# lablab.ai Track 2 Submission — Copy/Paste Ready

## Docker image (after Actions build completes)

```
ghcr.io/QuantumByte-01/amd-track2-captioner:v1
```

Replace `v1` with the actual run number from GitHub Actions (e.g. `v2`, `v3`).

## GitHub repo

```
https://github.com/QuantumByte-01/amd-track2-captioner
```

## Suggested form fields

**Title:** StyleCap — Grounded Multi-Style Video Captioning

**Short description:** A containerized video captioning agent that generates formal, sarcastic, humorous-tech, and humorous-non-tech captions using evidence-locked fact sheets and Fireworks Kimi K2.6 vision API. Gemma-on-AMD MI300X path documented for partner prize.

**Long description:** Two-phase anti-hallucination pipeline: (1) uniform ffmpeg frame sampling → vision model extracts strict JSON fact sheet; (2) text model styles captions from facts only. Graceful degradation ladder, 8-minute watchdog, guaranteed schema-valid output. Graded path uses Fireworks serverless Kimi K2.6; Gemma-3-12B on AMD MI300X via vLLM for partner demo.

**Tags:** Gemma, AMD ROCm, AMD Developer Cloud, Fireworks AI

**Application URL:** https://github.com/QuantumByte-01/amd-track2-captioner

## One remaining CI step (if build not started)

Your PAT cannot push `.github/workflows/` files. In the GitHub web UI:

1. Repo → **Add file → Create new file**
2. Path: `.github/workflows/build.yml`
3. Copy contents from `COPY_ME_TO_dot_github_workflows_build.yml` in this repo
4. Commit to `main`

Secret `FIREWORKS_API_KEY` is already set — build starts automatically.

## After build

1. GitHub → **Packages** → `amd-track2-captioner` → **Public**
2. Verify: `docker pull ghcr.io/QuantumByte-01/amd-track2-captioner:v1`
3. Submit image tag on lablab Track 2 form

## Deadline

3:30 AM IST, Mon Jul 13, 2026
