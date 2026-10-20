# MOSS-Image on Runpod

> **0.1.1 candidate:** a simpler **Deploy → Connect → choose a workflow** flow is under validation. The public `0.1.0` template remains unchanged. See [candidate status](docs/simple-launch.md).

MOSS-Image SFT with three curated ComfyUI workflows: BF16 photography, a smaller INT8 preset, and experimental latent img2img. Use the browser UI on a Pod or submit image jobs through the Runpod Hub queue API. Both use the same container and pinned model files.

**Release status — 2026-10-19:** image `0.1.0` is available. Pod and queue generation, browser workflows, and restart preservation pass; source CI passes 71 tests. The ComfyUI Pod template and [GitHub release](https://github.com/akhilsivanand/moss-runpod/releases/tag/v0.1.0) are public. [Hub submission](https://console.runpod.io/hub/listing/akhilsivanand/moss-runpod) is accepted; Runpod build/tests and manual approval are pending. See [validation details](docs/validation-status.md).

## Open the ComfyUI browser UI

The **0.1.1 candidate** reduces launch to three steps:

1. Deploy a Pod with one CUDA 13.0-compatible NVIDIA GPU with at least 24 GB VRAM.
2. Open **Connect → MOSS ComfyUI**. Runpod supplies its connection token automatically.
3. Wait for the preparation page to finish, then choose a workflow and enter a prompt.

The candidate requests a 60 GB container disk. No separate MOSS password, model-download token, terminal command, or storage edit is needed for first use. The preparation page shows phases, downloaded GB and percentage while the six pinned model files download and verify. Initial preparation transfers **23.51 GB**, so time depends on the selected host and download connection.

For models and images you want to keep after stopping or replacing the Pod, choose persistent storage mounted at `/workspace` in Runpod Storage. The current Runpod launch screen selects storage separately; the template's legacy volume setting alone does not guarantee a persistent attachment. Restarts reuse verified models when the data is retained.

The startup script is included in the image: [`scripts/entrypoint.sh`](scripts/entrypoint.sh), installed as **`/opt/moss/scripts/entrypoint.sh`**. The template explicitly selects that command and preserves the image's `tini` entry point. It initializes Runpod SSH and starts the supervised model preparation, connection page and ComfyUI services. The candidate makes the command explicit in the template's start-command field.

The candidate uses HTTP port **8888** for **MOSS ComfyUI** and port 22 for Runpod SSH. Its [Pod template](deploy/pod-template.json) and [console connection settings](deploy/pod-console.json) are a pair: the console must enable Runpod's native token-bearing Connect link. The internal ComfyUI service stays private.

The public [0.1.0 template](https://console.runpod.io/deploy?template=8m8mm2pkpw&type=gpu) still uses the earlier password-based setup on port 8188. It has not been replaced by this candidate. See [candidate validation and remaining gates](docs/simple-launch.md).

For a custom domain, set `MOSS_PUBLIC_ORIGIN` to its exact HTTP(S) origin, such as `https://comfy.example.com`, including a nondefault port if needed and no path.

## Choose a workflow

| Preset | Model and VAE | Default generation settings | Purpose |
|---|---|---|---|
| `photography` | SFT BF16, full FLUX.2 VAE | 1216×1664, 25 steps, `er_sde` / `simple`, CFG 2.5 | Photography starting point |
| `fast` | SFT INT8 ConvRot, small FLUX.2 VAE | 1024×1024, 25 steps, `er_sde` / `simple`, CFG 2.5 | Smaller diffusion checkpoint |
| `img2img` | SFT INT8 ConvRot, small FLUX.2 VAE | Approximately 1 MP preserving input aspect ratio, 25 steps, CFG 2.5, denoise 0.6 | Experimental latent repainting |

All presets share the Qwen3.5-9B W4A8 GPTQ text encoder. The photography graph has two model-only LoRA slots: SFT Destripe at **1.5**, then an optional compatible SFT adapter at **0**. Use only adapters that support this model and loading path. The [Destripe author](https://huggingface.co/nynxz/MOSS-Image) tested strength 1.5 at 1024; the approximately 2 MP photography size is an adaptation, not a validated strength-scaling rule.

The browser collection also includes the official prompt-enhanced graph. It is a UI-only workflow; the queue API accepts the three presets above.

These settings are starting points. Prompt, seed, subject, and adapters affect the result; this package makes no quality-superiority or generation-speed claim. Latent img2img is not an instruction-edit-trained model.

## Use the Hub API

The Hub package is a **queue-based Serverless API**, with `MOSS_MODE=serverless`; Hub submission is accepted and approval is pending. Once the listing is approved, deploy it to create your own endpoint. The worker does not expose the browser UI.

A worker downloads the same six files on first boot. One cold API job reported about **7 minutes of delay before execution**; this is one worker observation, and startup time varies with downloads and the host. Ephemeral workers may repeat the downloads after replacement. To retain models on a Serverless network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/moss`. Workers share that verified model cache while keeping their databases and job files in separate temporary workspaces.

Submit a job with a nonempty `prompt` and `preset` set to `photography`, `fast`, or `img2img`. For a small first test:

```json
{
  "input": {
    "preset": "fast",
    "prompt": "A ceramic coffee cup on a wooden table beside a window, natural morning light, realistic photograph.",
    "seed": 42,
    "width": 768,
    "height": 768,
    "steps": 25,
    "cfg": 2.5
  }
}
```

Send this payload to `https://api.runpod.ai/v2/ENDPOINT_ID/run` with `Authorization: Bearer YOUR_RUNPOD_API_KEY` and `Content-Type: application/json`, then poll `https://api.runpod.ai/v2/ENDPOINT_ID/status/JOB_ID` for that job. Replace the placeholders with your own endpoint, job, and key. The per-job execution limit is 600 seconds; cold worker preparation is separate. The Hub build test allows 1,200,000 milliseconds for its cold test. Use `/run` for jobs that can outlast a synchronous request.

The completed Runpod result contains this `output` structure:

```json
{
  "images": [{"type": "base64", "data": "BASE64_PNG_BYTES"}],
  "seed": 42,
  "preset": "fast"
}
```

| Input | Accepted values |
|---|---|
| `prompt` | Required, nonempty text, at most 12,000 characters |
| `preset` | `photography` (default), `fast`, or `img2img` |
| `seed` | Integer from 0 to 2⁶³−1; omitted means a random seed |
| `width`, `height` | Multiples of 64, at least 64 per side, at most 2,097,152 pixels in total |
| `steps`, `cfg` | 1–60 steps; CFG 0–10 |
| `image_base64` | Required for img2img: raw base64 PNG, JPEG, or WebP; no data-URI prefix or URL |
| `lora_name`, `lora_strength` | Optional second model-only slot for photography/fast; installed and deployment-approved SFT adapter basename, strength −2 to 2 |

The API img2img preset center-crops/resizes to the requested width and height, defaulting to 1024×1024; its denoise is fixed at 0.6. The browser graph instead preserves the input aspect ratio at approximately 1 MP. Img2img exposes no API LoRA slot. An image may contain at most 16 megapixels and 8192 pixels per side, with at most 7 MiB of decoded bytes; the entire encoded request must also fit [Runpod's request-size limits](https://docs.runpod.io/serverless/workers/handler-functions#payload-limits), including base64 expansion.

The default deployment's approved adapter list contains only the bundled Destripe file. The two default LoRA slots are already configured in the graph; specifying that same adapter again adds a second patch, so leave the optional slot unused unless intentionally testing it. A maintainer can add a compatible, licensed adapter to the deployment's model files and approved catalog. The API accepts preset parameters rather than arbitrary graphs, local paths, or model download URLs.

## Files and persistence

```text
.
├── Dockerfile                    # one image for Pod and Serverless modes
├── handler.py                    # Runpod queue SDK entry point
├── requirements/                 # pinned runtime environment and constraints
├── config/                       # model manifest and workflow catalog
├── .dockerignore                 # small, explicit build context
├── .runpod/
│   ├── hub.json                  # Hub metadata and Serverless settings
│   ├── tests.json                # real fast-preset generation test
│   └── README.md                 # Hub listing instructions
├── deploy/pod-template.json      # candidate Pod configuration and startup command
├── deploy/pod-console.json       # native Runpod Connect and SSH settings
├── docs/release.md               # build, validate, and publish gates
├── workflows/ui/                 # browser graphs
├── workflows/api/                # executable graph exports
├── custom_nodes/moss/            # bundled workflow-template registration
├── src/moss_runtime/             # preparation, persistence, gateway and API
└── LICENSE / THIRD_PARTY_NOTICES.txt
```

Application files are baked under `/opt/moss`, ComfyUI under `/opt/comfyui`, and the Python environment under `/opt/venv`. Mutable data lives under `/workspace/moss/{models,input,output,user,temp,state}`. A workspace mount therefore does not hide the installed application. User changes and older downloaded weights should be preserved; an upgraded volume may use more space than a fresh installation.

| Setting | Value |
|---|---|
| `MOSS_MODE` | `pod` for the browser; `serverless` for the queue worker |
| `JUPYTER_PASSWORD` | Runpod supplies this native Connect token; do not put a shared value in the template |
| `MOSS_PASSWORD` | Optional legacy/custom-deployment login; use a unique password of at least 12 characters |
| `MOSS_DATA_DIR` | Mutable data root; defaults to `/workspace/moss` |
| `MOSS_VOLUME_GB` | Optional capacity override for a known provisioned volume; the candidate uses detected free space |
| `MOSS_PUBLIC_ORIGIN` | Optional exact HTTP(S) origin for a custom domain; standard Runpod origin is derived automatically |

The published `0.1.0` image resolves to `sha256:4247e93d9fee317243f23713b5e55ec44e05f23a0cb41388599183b8789603ec`. Its [validation record](docs/validation.json) applies to that earlier runtime. The candidate deployment metadata is private and uses a staging tag until its own image and GPU checks pass; the old report does not validate it. See [the validation status](docs/validation-status.md). This repository contains no personal endpoints, generated samples, private runtime data, or embedded credentials.

Packaging code is [MIT licensed](LICENSE). Model weights, ComfyUI, and upstream workflow material retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.txt).
