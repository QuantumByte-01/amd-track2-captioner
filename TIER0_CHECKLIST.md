# TIER 0 — ACTION REQUIRED

## 1. GHCR package visibility (LIKELY PRIVATE — PULL_ERROR risk)

Anonymous pull test returned **404** on `v14` manifest. The package may still be **private**.

**You must verify in incognito:**
https://github.com/QuantumByte-01/amd-track2-captioner/pkgs/container/amd-track2-captioner

If not public → **Package settings → Change visibility → Public**

## 2. Update workflow (adds API-key guard + smoke test)

Edit `.github/workflows/build.yml` and replace with contents of:
`COPY_ME_TO_dot_github_workflows_build.yml` (updated with guard + smoke test)

This ships **v15+** that proves the baked key works inside the pulled image.

## 3. Submit to lablab NOW

If not submitted yet:
```
ghcr.io/quantumbyte-01/amd-track2-captioner:v14
```
After workflow update + new build:
```
ghcr.io/quantumbyte-01/amd-track2-captioner:v15
```
(or whatever run number succeeds with smoke test PASS in Actions logs)

## Tier 1 changes in this push (v15 code)

- Truncation: sentence-boundary only, regenerate once if over limit
- write.txt: calibrated to reference caption cadence (Ah yes / When you finally...)
- CANDIDATES=2 with batched judge re-enabled
