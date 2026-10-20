# MOSS-Image SFT API

Generate images through Runpod's **Serverless queue API** with three curated presets: BF16 `photography`, INT8 `fast` and experimental latent `img2img`. For the browser editor, [deploy the separate ComfyUI Pod](https://console.runpod.io/deploy?template=8m8mm2pkpw&type=gpu), then open **Connect → MOSS ComfyUI** and choose a workflow.

Deploy an available Hub listing to create your own endpoint. Use one supported NVIDIA GPU with at least 24 GB VRAM and a **60 GB container disk**. The worker runs with `MOSS_MODE=serverless`; Runpod API authentication protects its requests. No model-download token is required.

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

Poll `/status/JOB_ID` on your endpoint for the returned job ID. Completed jobs return `output.images` containing base64 PNG bytes, plus `output.seed` and `output.preset`. A nonempty prompt is required. Generation is limited to 600 seconds after worker preparation; the Hub cold test allows 1,200,000 ms.

First startup downloads and verifies **23.51 GB** of pinned public model files. Two validated cold requests had **326 and 336 seconds of queue delay** before execution; startup varies by host and network. Ephemeral replacement workers can repeat those downloads. A network volume mounted at `/runpod-volume` with `MOSS_DATA_DIR=/runpod-volume/moss` retains the model cache; worker databases and job files remain isolated. Shared-cache concurrency has not been validated.

`photography` defaults to 1216×1664, 25 steps and CFG 2.5. `fast` defaults to 1024×1024 with the same steps/CFG. Both include Destripe and an optional second compatible SFT LoRA slot. The default approved adapter list contains only the bundled Destripe file; specifying it again adds a second patch. Other adapters require compatible installed weights and an updated approved catalog.

For `img2img`, provide `image_base64` as raw PNG/JPEG/WebP base64 without a data-URI prefix or URL. The API center-crops/resizes to the requested dimensions, defaulting to 1024×1024 with denoise 0.6. Use at most 7 MiB decoded and respect the complete encoded request limit. This is ordinary latent repainting; the model is not instruction-edit trained. Img2img has no API LoRA slot. The official prompt-enhanced graph is available only in the browser collection.

**0.1.1 API validation:** all three presets, the optional bundled second-LoRA path and empty-prompt rejection passed through Runpod SDK 1.12.0 on a fresh RTX 4090 endpoint with 60 GB ephemeral disk. Four returned PNGs were verified and inspected. The separate Pod checks also passed three GPU presets, four browser workflows, fresh prompt-enhanced generation, proxy authentication and retained-volume restart preservation. The full four-workflow browser retest after restart also passed. See the repository's [validation record](https://github.com/akhilsivanand/moss-runpod/blob/main/docs/validation.json) for exact source/image identity. Check the listing for its current build, test and review state; Hub approval remains a separate external step.

See the root README for request limits, persistence and custom-domain settings. Packaging is MIT licensed; model weights and upstream software retain their own licenses in `THIRD_PARTY_NOTICES.txt`. No earnings are guaranteed.
