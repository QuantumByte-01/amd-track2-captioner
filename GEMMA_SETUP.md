# Gemma on AMD MI300X — Setup Blocked

**Status:** vLLM launch failed — `google/gemma-3-12b-it` is **gated on HuggingFace**.

## GPU (ready)

```
rocm-smi --showmeminfo vram
GPU[0]: VRAM Total 51522830336 (~48 GiB), Used 28028928 (idle)
```

## Blocker

vLLM log (`/workspace/vllm.log`):

```
huggingface_hub.errors.GatedRepoError: 401 Unauthorized
Cannot access gated repo google/gemma-3-12b-it
```

## Fix (you, ~2 min)

1. Laptop: https://huggingface.co/google/gemma-3-12b-it → accept license
2. Create read token: HuggingFace Settings → Access Tokens
3. On pod:

```bash
export HF_TOKEN=hf_xxxxxxxx
cd /workspace
nohup vllm serve google/gemma-3-12b-it \
  --host 0.0.0.0 --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 8192 \
  --dtype bfloat16 \
  --limit-mm-per-prompt '{"image": 8}' \
  > vllm.log 2>&1 &
tail -f vllm.log   # wait for Uvicorn on :8000
```

## Gemma pipeline command (after vLLM ready)

```bash
cd /workspace/track2
LLM_BASE_URL=http://localhost:8000/v1 \
MODEL_VISION=google/gemma-3-12b-it \
MODEL_CAPTION=google/gemma-3-12b-it \
MODEL_FALLBACK=google/gemma-3-12b-it \
FIREWORKS_API_KEY=dummy \
INPUT_PATH=work/input/tasks.json \
OUTPUT_PATH=work/gemma_results.json \
python run.py
```

**Do NOT deploy Gemma on Fireworks** — on-demand billing drains the same $50 credit pool as Kimi/GLM.
