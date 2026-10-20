# Release 0.1.1 candidate

This candidate simplifies the ComfyUI Pod launch to **Deploy → Connect → choose a workflow**, using Runpod's own connection token and visible preparation progress. The queue-based Hub API remains a separate delivery path in the same image.

The public Pod template and GitHub release remain on `0.1.0`. The candidate image build, actual platform Connect flow, fresh GPU generation and restart checks must pass before replacement. [Candidate status](simple-launch.md) records the remaining checks. [`validation.json`](validation.json) records only the earlier `0.1.0` runtime and must not validate this candidate.

## Source and image gates

Keep one root `Dockerfile` and root `handler.py`. Publish this directory as the repository root so Runpod can discover those files and `.runpod/{hub.json,tests.json,README.md}`. Do not include credentials, local deployment records, logs, generated images, weights or virtual environments in Git, the Docker context or the release archive.

Run the checks with Python 3.11:

```sh
python -m pip install -r requirements/test.txt
python -m pytest -q
python scripts/check_release.py
docker build --check .
docker build --platform linux/amd64 --tag ghcr.io/akhilsivanand/moss-comfyui:candidate .
docker run --rm --entrypoint /opt/venv/bin/python ghcr.io/akhilsivanand/moss-comfyui:candidate -m moss_runtime.bootstrap --check-package
docker run --rm --entrypoint /opt/venv/bin/python ghcr.io/akhilsivanand/moss-comfyui:candidate /opt/moss/scripts/smoke_container.py
```

Confirm that the image contains `/opt/moss`, `/opt/comfyui`, `/opt/venv` and upstream licenses independently of `/workspace`. Its entry point is `/usr/bin/tini --`; its startup command is `/opt/moss/scripts/entrypoint.sh`. The candidate template makes that command explicit. CPU checks establish package and node-schema compatibility, not GPU execution.

The pinned model manifest contains six public files totaling **23,509,579,072 bytes**. Verify immutable revisions, sizes and SHA256 values without a download token. Preserve each component's license and the package's third-party notices.

## Fresh Pod gate

Create a private template from [`deploy/pod-template.json`](../deploy/pod-template.json) and apply the native connection settings in [`deploy/pod-console.json`](../deploy/pod-console.json). Use a CUDA 13.0-compatible NVIDIA GPU with at least 24 GB VRAM, 60 GB container disk and HTTP port 8888 plus SSH port 22. Runpod must supply the native connection token through its enabled Connect/Jupyter setting. The template must not require a manual password or capacity environment variable.

Deploy once without a persistent attachment to confirm first use does not require storage edits. Verify the actual native **Connect → MOSS ComfyUI** link, token exchange and clean URL. Observe the preparation page before models are ready, including accurate transfer totals and bounded public status information. Check authentication on the UI, graph API, images and WebSocket; foreign origins must be rejected. Confirm configured Runpod SSH still works.

For persistence validation, attach fresh persistent storage at `/workspace`. Submit only newly authorized test jobs for photography, fast and img2img, and record their dimensions and image checksums. Verify actual nonzero Destripe patches and the official prompt-enhanced graph through the browser. Observe only these jobs' events and outputs; do not inspect user logs, unrelated history or prior images.

The bundled GPU helper can submit the three preset jobs to a task-owned staging Pod:

```sh
/opt/venv/bin/python /opt/moss/scripts/validate_gpu.py --run --output-dir /workspace/moss/validation/fresh-image-smoke-01
```

Use a new output directory. This helper supplements actual browser, API and restart checks; its output alone is not a publication report. Edit one task-created workflow and add test input/output files, then restart with the same volume. Verify those files, model metadata and baked application hashes are preserved. Do not restart the user's stopped Pod for this check.

The standard public origin is derived from trusted Runpod identity and the active gateway port. A custom domain may set `MOSS_PUBLIC_ORIGIN` to its exact HTTP(S) origin. Test browser HTTP and WebSocket traffic through the actual proxy; direct loopback tests do not cover that path.

## Queue API gate

Deploy the same immutable image as a private Serverless worker with `MOSS_MODE=serverless`, one 24 GB GPU, CUDA 13.0 host compatibility and 60 GB disk. This is a queue API, not a load-balanced UI service.

Run the exact `.runpod/tests.json` fast input on a cold worker and verify a decodable 768×768 image, seed 42 and preset `fast`. Then verify photography, img2img, an optional approved second-LoRA slot and meaningful rejection of invalid input. The Hub test allows 1,200,000 ms for cold preparation; actual generation is limited to 600 seconds after initialization. Record preparation separately from inference.

For a shared network volume at `/runpod-volume`, `MOSS_DATA_DIR=/runpod-volume/moss` retains the verified model cache while worker job files and databases remain isolated. Test concurrency and worker replacement before claiming those storage paths have been validated. Ephemeral replacement can download all 23.51 GB again.

## Publication gate

Record the candidate's own tested source commit, immutable image digest, hardware, completed jobs, authentication and restart checks in the public validation report. Include no prompts, credentials, Pod IDs, private paths or generated images. Run:

```sh
python scripts/check_release.py --publish
```

The gate requires a digest-pinned Pod image matching the GPU report; a staging tag plus historical report is insufficient. Promote the exact tested manifest to `:0.1.1`, verify anonymous access and digest identity, then publish the same already-tested Pod template. GitHub repository visibility does not establish GHCR package visibility.

Create a GitHub `v0.1.1` release from the final packaging commit with the checked source archive, checksum and public validation report. Record the tested runtime separately if a final documentation commit follows it. Update public READMEs with the actual release, template and validation status only after the actions succeed.

Submit through [Runpod Hub](https://console.runpod.io/hub) following its [publishing guide](https://docs.runpod.io/hub/publishing-guide). Hub indexes GitHub releases and then builds, tests and manually reviews them. Template publication and a successful build do not establish Hub approval; keep the status pending until Runpod confirms the listing is approved.

## Published 0.1.0 baseline

The earlier release validated runtime `37236a8e329d51adf2591c197a678f437650cebc` and image `sha256:4247e93d9fee317243f23713b5e55ec44e05f23a0cb41388599183b8789603ec`. Its 71 source tests, fresh Pod/API generation, four native workflows, prompt enhancement, browser security and restart checks passed. See [the historical report](validation.json) and [validation status](validation-status.md) for scope. That evidence applies to 0.1.0 only.

Creator rewards depend on Runpod's current program and approval. The [Hub revenue-sharing program](https://docs.runpod.io/hub/revenue-sharing) awards Runpod credits rather than a cash template sale; no earnings are guaranteed.
