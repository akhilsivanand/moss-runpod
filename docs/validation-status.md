# Validation status — 2026-10-20

**0.1.2 corrects the workspace and model paths.** Pod data now uses `/workspace/ComfyUI`, with LoRAs under **`/workspace/ComfyUI/models/loras`**. The installed application's `/opt/comfyui/models` points to that same model tree.

Runtime source is `a14d011be32b86447a06c88531f0c334b9b86f08`; the exact image is:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:21cde4857330e4bd5f8660dc95a89a85c358c79fbac77e2c08f0e80004729671
```

Fresh Pod generation, native browser, prompt enhancement and restart checks passed on the corrected image. The stable 0.1.2 image, corrected public Pod template and [GitHub release](https://github.com/akhilsivanand/moss-runpod/releases/tag/v0.1.2) are published and verified. Hub accepted the normal submission, but its build failed before tests started; it is not approved or listed. The historical [0.1.0](validation-0.1.0.json) and [0.1.1](validation-0.1.1.json) reports remain separate evidence for their earlier runtimes.

| Check | 0.1.2 result |
|---|---|
| Source suite | 89 tests passed |
| Built image | Linux AMD64 build and both in-image CPU gates passed |
| Container-only model layout | Exact image passed the Docker-overlay CPU check with no persistent mounts: baked files preserved, canonical models real, alias fixture visible and helper idempotent |
| Registry identity | Anonymous exact-image verification passed |
| Fresh GPU/dependency preflight | 409-ELF dependency and GPU preflight checks passed |
| Existing Pod data migration | Eight task-file SHA256 values, all six model inode/size/mtime records and the uploaded adapter preserved |
| Canonical model layout | Real `/workspace/ComfyUI` root and `/opt/comfyui/models` alias verified; old managed root absent after upgrade |
| Upgraded Pod native browser | All four native imports passed; both LoRA choices visible; exactly one real Run-button job produced a verified 1024×1024 PNG |
| Fresh Pod model preparation | Ready observed 1,119.0 seconds after the deployment response; six pinned models prepared |
| Fresh Pod GPU presets | New fast 768×768, photography 1216×1664 and img2img 1024×1024 jobs passed |
| Fresh native browser workflows | All four imports/serialization checks passed; a new 1024×1024 prompt-enhanced job passed with uncached TextGenerate execution |
| Public HTTP/WebSocket checks | Corrected image passed unauthenticated/invalid-token 401, same-origin POST 405/WebSocket 101 and foreign-origin HTTP/WebSocket 403 |
| Same-volume restart preservation | New container process; eight task-file hashes, six model inode/size/mtime records and two application hashes preserved; readiness and all four browser imports passed afterward |
| Fresh queue API | All three presets, optional second bundled LoRA and expected empty-prompt rejection passed |
| API response integrity | Four new PNGs decoded, hashed, seed-checked and viewed |
| API runtime evidence | SDK 1.12.0; package version 0.1.2; actual worker image matched the exact digest; RTX 4090 observed |
| API configuration | Observed 60 GB ephemeral disk, no persistent volume, min 0/max 1/idle 30 and CUDA host minimum 13.0 |
| Disposable API cleanup | Endpoint/source template deleted and 404 verified; existing published API resources unchanged |
| Stable 0.1.2 tag and public Pod template | Tested manifest promoted without rebuilding; anonymous digest identity and template image/start command/native Connect/storage/README readback verified |
| GitHub v0.1.2 release | Public release/tag target and all three downloaded assets verified anonymously; archive extraction/publication check passed |
| Runpod Hub | Submission accepted at the correct commit; build failed after 13.339 seconds without an image or test record; not listed or approved |

## Layout preservation scope

The actual existing-Pod upgrade moved the recognized managed workspace to the standard root, kept the six model files' inode/size/mtime records, preserved eight task-created file hashes and retained the uploaded adapter. The new directory is real and the installed model path resolves to it. The upgraded Pod also passed all four native browser imports, LoRA chooser visibility and a real Run-button generation. That browser test waited for a zero queue count and used only bundled Destripe; the uploaded adapter was not executed or inspected.

The separate fresh Pod passed all three GPU presets, prompt enhancement and a same-image restart. The restart preserved eight task-file hashes, six model inode/size/mtime records and two application hashes; a new process, readiness and all four native imports were verified. Model stat preservation is separate from the model verification performed during startup.

If the destination already exists, different same-name model files conflict, or unexpected links are present, migration preserves the data and stops rather than merging or overwriting it. Adapter preservation does not establish compatibility or inference quality for an arbitrary uploaded model.

## Fresh Pod observations

The fresh Pod used an RTX 4090 with NVIDIA driver 595.91.07, PyTorch 2.13.0+cu130 and CUDA runtime 13.0. The first ready observation was **1,119.0 seconds (18 min 39 s) after the deployment response**. This excludes time spent in the deployment request before its response and is not a complete click-to-ready measurement. The progress page was observed during model download; a later ready browser pass and a post-restart browser pass each imported all four workflows.

The three preset jobs took 20.026 seconds for fast, 50.437 seconds for photography and 18.148 seconds for img2img at the tested dimensions. These are client wall times, including local request handling, not isolated GPU execution measurements. The prompt-enhanced browser job separately completed with fresh TextGenerate execution. All returned test images were decoded and inspected. Host and network conditions affect startup and execution time.

The separate [container-layout CPU check](https://github.com/akhilsivanand/moss-runpod/actions/runs/39424748372) passed on the exact image without persistent mounts. It verified baked-file preservation, the real canonical model directory, alias access to an opaque LoRA fixture and repeated-helper idempotence. This is filesystem evidence; the GPU jobs above ran on the fresh Pod with its attached volume.

## Fresh queue API observations

The five cases ran sequentially on the new immutable image without an idle replacement between cases. The endpoint used the image's new default cache paths and isolated worker workspace; no old-path override was supplied.

| Check | Queue delay | Execution | Result |
|---|---:|---:|---|
| Exact Hub fast input, 768×768 | 206,571 ms | 15,543 ms | Valid PNG, seed 42 |
| Photography, 1216×1664 | 143 ms | 47,656 ms | Valid PNG, seed 424242 |
| Img2img, 1024×1024 | 158 ms | 14,322 ms | Valid PNG, seed 43; input was only the new fast image |
| Optional second Destripe LoRA at 0.25, 768×768 | 139 ms | 5,321 ms | Valid PNG, seed 44 |
| Empty prompt | 131 ms | 140 ms | Correctly rejected |

The 206.571-second cold queue delay includes worker preparation and scheduling. Execution time is separate. These are observations, not launch-time or generation-speed guarantees. Replacement ephemeral workers can download all 23.51 GB again; shared-cache concurrency remains untested. API metadata does not independently prove the exact NVIDIA driver version.

The current [validation report](validation.json) must include only completed 0.1.2 evidence. Earlier browser, restart and timing results remain in the archived reports rather than being reused for this release. Successful local checks do not establish Runpod Hub approval.

The [publication record](publication-0.1.2.json) records post-upload checks. The release ZIP and attached runtime report remain immutable; later Hub status is recorded here on repository main.

The Hub failure is separate from the successful direct Pod and queue API runtime checks. Build metadata alone does not identify the cause; the image and Pod release remain available.
