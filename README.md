# MOSS-Image on Runpod

MOSS-Image SFT with three curated ComfyUI workflows: BF16 photography, a smaller INT8 preset, and experimental latent img2img. Use the browser UI on a Pod or submit image jobs through the Runpod Hub queue API. Both use the same container and pinned model files.

**Release status:** source package prepared for release; a completed container build and fresh-volume GPU validation are required before publication. The planned registry image below has not been published. See [release steps](docs/release.md).

Source validation: **65 tests passed**, and Docker's configuration check passed. See [the validation record](docs/validation-status.md) for the checks still pending.

## Open the ComfyUI browser UI

After a maintainer publishes a tested image and Pod template:

1. Deploy the Pod template with one NVIDIA GPU with at least 24 GB VRAM, a CUDA 13.0-compatible host, 40 GB container disk, and a 60 GB persistent volume mounted at `/workspace`.
2. Set `MOSS_MODE=pod` and your own `MOSS_PASSWORD` of at least 12 characters before starting. There is no default password. Prefer a Runpod Secret for the password. Leave the image's start command unchanged.
3. Open the HTTP service on port **8188**. The same address shows preparation progress while models download. When prompted, sign in as **moss** with your configured password.
4. Open `/?template=photography-bf16&source=moss` on that service, enter a prompt, and run the graph. The **Workflows** panel also contains the bundled graphs.

Initial startup downloads and verifies **23.51 GB** across six public model files listed in the [pinned model manifest](config/models.json). It is not instant; download speed and the selected host determine preparation time. No Hugging Face token is required. Restarts reuse verified models on the attached volume. Retain that volume to preserve your files.

Port 22 is available for SSH using Runpod's configured SSH key. Expose the password-protected gateway on 8188 for ComfyUI; the internal service on `127.0.0.1:8189` stays private. Public health endpoints return readiness and startup phase. Detailed download progress requires login.

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

The Hub package is a **queue-based Serverless API**, with `MOSS_MODE=serverless`. It is separate from the interactive Pod template and does not expose the browser UI. A worker downloads the same six files on first boot; an ephemeral worker can need those downloads again after replacement. To retain models on a Serverless network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/moss`. Workers share that verified model cache while keeping their databases and job files in separate temporary workspaces.

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

Send this payload to `https://api.runpod.ai/v2/ENDPOINT_ID/run` using your Runpod API key in the Authorization header, then poll `https://api.runpod.ai/v2/ENDPOINT_ID/status/JOB_ID` for that job. The per-job execution limit is 600 seconds; cold worker preparation is separate. The Hub build test allows 1,200,000 milliseconds for its cold test. Use `/run` for jobs that can outlast a synchronous request.

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
├── deploy/pod-template.json      # Pod configuration; image publication pending
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
| `MOSS_PASSWORD` | Your own password of at least 12 characters; required in Pod mode |
| `MOSS_DATA_DIR` | Mutable data root; defaults to `/workspace/moss` |

The planned release image is `ghcr.io/akhilsivanand5000/moss-comfyui:0.1.0`. This namespace comes from the connected GitHub account. Build, test, and publish the image before using the Pod configuration. This repository contains no account-specific deployment, generated samples, private runtime data, or embedded credentials.

Packaging code is [MIT licensed](LICENSE). Model weights, ComfyUI, and upstream workflow material retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.txt).
