# MOSS-Image SFT API

Generate images through Runpod's **Serverless queue API** with BF16 `photography`, INT8 `fast` and experimental latent `img2img`. For the browser editor, use the separate [ComfyUI Pod](https://console.runpod.io/deploy?template=8m8mm2pkpw&type=gpu): **Deploy → Connect → MOSS ComfyUI → choose a workflow**.

Version **0.1.2** corrects the Pod layout to `/workspace/ComfyUI`. Upload compatible browser LoRAs to **`/workspace/ComfyUI/models/loras`** (plural). `/opt/comfyui/models` points to the same model tree, so the installed application's `models/loras` path sees those files too. Refresh the model list or reload the editor after an upload. API adapters also need to be in the deployment's approved catalog.

Deploy an available Hub listing to create your own API endpoint. Use one supported NVIDIA GPU with at least 24 GB VRAM and a **60 GB container disk**. The worker runs with `MOSS_MODE=serverless` and Runpod API authentication. No model-download token is required. Runtime validation has passed; publication of the corrected release is pending, and Hub submission remains held until publication verification.

Send this body to `https://api.runpod.ai/v2/ENDPOINT_ID/run`, with `Authorization: Bearer YOUR_RUNPOD_API_KEY` and `Content-Type: application/json`:

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

Poll `/status/JOB_ID` on your endpoint for the returned job ID. Completed jobs return base64 PNG bytes in `output.images`, plus `output.seed` and `output.preset`. A nonempty prompt is required. Generation is limited to 600 seconds after preparation; the Hub cold test allows 1,200,000 ms.

First startup downloads and verifies **23.51 GB** of pinned public model files. The fresh 0.1.2 API test had **206.571 seconds of queue delay** before its first execution. Later generation tests queued in 139–158 ms. These observations are not startup guarantees; ephemeral replacement workers can download models again.

Serverless keeps the model cache separate from each worker's temporary database, inputs, outputs and runtime lock. The default cache root is `/workspace/ComfyUI`. For a network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/ComfyUI` to retain that cache. Shared-cache concurrency has not been validated.

`photography` defaults to 1216×1664, 25 steps and CFG 2.5. `fast` defaults to 1024×1024 with the same steps/CFG. Both include Destripe and an optional second compatible SFT LoRA slot. The default API approves only the bundled Destripe file; specifying it again adds a second patch. Other adapters require compatible installed weights and an updated approved catalog.

For `img2img`, provide `image_base64` as raw PNG/JPEG/WebP base64 without a data-URI prefix or URL. The API center-crops/resizes to the requested dimensions, defaulting to 1024×1024 with denoise 0.6. Use at most 7 MiB decoded and respect the complete encoded request limit. This is experimental latent repainting and exposes no API LoRA slot. The official prompt-enhanced graph is browser-only.

**0.1.2 validation:** 89 source tests, both image CPU gates and fresh GPU/dependency preflight passed. A fresh RTX 4090 queue endpoint passed all three presets, a second bundled LoRA and empty-prompt rejection through Runpod SDK 1.12.0. Four new PNGs were decoded, hashed and inspected; the disposable resources were deleted and 404 verified. The existing Pod's layout upgrade preserved eight task-created file hashes, six model records and the uploaded adapter, with the canonical directory, model alias and LoRA chooser verified. A real browser Run-button job passed. A separate fresh Pod passed all three GPU presets, all four native workflow imports, prompt enhancement and same-volume restart preservation; all four imports passed again after restart. Earlier release results remain historical.

See the repository's [current validation status](https://github.com/akhilsivanand/moss-runpod/blob/main/docs/validation-status.md) for remaining checks and publication state. Hub build, tests and external review remain separate steps. Packaging is MIT licensed; model weights and upstream software retain their licenses in `THIRD_PARTY_NOTICES.txt`. No earnings are guaranteed.
