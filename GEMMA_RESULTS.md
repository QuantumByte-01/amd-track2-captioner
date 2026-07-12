# Gemma-3-12B on AMD MI300X — Results

**Date:** 2026-07-12 UTC  
**Hardware:** AMD Instinct MI300X (ROCm), ~48 GiB VRAM  
**Stack:** vLLM 0.16.1 + `google/gemma-3-12b-it`  
**Pipeline:** Identical Track 2 agent — ground → write → judge, all via local vLLM

## Serving

```bash
vllm serve google/gemma-3-12b-it \
  --host 0.0.0.0 --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 8192 \
  --dtype bfloat16 \
  --limit-mm-per-prompt '{"image": 8}'
```

Smoke test: `curl localhost:8000/v1/chat/completions` → `"OK!"`

## GPU snapshot (during/after serve)

| Metric | Value |
|--------|-------|
| VRAM used | ~39.6 GiB / ~48 GiB (**82%**) |
| Temp | 48°C |
| Power | ~62 W idle after run |

## 8-clip public eval run

| Metric | Value |
|--------|-------|
| Input | `work/input/tasks.json` (8 public validation clips) |
| Output | `work/gemma_results.json` |
| Wall clock | **86 s** |
| Models | `MODEL_VISION`, `MODEL_CAPTION`, `MODEL_FALLBACK` = `google/gemma-3-12b-it` |

## Sample captions (v1 — urban autumn boulevard)

| Style | Caption |
|-------|---------|
| formal | This urban street showcases multiple lanes of traffic, including cars, buses, and motorcycles, all moving right, alongside tall gray and white apartment buildings and trees displaying yellow leaves. |
| sarcastic | Ah yes, a perfectly organized urban commute, where everything moves in the same direction, eventually. |
| humorous_tech | When you finally refactor your codebase and everything still runs on the same multiple lanes of traffic. |
| humorous_non_tech | When you finally think you've mastered parallel parking, but then you see the traffic. |

## Sample captions (v4 — mountains)

| Style | Caption |
|-------|---------|
| sarcastic | Ah yes, a mountain range and a city—because we needed *more* places to escape to. |
| humorous_non_tech | When you finally reach the summit and realize you left your phone in the car. |

## Partner prize narrative

The **same containerized pipeline** that ships on GHCR (Kimi K2.6 + GLM 5.2 for grader availability) runs **end-to-end on Gemma-3-12B** on AMD Instinct MI300X via ROCm + vLLM — grounding, styling, and judging — with no Fireworks Gemma deployment and zero incremental API cost on the pod.

**Demo evidence:** screen recording of `rocm-smi` + vLLM log + captions appearing (capture manually).
