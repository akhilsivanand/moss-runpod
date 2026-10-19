# Release 0.1.0

The package has two delivery paths: an interactive ComfyUI Pod template and a queue-based Runpod Hub API. Both use the root Dockerfile. Completed checks are recorded below and in [validation-status.md](validation-status.md); remaining steps are publication gates.

## Current status

As of **2026-10-19**, [akhilsivanand/moss-runpod](https://github.com/akhilsivanand/moss-runpod) is public, GitHub publishing authorization is complete, and the maintainer's GitHub account is linked to Runpod. The first candidate's [source CI](https://github.com/akhilsivanand/moss-runpod/actions/runs/39234091302) passed 68 tests. Its [container build](https://github.com/akhilsivanand/moss-runpod/actions/runs/39234091053) and both in-image dependency/CPU-template checks passed. These results do not validate the corrected replacement image.

The first-candidate image is public and its digest was verified anonymously. It requires a gateway correction and is not the promoted 0.1.0 release:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:e537b3802e74ce6f560c3007cff039d392c8e91d8952ddf75a791241218a393b
```

The first candidate's tested runtime source is `4f4071f610a457fb168236383e021c4090765fe5`. A private Pod template and fresh staging Pod were created; an empty initial model directory, CUDA 13.0, and SSH were verified. Its [deployment link](https://console.runpod.io/deploy?template=8m8mm2pkpw&type=gpu) remains **private / replacement validation pending**; the final template ID may change.

On the first candidate's new Serverless endpoint, the primary suite completed fast at 768×768 (seed 42), photography at 1216×1664 (seed 424242), and img2img at 1024×1024 (seed 43). An additional second-LoRA-slot variant also passed, and all four new images were inspected. A blank-prompt job failed as expected. Cold preparation took about 7.4 minutes on one worker; this is not a startup-time guarantee.

Actual browser testing exposed an incoming Host/Origin mismatch. The gateway was corrected to validate the trusted origin derived from `RUNPOD_POD_ID`, or an explicitly configured `MOSS_PUBLIC_ORIGIN`. Six gateway tests and the full updated 71-test suite pass; the corrected image build is pending. Record its new source revision and digest when available.

Corrected-image Pod GPU generation, browser/native-template behavior, restart preservation, and queue verification remain pending. Promotion to `ghcr.io/akhilsivanand/moss-comfyui:0.1.0`, public Pod-template publication, a GitHub release, and Hub submission/approval have not occurred.

## Remaining release gates

- Build the corrected image, and repeat its dependency/CPU smoke and anonymous digest verification.
- Validate the corrected image through the actual browser, native templates, Pod generation, restart preservation, and queue endpoint. Update or replace the private template and staging resources as required.
- Test shared-cache scaling separately before claiming it is validated.
- Record the corrected image digest and runtime revision with actual GPU/driver/CUDA details and new-job results in the publication report; do not carry forward first-candidate passes as replacement-image proof.
- Run the publish gate, promote the tested Pod template, and create the GitHub release. Then submit to Hub for its build/tests and manual review. Describe each interface's actual state separately.

## 1. Prepare the repository

Publish this directory as the repository root: `Dockerfile`, `handler.py`, `README.md`, `.runpod/hub.json`, and `.runpod/tests.json` must be discoverable without a parent project. Keep the single root Dockerfile; no Hub-specific Dockerfile override is needed.

Review the source export and Docker build context. Include the curated graphs, pinned downloader/manifest, runtime, dependency lock, licenses, and checks. Exclude credentials, `.env` files, SSH keys, private deployment records, logs, history, generated images, model weights, virtual environments, and retired graphs. The six model downloads belong in the pinned runtime manifest, not Git or a developer's local cache.

Confirm that [the model manifest](../config/models.json) totals **23,509,579,072 bytes** across the six required files and verifies every revision, size, and SHA256. Confirm that model downloads work without credentials. Preserve upstream license files in the image and keep [third-party notices](../THIRD_PARTY_NOTICES.txt) with the exported graphs. The original application and bundled upstream components retain separate licenses.

Use the current official [Hub publishing guide](https://docs.runpod.io/hub/publishing-guide), [template API schema](https://docs.runpod.io/api-reference/templates/POST/templates), and [Pod template guide](https://docs.runpod.io/pods/templates/manage-templates) when submitting. `.runpod` files override root files on the Hub. The Hub indexes GitHub releases, not individual commits; later releases trigger new builds and tests.

## 2. Build one image

Run the source checks with Python 3.11:

```sh
python -m pip install -r requirements/test.txt
python -m pytest -q
python scripts/check_release.py
docker build --check .
```

The namespace uses the connected GitHub account. Run from this repository root:

```sh
docker build --platform linux/amd64 --tag ghcr.io/akhilsivanand/moss-comfyui:candidate .
docker run --rm --entrypoint /opt/venv/bin/python ghcr.io/akhilsivanand/moss-comfyui:candidate -m moss_runtime.bootstrap --check-package
docker run --rm --entrypoint /opt/venv/bin/python ghcr.io/akhilsivanand/moss-comfyui:candidate /opt/moss/scripts/smoke_container.py
```

The image must contain `/opt/comfyui`, `/opt/venv`, and `/opt/moss`. It must not depend on pre-existing `/workspace` application files. Inspect the final image for the pinned environment, upstream sources/licenses, required model nodes, and the intended entry point. Source-only checks do not establish that a container can start or generate an image.

The image checks require no model download or GPU. The second starts ComfyUI on CPU in a temporary workspace, checks its actual node schemas and template catalog, then cleans up. GPU generation still requires the staging tests below.

## 3. Test the interactive Pod on a fresh volume

Create the template privately, then launch the fresh staging Pod from that exact template; publish the same template after verification. Use one 24 GB NVIDIA GPU and a host supporting CUDA 13.0. The image's quantized kernels require that host support; GPU memory alone is insufficient. Start with an empty 60 GB volume mounted at `/workspace`, 40 GB container disk, `MOSS_MODE=pod`, `MOSS_VOLUME_GB=60`, and a newly configured `MOSS_PASSWORD` of at least 12 characters. Set `MOSS_VOLUME_GB` to the actual provisioned decimal-GB size whenever the volume is resized. Expose only 8188/http and 22/tcp.

Verify preparation status during first boot; all six model files must download, hash-check, and reach readiness without a model token. Check that requests for the browser, graph API, outputs, and WebSocket require authentication, while public startup health/status reveals only sanitized preparation information. Confirm that an empty password prevents exposure of an unprotected UI. Confirm that Runpod SSH initialization still works with a configured public key.

For standard Runpod access, the corrected gateway derives the trusted public origin automatically from `RUNPOD_POD_ID`. For a custom domain, set `MOSS_PUBLIC_ORIGIN` to the exact HTTP(S) origin, such as `https://comfy.example.com`, including a nondefault port if applicable and no path. Verify actual browser HTTP and WebSocket traffic through that origin; CPU node-schema checks do not exercise proxy origin handling.

Log in as `moss`. Open `/?template=photography-bf16&source=moss` and each bundled workflow through the actual browser frontend. Submit new authorized jobs for photography, fast, and img2img; record the returned identifiers and observe only those jobs' events and outputs. Check the expected output dimensions, actual nonzero Destripe patches, and images. Do not inspect unrelated logs, global history, prior prompts, or existing user outputs.

On the fresh staging Pod, the bundled helper can run the three preset jobs against its internal ComfyUI service:

```sh
/opt/venv/bin/python /opt/moss/scripts/validate_gpu.py --run --output-dir /workspace/moss/validation/fresh-image-smoke-01
```

Use a new output directory each time. It saves only those jobs' returned images and a record with hardware details, dimensions, checksums, and client elapsed times. Run without `--run` to inspect the plan without GPU work. This supplements the actual browser, Serverless SDK, and restart checks; its record alone is not the final publication report.

Change a user workflow, add a small test input and an output, then restart with the same volume. Verify that these task-created files survive, the user-edited workflow is preserved, models are reused, and the new image's application remains available under `/opt`. Confirm that existing older weights are preserved. Record cold preparation and actual inference separately; cached execution is not an inference benchmark.

## 4. Test the queue API

Deploy the same built image in Serverless staging with `MOSS_MODE=serverless`, 60 GB container disk, one 24 GB NVIDIA GPU, and CUDA 13.0 host compatibility. Use the queue SDK entry point in root `handler.py`; do not set `endpointType: "LB"` or expose the Pod UI for this listing.

Run the exact `.runpod/tests.json` fast test from a cold worker. Its input is the raw job input object; Runpod wraps it in `input` when submitting the job. Its timeout is **1,200,000 ms** to allow preparation. Verify a completed job contains a decodable 768×768 image, seed 42, and preset `fast`; a 200 HTTP response alone is not enough. Then verify photography and img2img through their advertised API inputs. Verify invalid prompts/presets and timeout handling return meaningful job failures. The intended per-job generation limit is **600 seconds** after initialization.

Test worker replacement and document whether the selected endpoint storage retains models. For a network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/moss`. Verify two workers can use the shared cache while retaining separate temporary databases and job directories. Without persistent storage, a replacement worker can download all 23.51 GB again. Measure cold starts on the released image before advertising them.

## 5. Publish the container and Pod template

The first candidate is already public, but its gateway defect prevents promotion. Publish the corrected candidate, verify it anonymously, and complete the staging checks before promoting that exact tested digest to `:0.1.0`. A local candidate build can be pushed for staging with:

```sh
docker push ghcr.io/akhilsivanand/moss-comfyui:candidate
```

Record the corrected immutable digest and replace the first-candidate pin in `deploy/pod-template.json` before final validation. A public repository alone does not make a new GHCR package public; see [GitHub's package visibility instructions](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility). The JSON uses the [Runpod REST template schema](https://docs.runpod.io/api-reference/templates/POST/templates). Leave its empty password as a per-user setup requirement; do not publish a shared password. Leave the image's entry point and start command intact.

The current template is private and its real deployment link is labeled pending in the README. Finish its fresh-volume generation, readiness/authentication, browser, and restart checks before setting visibility to public. Then remove the private/pending label. Do not add a badge that implies an approved Hub listing.

## 6. Submit the Hub release

Record completed staging results in `docs/validation.json` using the schema documented in `scripts/check_release.py`, resolve the registry identity, then run `python scripts/check_release.py --publish`. This checks the report's structure; keep the actual test evidence. Do not fill the report with assumed passes.

Ensure `.runpod/hub.json` selects GPU execution, 60 GB disk, `ADA_24`, one GPU, CUDA 13.0, and `MOSS_MODE=serverless`. Ensure its tests match the released handler. The current metadata intentionally describes a queue API; the interactive Pod is a separate template.

Create the `v0.1.0` GitHub release from the tested source commit. Sign in to the [Runpod Hub console](https://console.runpod.io/hub), choose **Add your repo → Get Started**, supply the actual GitHub URL, and follow the guided configuration. This is the documented submission route; creating a template through the REST template API does not itself submit or approve a Hub listing.

Runpod builds and tests the release, then its team manually reviews it. Record the submission's actual status and keep it described as pending until approval is confirmed. No approval time is promised by the publishing guide. A pushed image or GitHub commit alone is not an approved Hub listing. Keep the listing description clear about first-boot downloads and experimental img2img. Add the real Hub deployment badge only after approval.

For Hub creator credits, link the maintainer's GitHub profile to the Runpod account, obtain approval for the published repository, and maintain working releases. Revenue tiers reset monthly across published repositories: below 100 compute hours earns 0%; 100–999 earns 1%; 1,000–4,999 earns 3%; 5,000–9,999 earns 5%; and 10,000 or more earns 7% of compute revenue. Credits are deposited during the first week of the following month. These are Runpod credits, not a paid-template checkout or cash payout. See [the current revenue program](https://docs.runpod.io/hub/revenue-sharing) before making revenue claims.

The separate [Pod creator program](https://docs.runpod.io/accounts-billing/referrals#runpod-creator-program) pays 1% in Runpod credits after the template accumulates at least one day of combined runtime. Do not assume that the Pod and Hub programs stack for a single deployment.
