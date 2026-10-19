# Preparation checks — 2026-10-19

This is a source preparation record. It is not the GPU evidence report required
for publication.

| Check | Result |
|---|---|
| Python 3.11 tests with pinned aiohttp 3.14.5 and Pillow 13.0.0 | 65 passed |
| Model manifest, graph references, Hub/Pod metadata, and public source checks | Passed |
| Shell syntax and Python compilation | Passed |
| Docker BuildKit `docker build --check .` | Passed, no warnings |
| Full final image build | Pending |
| CPU startup and native template serving inside the built image | Pending; smoke script supplied |
| Fresh-volume Pod generation, authentication, and restart | Pending |
| Fresh Serverless worker generation and shared-cache scaling | Pending |
| Public image, Pod template, GitHub release, and Hub submission | Pending |

The tests cover download resumption, corruption recovery, capacity checks,
preservation of existing files and edited workflows, gateway authentication,
HTTP/WebSocket proxying, API input/output validation, scoped cancellation,
the asynchronous SDK handler, and worker workspace isolation. Their image jobs
use controlled test services; they do not establish GPU inference or quality.

The final image uses the digest-pinned Runpod CUDA 13 base without a preinstalled
PyTorch stack. Its Python environment is separately locked with package hashes.
The full image and its smoke script still need execution on a build host.

`python scripts/check_release.py --publish` currently fails because no completed
GPU report exists. Follow [release.md](release.md), then record actual results
in `docs/validation.json` using the schema in the checker. The planned registry
and repository names are preparation settings, not evidence of publication.
