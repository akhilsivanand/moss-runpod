# Release validation — 2026-10-19

This records completed release checks and remaining work. The final publication
report in `docs/validation.json` must be created from actual evidence after the
remaining Pod checks pass.

The results below are first-candidate evidence unless marked otherwise. Browser
testing found a gateway Host/Origin mismatch; a correction is in source, but its
replacement image has not yet been built or validated. Version 0.1.0 has not
been promoted or published as a release.

| Check | Result |
|---|---|
| First-candidate Python 3.11 suite with pinned aiohttp 3.14.5 and Pillow 13.0.0 | 68 passed; [source CI](https://github.com/akhilsivanand/moss-runpod/actions/runs/39234091302) |
| Corrected gateway origin tests | 6 passed |
| Updated full source suite | 71 passed |
| Model manifest, graph references, Hub/Pod metadata, and public source checks | Passed |
| Shell syntax and Python compilation | Passed |
| Docker BuildKit `docker build --check .` | Passed, no warnings |
| First-candidate Linux AMD64 image build | Passed; [container CI](https://github.com/akhilsivanand/moss-runpod/actions/runs/39234091053) |
| First-candidate dependency check and CPU startup/native-template smoke | Both passed |
| First-candidate public image and anonymous digest verification | Passed; immutable identity below |
| Corrected replacement image build and smoke | Pending |
| Private Pod template and fresh staging Pod | Created; initial model directory empty, CUDA 13.0 and SSH verified |
| First-candidate actual browser proxy-origin check | Failed: incoming Host/Origin mismatch; corrected in source |
| Corrected-image Pod GPU generation, browser/native routes, authentication, and restart | Pending |
| Fresh Serverless worker: fast 768×768, seed 42 | Completed with image |
| Fresh Serverless worker: photography 1216×1664, seed 424242 | Completed with image |
| Fresh Serverless worker: img2img 1024×1024, seed 43 | Completed with image |
| Serverless invalid blank prompt | Job failed as expected |
| First-candidate additional second-LoRA-slot generation | Passed; all four new API images inspected |
| Corrected-image queue generation | Pending |
| Shared-cache scaling and worker replacement | Pending |
| Public Pod template, GitHub release, and Hub submission/approval | Pending |

The tests cover download resumption, corruption recovery, capacity checks,
preservation of existing files and edited workflows, gateway authentication,
HTTP/WebSocket proxying, API input/output validation, scoped cancellation,
the asynchronous SDK handler, and worker workspace isolation. Their image jobs
use controlled test services; they do not establish GPU inference or quality.

The image uses the digest-pinned Runpod CUDA 13 base without a preinstalled
PyTorch stack. Its Python environment is separately locked with package hashes.
The first-candidate runtime revision is `4f4071f610a457fb168236383e021c4090765fe5`.
The following public digest requires the gateway correction before release:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:e537b3802e74ce6f560c3007cff039d392c8e91d8952ddf75a791241218a393b
```

Cold preparation was about 7.4 minutes on one Serverless worker. That single
observation is not a startup-time or generation-speed guarantee. An ephemeral
replacement worker may download all 23.51 GB again without persistent storage.
Queue inference confirms those tested execution paths; it does not establish
browser behavior, restart persistence, shared-cache scaling, or image-quality
superiority.

The corrected gateway derives the standard Runpod trusted origin automatically
from `RUNPOD_POD_ID`. A custom domain can set `MOSS_PUBLIC_ORIGIN` to its exact
HTTP(S) origin, including a nondefault port if needed and no path. Its real
browser HTTP/WebSocket behavior must pass on the corrected image.

The publication report is still pending. Follow [release.md](release.md), record
actual results in `docs/validation.json` using the schema in the checker, then
run `python scripts/check_release.py --publish`. A published image and successful
queue jobs do not by themselves complete Pod validation or Hub approval, and
first-candidate evidence is not proof for a replacement image.
