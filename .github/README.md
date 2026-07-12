# CI setup

GitHub Actions workflow files cannot be pushed via the current PAT (requires `workflow` scope).

## Add the build workflow (required once)

1. Open: https://github.com/QuantumByte-01/amd-track2-captioner/new/main/.github/workflows/build.yml
2. Copy the full contents of [`COPY_ME_TO_dot_github_workflows_build.yml`](../COPY_ME_TO_dot_github_workflows_build.yml) from the repo root
3. Paste into the editor and click **Commit changes**

The `FIREWORKS_API_KEY` secret is already configured. The build starts automatically after you commit.

## After build

- Make GHCR package **public**: GitHub profile → Packages → `amd-track2-captioner`
- Submit: `ghcr.io/QuantumByte-01/amd-track2-captioner:v1` (use actual run number from Actions)
