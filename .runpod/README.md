# MOSS-Image SFT API

Generate images with three presets: `photography` (SFT BF16 and full VAE), `fast` (SFT INT8 and small VAE), and experimental latent `img2img`. This Hub listing uses Runpod's queue-based Serverless API. For the interactive ComfyUI browser, use the separate Pod template described in the repository README.

**Release preparation:** the container image and a fresh-volume GPU run still require validation before publication.

Use one 24 GB NVIDIA GPU with a CUDA 13.0-compatible host and 60 GB container disk. Initial startup downloads and verifies 23.51 GB of public model files; no model-download token is required. For a persistent network volume mounted at `/runpod-volume`, set `MOSS_DATA_DIR=/runpod-volume/moss` to retain the model cache across worker replacements. Job files and databases stay in separate temporary workspaces per worker.

Example `/run` request body:

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

A nonempty prompt is required. Completed jobs return base64 images, seed, and preset. Use the asynchronous `/run` route and poll the returned job's status. Execution is limited to 600 seconds per job after worker preparation. The release's Hub test has a 1,200,000 ms cold-test timeout.

For img2img, supply `image_base64` containing raw base64 PNG, JPEG, or WebP bytes, without a data-URI prefix or URL. The API resizes/center-crops to `width` and `height` (default 1024×1024), with denoise 0.6. The browser graph's approximately 1 MP aspect-preserving behavior is separate. Use at most 7 MiB of decoded image bytes so the encoded request fits Runpod's asynchronous request-size limit.

The worker runs with `MOSS_MODE=serverless`. The Pod mode uses `MOSS_MODE=pod`, port 8188, and a user-configured `MOSS_PASSWORD` of at least 12 characters for the `moss` login. No password is needed for the Serverless worker; use Runpod API authentication.

See the root README for graph details, image-input format, persistence, and licenses. Maintainers must complete `docs/release.md` before promoting this listing. Model weights and upstream software keep their separate licenses in `THIRD_PARTY_NOTICES.txt`.
