# Simple launch — 0.1.1

**Deploy → Connect → MOSS ComfyUI → choose a workflow.** Runpod supplies the connection token. No separate password, terminal command, download token or storage edit is needed for first use.

The preparation page appears before model downloads finish and shows phases, downloaded GB and percentage. The six pinned model files total 23,509,579,072 bytes. One fresh Pod without persistent storage became ready after **452.7 seconds (about 7 min 33 s)**. On another Pod with persistent storage, readiness was established no later than **1,134.8 seconds (about 18 min 55 s)** after creation. The latter is an upper bound taken from the first new GPU-validation record. A separate earlier attempt encountered a registry TLS handshake failure and was retired. Placement, image transfer and model-download speeds vary; these are observations rather than a launch-time guarantee.

The 0.1.1 image transfers 3,747,665,350 compressed bytes, 64.19% less than 0.1.0's 10,465,719,607 bytes. This reduces image transfer; model downloads still account for 23.51 GB on a cold cache.

## The startup script

[`scripts/entrypoint.sh`](../scripts/entrypoint.sh) is baked into the image at **`/opt/moss/scripts/entrypoint.sh`**. The image CMD and the template's explicit start command both select it. The image retains `/usr/bin/tini --` as its entry point. No external startup-script download is required.

The script initializes Runpod SSH, starts the authenticated progress page, prepares the models and supervises ComfyUI. The gateway uses port 8888, labeled **MOSS ComfyUI**; SSH uses port 22. The internal ComfyUI service remains private.

Runpod's native connection setting supplies `JUPYTER_PASSWORD`. MOSS exchanges that token for a secure HTTP-only browser session and removes the token from the URL. The image prevents a separate Jupyter server from competing for port 8888. Existing explicit-password deployments remain supported; the separate Serverless API uses Runpod API authentication.

## Optional persistent storage

The 60 GB container disk fits a fresh first-use installation without an attached volume. To keep models, edited workflows and images after stopping, choose persistent storage mounted at `/workspace` in Runpod Storage. The current launch screen chooses storage independently; a legacy template volume field does not prove a persistent attachment was created. Replacing/deleting a Pod needs storage that outlives that Pod.

Mutable data is stored under `/workspace/moss`; the installed application remains under `/opt`, so a workspace mount does not hide it. Preserve retained user files when upgrading. A volume containing earlier checkpoints can need more capacity than a fresh install.

## Validation and host compatibility

Actual native token/startup checks passed on fresh Pods with and without persistent storage. The source suite passed 79 checks; the built image passed both CPU gates and the final task-owned Pod passed the 409-ELF dependency and GPU driver checks. The final Pod completed three preset generations, all four browser imports, fresh prompt-enhanced generation and public HTTP/WebSocket checks. Restart preserved eight task files, six model records and two application hashes, with a new process and healthy service confirmed afterward. The full four-workflow browser retest after restart also passed.

The queue API passed three presets, optional second LoRA and empty-prompt rejection. The public Pod template uses the tested immutable image. See [validation status](validation-status.md) and the [release report](validation.json) for the exact tested image and completed scope; historical 0.1.0 evidence does not validate 0.1.1.

The runtime retains pinned CUDA 13.0 user libraries. Deployment metadata allows compatible host versions, including available 13.2-capable hosts. See [NVIDIA CUDA compatibility](https://docs.nvidia.com/cuda/archive/13.0.1/cuda-toolkit-release-notes/index.html) and [Runpod CUDA filters](https://docs.runpod.io/sdks/graphql/manage-pods#filter-by-cuda-version).
