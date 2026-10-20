# MOSS-Image on Runpod

**Deploy → Connect → MOSS ComfyUI → choose a workflow.** Generate images in the browser or use the separate Runpod Hub queue API. Both use the same image and pinned MOSS-Image SFT models.

## Open ComfyUI

1. [Deploy the MOSS ComfyUI Pod](https://console.runpod.io/deploy?template=8m8mm2pkpw&type=gpu) with one supported NVIDIA GPU with at least 24 GB VRAM.
2. Open **Connect → MOSS ComfyUI**. Runpod signs you in through its connection link.
3. Wait for preparation to finish, choose a workflow, enter a prompt and queue an image.

No separate password, terminal command, model-download token or storage edit is needed for first use. The startup page shows the current phase, downloaded GB and percentage while **23.51 GB** of public model files download and verify. Startup depends on the host and network. One fresh Pod became ready in about **7 min 33 s**; another was confirmed ready by **18 min 55 s** after creation. These are two observations, not a timing guarantee. Later starts can reuse retained models.

## Choose a workflow

| Browser workflow | Starting settings | Use |
|---|---|---|
| SFT Photography — BF16 | 1216×1664, 25 steps, CFG 2.5, full FLUX.2 VAE | Direct photographic prompts |
| SFT Fast — INT8 + LoRAs | 1024×1024, 25 steps, CFG 2.5, small FLUX.2 VAE | Smaller diffusion checkpoint |
| Image variation — experimental | Approximately 1 MP, input aspect ratio, denoise 0.6 | Ordinary latent repainting |
| Official SFT — prompt enhancement | Official graph with its prompt enhancer | Expanded prompts in the browser |

The workflows share the Qwen3.5-9B W4A8 GPTQ text encoder. Photography and fast include two model-only LoRA slots: bundled SFT Destripe at **1.5**, then an optional compatible SFT adapter initially disabled. The default API approves only the bundled Destripe adapter; installing another adapter also requires adding it to the approved catalog.

These are starting settings, with no claim of universal image-quality superiority. Img2img is experimental latent repainting, not an instruction-edit-trained model. The official prompt-enhanced workflow is browser-only.

## Use the queue API

The [Runpod Hub listing](https://console.runpod.io/hub/listing/akhilsivanand/moss-runpod) is a **Serverless queue API**. Its availability depends on Runpod's build, tests and review. Deploy an available listing to create your own endpoint; the worker does not expose the browser editor. Use the Pod link above for ComfyUI.

Submit this small first test to `https://api.runpod.ai/v2/ENDPOINT_ID/run`, with `Authorization: Bearer YOUR_RUNPOD_API_KEY` and `Content-Type: application/json`:

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

Poll `/status/JOB_ID` on that endpoint for the returned job ID. A completed job contains:

```json
{
  "output": {
    "images": [{"type": "base64", "data": "BASE64_PNG_BYTES"}],
    "seed": 42,
    "preset": "fast"
  }
}
```

| Input | Accepted values |
|---|---|
| `prompt` | Required, nonempty text; at most 12,000 characters |
| `preset` | `photography` (default), `fast` or `img2img` |
| `seed` | Integer from 0 to 2⁶³−1; omitted means random |
| `width`, `height` | Multiples of 64; at least 64 per side; at most 2,097,152 pixels total |
| `steps`, `cfg` | 1–60 steps; CFG 0–10 |
| `image_base64` | Required for img2img: raw PNG/JPEG/WebP base64, without a data-URI prefix or URL |
| `lora_name`, `lora_strength` | Approved, installed SFT adapter basename for the second photography/fast slot; strength −2 to 2 |

API img2img center-crops/resizes to the requested dimensions, defaulting to 1024×1024, with denoise 0.6. It has no exposed LoRA slot. Input images are limited to 7 MiB decoded, 16 megapixels and 8192 pixels per side; the complete encoded request must also fit [Runpod's payload limit](https://docs.runpod.io/serverless/workers/handler-functions#payload-limits).

A cold API worker downloads the same model files. Two validated cold requests had **326 and 336 seconds of queue delay** before execution. Replacement workers can download them again; these observations are not a startup guarantee. Use asynchronous `/run` for long requests. Generation has a 600-second worker timeout after preparation; the Hub cold test allows 1,200,000 ms.

## Keep models and images

The template requests a **60 GB container disk**, sufficient for first use without a persistent attachment. To retain models, workflows and images after stopping the Pod, select persistent storage mounted at `/workspace` in Runpod Storage. The current launch screen selects storage separately, so the legacy template volume field alone does not guarantee retention. Preserve the volume when stopping; replacing or deleting a Pod requires storage that outlives that Pod.

For a Serverless network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/moss`. Workers can share the verified model cache while keeping databases and job files in separate temporary workspaces. Shared-cache concurrency has not been validated for this release.

## Startup and package layout

The startup script is included in the image at **`/opt/moss/scripts/entrypoint.sh`** and explicitly selected in the template's start-command field. It initializes Runpod SSH, starts the connection/progress page, prepares models and supervises ComfyUI. No external startup-script download is required. The image retains `tini` for process supervision.

Application files live under `/opt/moss`, ComfyUI under `/opt/comfyui` and Python under `/opt/venv`. Mutable Pod data lives under `/workspace/moss/{models,input,output,user,temp,state}`; mounting a workspace does not hide the installed application.

```text
Dockerfile / handler.py        Container build and queue SDK entry point
.runpod/                      Hub metadata, generation test and listing README
requirements/ / config/       Locked dependencies, model manifest and preset catalog
deploy/                       Pod template, explicit startup command and Connect settings
workflows/ui/ / workflows/api/ Browser graphs and executable graph exports
custom_nodes/moss/            Native workflow-template registration
src/moss_runtime/ / scripts/  Preparation, connection gateway, API and validation tools
docs/                         Release procedure and dated validation evidence
```

| Setting | Purpose |
|---|---|
| `MOSS_MODE` | `pod` for ComfyUI; `serverless` for queue jobs |
| `JUPYTER_PASSWORD` | Runpod supplies the native Connect token automatically |
| `MOSS_PASSWORD` | Optional legacy/custom login; use a unique password of at least 12 characters |
| `MOSS_DATA_DIR` | Mutable root; defaults to `/workspace/moss` |
| `MOSS_PUBLIC_ORIGIN` | Optional exact HTTP(S) origin for a custom domain, without a path |

ComfyUI is exposed through the authenticated **8888** gateway; Runpod SSH uses port 22. The internal ComfyUI service remains private. Standard Runpod origins are derived automatically.

The tested `0.1.1` image, exact runtime revision and completed checks are recorded in [validation status](docs/validation-status.md) and [validation.json](docs/validation.json). The public Pod template uses this tested image. The [release procedure](docs/release.md) separates image/template publication from Runpod Hub approval.

Packaging code is [MIT licensed](LICENSE). Model weights, ComfyUI and upstream workflows retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.txt).
