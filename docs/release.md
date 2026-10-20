# Releasing MOSS-Image 0.1.1

One immutable image serves two interfaces: the authenticated ComfyUI Pod and the separate Serverless queue API. Publish only after checks for that exact image and runtime pass. The full four-workflow browser retest after restart passed. See validation status for current publication state. GitHub publication and a public Pod template do not establish Runpod Hub approval.

## Package and image

Keep a single root `Dockerfile` and root `handler.py`, with Hub files in `.runpod/{hub.json,tests.json,README.md}`. Exclude credentials, deployment journals, logs, generated images, model weights and virtual environments from Git, build context and release archives.

With Python 3.11, run:

```sh
python -m pip install -r requirements/test.txt
python -m pytest -q
python scripts/check_release.py
docker build --check .
```

Build Linux AMD64 in the container workflow, run both mandatory in-image CPU gates and verify the exact manifest anonymously after push. The application belongs under `/opt/moss`, ComfyUI under `/opt/comfyui` and Python under `/opt/venv`; `/workspace` holds mutable data. Preserve upstream license notices. The entry point is `/usr/bin/tini --`; CMD is `/opt/moss/scripts/entrypoint.sh`.

The built, GPU-tested 0.1.1 image is:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:816f8e002989b700678f2efc53c3dc08e799a69f2b61079e1c80d1406be792c1
```

Runtime source is `0bf51872c7b9350a40f96cd8295d318bcef8b181`. Record a later packaging/documentation revision separately. The image is 3,747,665,350 compressed bytes; the six pinned model files total 23,509,579,072 bytes. Neither source-only checks nor historical 0.1.0 GPU results validate this image.

## Pod checks

Use a private template derived from [`pod-template.json`](../deploy/pod-template.json) and [`pod-console.json`](../deploy/pod-console.json). Keep the image digest pinned, container disk 60 GB, gateway 8888/SSH 22, explicit startup CMD and enabled native connection setting. Runpod must generate the token; do not publish a shared password.

Validate a fresh first launch without a persistent volume: actual **Connect → MOSS ComfyUI**, platform token exchange, clean URL, visible download phases/progress and readiness. Check unauthenticated UI/API/images/WebSocket, valid sessions and foreign-origin rejection through the public proxy. Verify configured SSH still works. Preserve user restrictions on logs and content.

On a fresh persistent `/workspace` attachment, run only newly authorized photography, fast and img2img jobs. Verify images, dimensions, seeds and checksums. Import all four browser workflows, including nested-subgraph serialization, and actually execute the official prompt-enhanced path. A successful import alone is insufficient.

The bundled helper submits three new preset jobs to a task-owned staging Pod:

```sh
/opt/venv/bin/python /opt/moss/scripts/validate_gpu.py --run --output-dir /workspace/moss/validation/fresh-image-smoke-01
```

Use a new output directory. For restart validation, record task-created workflow/input/output hashes, six model inode/mtime/size records and the baked application identity. Restart with retained storage; compare records and repeat health/browser HTTP/WebSocket checks. Do not restart unrelated user Pods. Leave the final working Pod running when requested.

## Queue API checks

Use the same immutable image, `MOSS_MODE=serverless`, one 24 GB GPU and a 60 GB disk. The validation endpoint used min 0, max 1, idle timeout 30 seconds and a CUDA host minimum of 13.0. Current stock may support 13.2; verify actual hardware/driver compatibility before promotion rather than requiring unavailable exact host versions.

Submit the exact `.runpod/tests.json` input through the SDK to a fresh cold endpoint. Verify a 768×768 PNG, seed 42 and preset `fast`. Also exercise photography 1216×1664, img2img using only that new fast image, a nonzero approved second LoRA and empty-prompt rejection. Observe only these jobs, never unrelated logs/history. Keep preparation queue delay separate from execution time.

These five 0.1.1 API checks passed via Runpod SDK 1.12.0; four images were verified and inspected. Two cold delays were 326,179 and 336,267 ms. The 600-second generation timeout begins after preparation; the Hub cold-test timeout is 1,200,000 ms. The disposable endpoint/source template were deleted and 404 verified after testing; existing published API resources were left unchanged.

A persistent Serverless cache at `/runpod-volume` can use `MOSS_DATA_DIR=/runpod-volume/moss`, while each worker keeps isolated databases/job files. Shared-cache concurrency has not been exercised; validate before claiming it. Without a retained cache, replacement workers can download all 23.51 GB again.

## Publish and verify

Record completed 0.1.1 evidence in [`validation.json`](validation.json): source revision, exact digest, hardware/driver, jobs with seeds/dimensions/image SHA256, browser/auth checks and restart preservation. Exclude prompts, credentials, resource/job IDs, private paths and generated images. Archive the older report as [`validation-0.1.0.json`](validation-0.1.0.json).

Run the fail-closed publication gate:

```sh
python scripts/check_release.py --publish
```

Promote the **same tested manifest** to `:0.1.1`; verify anonymous access and digest identity. Update public template 8m8mm2pkpw to that exact image and verify its explicit start command, 8888 **MOSS ComfyUI** label, native connection setting, storage defaults and README. Test the actual public deploy path. Do not point users at untested mutable staging tags.

Package the final source with the repository helper and validate the extracted archive. Publish GitHub `v0.1.1` from the final packaging commit with its source ZIP, SHA256 file and public validation report; download public assets and verify their exact bytes. Apply the final README/status only after the corresponding publication actions succeed.

Submit the release through normal [Runpod Hub publishing](https://docs.runpod.io/hub/publishing-guide). Check its actual build, test, listing and review state; record any failure accurately. Submission acceptance, image build and template visibility are separate from manual approval. Do not claim approval while pending.

Creator rewards depend on Runpod's current program and approval. The [revenue-sharing program](https://docs.runpod.io/hub/revenue-sharing) awards Runpod credits; there is no guaranteed income or cash template sale.
