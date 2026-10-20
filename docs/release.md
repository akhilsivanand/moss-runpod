# Releasing MOSS-Image 0.1.2

Version 0.1.2 corrects the Pod workspace to `/workspace/ComfyUI`, exposes `models/loras` where users expect it and aliases the installed application's model directory to that same tree. One image serves the authenticated ComfyUI Pod and the separate Serverless queue API. Runtime validation has passed. The stable image and public Pod template are published and independently verified; Hub submission remains held until the GitHub release assets are verified.

## Package and image

Keep a single root `Dockerfile` and root `handler.py`, with Hub files in `.runpod/{hub.json,tests.json,README.md}`. Exclude credentials, deployment journals, logs, generated images, model weights and virtual environments from Git, build context and release archives.

With Python 3.11, run:

```sh
python -m pip install -r requirements/test.txt
python -m pytest -q
python scripts/check_release.py
docker build --check .
```

The 0.1.2 source suite passed 89 tests; the Linux AMD64 image build, both in-image CPU gates, anonymous image verification and fresh GPU/dependency preflight passed. The exact image is:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:21cde4857330e4bd5f8660dc95a89a85c358c79fbac77e2c08f0e80004729671
```

Runtime source is `a14d011be32b86447a06c88531f0c334b9b86f08`. Record later packaging/documentation revisions separately. The six pinned public model files total 23,509,579,072 bytes. Historical 0.1.0/0.1.1 execution results do not validate this changed image.

The separate [container-layout CPU check](https://github.com/akhilsivanand/moss-runpod/actions/runs/39424748372) passed against that exact image with no persistent mounts. It checked baked-file preservation, the canonical model directory, alias fixture visibility and helper idempotence on Docker's overlay filesystem. GPU generation and restart results below come from the fresh Pod with its attached volume.

Application code belongs under `/opt/moss`, ComfyUI under `/opt/comfyui` and Python under `/opt/venv`. Pod mutable data belongs under `/workspace/ComfyUI`; `/opt/comfyui/models` must point to `/workspace/ComfyUI/models`. Preserve upstream licenses. The entry point is `/usr/bin/tini --`; CMD is `/opt/moss/scripts/entrypoint.sh`.

## Layout and existing-volume checks

Verify the real canonical directory, the installed model alias and LoRA discoverability at `/workspace/ComfyUI/models/loras`. Preserve uploaded adapters, edited workflows, inputs and outputs. For a recognized legacy workspace, record task-file SHA256 values and model inode/size/mtime before migration, then verify them afterward. If both roots exist or different same-name files conflict, preserve them and stop rather than merging or overwriting.

The existing Pod upgrade passed eight task-file hash checks, six model inode/size/mtime checks and uploaded-adapter preservation. Its canonical root and alias were verified, with the old managed root absent. All four native workflows opened afterward and both bundled and uploaded adapter choices were visible. Exactly one real Run-button generation passed after an idle-count check; it used bundled Destripe and produced a verified 1024×1024 PNG.

## Fresh Pod gate

Use a private template derived from [`pod-template.json`](../deploy/pod-template.json) and [`pod-console.json`](../deploy/pod-console.json). Keep the image digest pinned, container disk 60 GB, gateway 8888/SSH 22, explicit startup CMD and native connection setting. Runpod must generate the token; never publish a shared password.

Validate **Connect → MOSS ComfyUI**, token exchange, clean URL, progress and readiness on the changed image. Verify configured SSH, unauthenticated UI/API/images/WebSocket, valid sessions and foreign-origin rejection through the public proxy. Test the upgraded Pod's browser flow as well. Observe only authorized new jobs and outputs, respecting restrictions on user logs, history and existing content.

On fresh persistent storage at `/workspace`, run new photography, fast and img2img jobs. Verify dimensions, seeds and image checksums. Import all four native workflows, including nested-subgraph serialization, and execute the official prompt-enhanced path. A successful import alone is insufficient.

The bundled helper submits three new preset jobs:

```sh
/opt/venv/bin/python /opt/moss/scripts/validate_gpu.py --run --output-dir /workspace/ComfyUI/validation/fresh-image-smoke-01
```

Use a new output directory. Record task-created workflow/input/output hashes, six model stat records and baked application hashes before a same-volume restart. Verify a new process, preserved data, readiness and browser HTTP/WebSocket behavior afterward. Leave the final working Pod running when requested.

The fresh 0.1.2 Pod passed fast, photography and img2img generation, all four native imports and a new prompt-enhanced job with uncached TextGenerate execution. Its first readiness observation was **1,119.0 seconds after the deployment response**, excluding allocation time before that response. A same-volume restart preserved eight task-file hashes, six model inode/size/mtime records and two application hashes, with a new container process. All four native imports and authenticated browser POST/WebSocket checks passed after restart. These results validate execution and preservation; they are not speed or aesthetic guarantees.

## Queue API gate

Use the same immutable image, `MOSS_MODE=serverless`, one 24 GB GPU and 60 GB disk. The fresh test used min 0, max 1, idle timeout 30 seconds and a CUDA host minimum of 13.0. Verify the actual worker image and GPU metadata; do not substitute requested configuration for observed configuration.

Run the exact `.runpod/tests.json` fast input, photography 1216×1664, img2img using only the new fast image, a nonzero approved second LoRA and empty-prompt rejection. Submit each following case promptly to avoid idle shutdown. Separate queue/preparation delay from execution time.

All five 0.1.2 cases passed through Runpod SDK 1.12.0. Four returned PNGs were decoded, hashed, seed-checked and viewed. The first cold queue delay was 206,571 ms; later generation jobs queued in 139–158 ms. The disposable endpoint/source template were deleted and 404 verified, and existing API resources were unchanged. These measurements are observations, not performance guarantees.

The default model cache is `/workspace/ComfyUI`; each Serverless worker keeps its own temporary database, input/output directories and runtime lock. A network cache mounted at `/runpod-volume` can use `MOSS_DATA_DIR=/runpod-volume/ComfyUI`. Shared-cache concurrency remains untested. Ephemeral replacement can download all 23.51 GB again. Generation has a 600-second worker timeout after preparation; the Hub cold test allows 1,200,000 ms.

## Publish and verify

Record completed 0.1.2 evidence in [`validation.json`](validation.json): exact source/image identity, hardware/driver, layout migration, jobs with seeds/dimensions/image SHA256, browser/auth checks and restart preservation. Exclude prompts, credentials, resource/job IDs, private paths and generated images. Keep the [0.1.0](validation-0.1.0.json) and [0.1.1](validation-0.1.1.json) reports historical.

Run the fail-closed publication gate only when the required new-image checks are complete:

```sh
python scripts/check_release.py --publish
```

Promote the **same tested manifest** to `:0.1.2`; verify anonymous access and digest identity. Update public template 8m8mm2pkpw to that exact image, then verify its startup command, native Connect settings, standard directories, storage defaults and README. Test the public deployment path. A public older template is not proof that the corrected release has been promoted.

Package the final source, validate the extracted archive and publish GitHub `v0.1.2` with the source ZIP, SHA256 file and public report. Download public assets and verify their bytes. Record the packaging commit separately from the tested runtime revision.

Resume normal [Runpod Hub publication](https://docs.runpod.io/hub/publishing-guide) only after release verification. Check actual build, test, listing and review state. Submission, image publication and manual approval are separate steps; approval remains external. The [revenue-sharing program](https://docs.runpod.io/hub/revenue-sharing) awards Runpod credits and guarantees no earnings.
