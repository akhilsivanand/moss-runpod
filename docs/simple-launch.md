# Simple launch — 0.1.2

**Deploy → Connect → MOSS ComfyUI → choose a workflow.** Runpod supplies the connection token. No separate password, terminal command, model-download token or storage edit is needed for first use.

The preparation page shows the startup phase, downloaded GB and percentage while six pinned model files totaling **23.51 GB** download and verify. The fresh 0.1.2 Pod was confirmed ready **1,119.0 seconds (18 min 39 s) after the deployment response**, excluding allocation time before that response. Placement, image transfer and download speeds vary; first startup is not instant.

## Familiar ComfyUI folders

The Pod's data root is **`/workspace/ComfyUI`**:

```text
/workspace/ComfyUI/
├── models/
│   └── loras/          # upload compatible SFT LoRA files here
├── input/
├── output/
├── user/
├── custom_nodes/
├── temp/
├── cache/
└── state/
```

Use **`/workspace/ComfyUI/models/loras`**, with `loras` plural. The installed application's `/opt/comfyui/models` is an alias to the same model tree. Uploading through either model path reaches the same files. Refresh the model list or reload the editor, select the compatible SFT adapter in the second LoRA slot and set a nonzero strength. The queue API additionally requires each adapter to be in its approved catalog.

The application is baked under `/opt/moss`, ComfyUI under `/opt/comfyui` and Python under `/opt/venv`. Mounting `/workspace` does not hide that installed code.

## Existing volumes and retention

An upgrade recognizes the earlier managed `/workspace/moss` workspace and moves it to `/workspace/ComfyUI` when the destination is absent. It preserves data rather than merging conflicting roots or overwriting different same-name model files. Uploads in the installed application's old model tree are preserved before that tree becomes an alias. Unexpected links or conflicting files stop the migration for review.

The existing Pod's actual upgrade preserved eight task-file hashes, all six model inode/size/mtime records and the uploaded adapter. The new canonical directory is real, `/opt/comfyui/models` points to it, and the old managed root is absent. All four native workflows opened after the upgrade; the uploaded adapter appeared in the LoRA chooser. One real browser Run-button test produced a verified 1024×1024 image using bundled Destripe.

A **60 GB container disk** fits first use without an attached volume. To retain models, workflows and images after stopping, choose persistent storage mounted at `/workspace` in Runpod Storage. The current launch screen selects storage independently; the template's legacy volume field alone does not guarantee an attachment. Preserve retained storage when stopping. Replacing or deleting a Pod needs storage that outlives that Pod.

## Included startup script

[`scripts/entrypoint.sh`](../scripts/entrypoint.sh) is baked into the image at **`/opt/moss/scripts/entrypoint.sh`** and selected by both the image CMD and template start command. It initializes Runpod SSH, starts the authenticated progress page, prepares models and supervises ComfyUI. No external startup-script download is required. The image retains `/usr/bin/tini --` as its entry point.

The gateway uses port **8888**, labeled **MOSS ComfyUI**; SSH uses port 22. Runpod's native connection setting supplies the token, which MOSS exchanges for a secure HTTP-only browser session and removes from the URL. The internal ComfyUI service stays private. The separate Serverless API uses Runpod API authentication.

## Validation and publication

The 0.1.2 source suite passed 89 tests. The exact image passed both CPU gates and fresh GPU/dependency preflight. New fast, photography and img2img jobs passed, all four native workflows opened, and the official prompt-enhanced graph generated a new image. All five fresh queue API checks passed, including a real optional second-LoRA job and empty-prompt rejection. A same-volume restart preserved eight task-file hashes, six model inode/size/mtime records and two application hashes; readiness and all four browser imports passed again afterward.

Publication and Hub submission remain pending. See [validation status](validation-status.md), the [current report](validation.json) and the [release procedure](release.md). The runtime retains pinned CUDA 13.0 user libraries with compatible host filters, including 13.2-capable hosts; actual GPU checks remain part of each release.
