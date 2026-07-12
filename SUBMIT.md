# lablab.ai Track 2 Submission — Copy/Paste Ready (verified 2026-07-12)

## Docker image (latest green build)

```
ghcr.io/quantumbyte-01/amd-track2-captioner:v34
```

- **Latest Actions build:** #34 — success (commit `de5634f`)
- **Also tagged:** `ghcr.io/quantumbyte-01/amd-track2-captioner:latest` (same digest as v34)
- **Verify on your laptop:** `docker pull ghcr.io/quantumbyte-01/amd-track2-captioner:v34`
- **After pasting workflow:** build #35+ adds API-key guard + smoke test — update submission to `v35` when green

> Use **lowercase** `quantumbyte-01` only. GHCR package must stay **Public**.

## GitHub repo

```
https://github.com/QuantumByte-01/amd-track2-captioner
```

## Hackathon page

```
https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii
```

## Suggested form fields

**Title:** StyleCap — Grounded Multi-Style Video Captioning

**Short description:** Containerized video captioning agent: Kimi K2.6 vision fact sheets → GLM 5.2 styled captions (formal, sarcastic, humorous-tech, humorous-non-tech). Identical pipeline runs Gemma-3-12B end-to-end on AMD MI300X via ROCm/vLLM.

**Long description:** Two-phase anti-hallucination pipeline: (1) ffmpeg uniform-seek frames → vision model extracts strict JSON fact sheet; (2) text model styles captions from facts only, batched judge picks best candidate. Graceful degradation ladder, 9-minute soft deadline, guaranteed schema-valid output. **Graded Docker image:** serverless Kimi K2.6 + GLM 5.2 (Fireworks, key baked in). **Partner demo:** Gemma-3-12B on AMD Instinct MI300X — 8 public clips in 86s (see GEMMA_RESULTS.md).

**Tags:** Gemma, AMD ROCm, AMD Developer Cloud, Fireworks AI

**Application URL:** https://github.com/QuantumByte-01/amd-track2-captioner

**Package page (public check):** https://github.com/QuantumByte-01/amd-track2-captioner/pkgs/container/amd-track2-captioner

## Models (graded container)

| Role | Model |
|------|-------|
| Vision / ground | `accounts/fireworks/models/kimi-k2p6` |
| Caption / judge | `accounts/fireworks/models/glm-5p2` |
| API | `https://api.fireworks.ai/inference/v1` |

## Models (Gemma demo on pod)

| Role | Model |
|------|-------|
| All stages | `google/gemma-3-12b-it` via vLLM `http://localhost:8000/v1` |

## Evidence files in repo

- `GEMMA_RESULTS.md` — MI300X run timings + sample captions
- `work/gemma_results.json` — 8-clip Gemma output

## Workflow (optional — proves baked key)

Paste `COPY_ME_TO_dot_github_workflows_build.yml` → `.github/workflows/build.yml` in GitHub browser (PAT cannot push workflows).

## Deadline

3:30 AM IST, Mon Jul 13, 2026
