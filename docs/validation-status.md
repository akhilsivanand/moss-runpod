# Validation status — 2026-10-20

Release 0.1.1 uses runtime source `0bf51872c7b9350a40f96cd8295d318bcef8b181` and the tested immutable image:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:816f8e002989b700678f2efc53c3dc08e799a69f2b61079e1c80d1406be792c1
```

The public Pod template and stable `0.1.1` image tag use the tested immutable image. GitHub release assets and Runpod Hub status are tracked separately; successful deployment tests do not establish Hub approval.

| Check | Result |
|---|---|
| Source checks | 79 passed |
| Built image | Linux AMD64 build and both in-image CPU gates passed |
| Native dependencies and GPU driver | Final task-owned Pod passed the 409-ELF dependency check and GPU driver probe; see validation.json for exact hardware/runtime versions |
| Registry | Anonymous immutable-image verification passed |
| Image transfer | 3,747,665,350 compressed bytes; 64.19% smaller than 0.1.0's 10,465,719,607 bytes |
| Native Runpod connection | Platform-issued token and startup page passed on fresh Pods with and without a persistent attachment |
| No-volume first use | Ready after 452.7 seconds on one host; no storage/password/terminal edit required |
| No-volume browser generation | Fresh, uncached UI generation passed; a repeat network capture recorded 11 cached resources separately |
| Final Pod GPU presets | Fast 768×768, photography 1216×1664 and img2img 1024×1024 passed |
| Four native browser workflows | All four imports and graph checks passed before restart |
| Prompt-enhanced browser generation | Fresh 1024×1024 output passed at 25 steps/CFG 2.5 through native graphToPrompt and TextGenerate; executing/success events confirmed uncached execution |
| Public HTTP/WebSocket security | HTTP/WebSocket 401 without authentication, invalid-token 401, same-origin POST 405/WebSocket 101 and foreign-origin 403 for both passed |
| Restart preservation | A new process was confirmed; eight task-file hashes, six model stat records and two application hashes were preserved |
| Post-restart health and transport | Health READY; public authentication, same-origin and foreign-origin HTTP/WebSocket checks passed |
| Full post-restart browser retest | All four workflows passed the native browser suite after restart |
| Fresh queue API | All three presets, optional bundled second LoRA and expected empty-prompt rejection passed via Runpod SDK 1.12.0 |
| API output integrity | Four returned PNGs verified, hashed and viewed; sizes 768², 1216×1664, 1024² and 768² |
| Disposable API cleanup | Task-created endpoint/source template deleted; 404 verified; existing published endpoint/template unchanged |
| Public Pod template | Verified public with the tested immutable image, explicit startup command, native Connect and updated README; fresh unsigned browser rendered the selected template |
| Stable image 0.1.1 | Exact tested manifest promoted through [GitHub Actions](https://github.com/akhilsivanand/moss-runpod/actions/runs/39417149680); anonymous digest verification passed |
| GitHub v0.1.1 release | Source ZIP and extracted publication checks passed; public artifacts are tracked on the [release page](https://github.com/akhilsivanand/moss-runpod/releases/tag/v0.1.1) |
| Runpod Hub | New release requires Hub build, test and external review; check the [listing](https://console.runpod.io/hub/listing/akhilsivanand/moss-runpod) for availability |

The public deploy page and template metadata were checked in a fresh unsigned browser. Runpod's sign-in modal prevented an authenticated console launch; equivalent task-owned GPU deployments were created through the API, and actual ComfyUI use was validated in the browser.

## Pod observations

Three newly submitted preset jobs completed on the final Pod: fast in 28.696 seconds, photography in 54.612 seconds and img2img in 20.582 seconds. These are client timings for these jobs, not speed guarantees or image-quality benchmarks.

Cold startup varied across hosts. The fresh Pod without a persistent volume became ready after **452.7 seconds (about 7 min 33 s)**. On the final persistent Pod, readiness was established no later than **1,134.8 seconds (about 18 min 55 s)** after creation, using the first new GPU-validation record as the upper bound. A separate earlier attempt encountered a registry TLS handshake failure while fetching image configuration and was retired. These observations include host/image-transfer effects and do not establish a fixed launch time.

## Queue API observations

The fresh endpoint used one RTX 4090 GPU, a 60 GB ephemeral disk, no persistent model volume and worker settings of min 0, max 1 and an idle timeout of 30 seconds. A CUDA host minimum of 13.0 accepted available hosts; API worker metadata did not independently establish the exact NVIDIA driver version.

| Check | Queue delay | Execution | Result |
|---|---:|---:|---|
| Exact Hub fast input, 768×768 | 326,179 ms | 16,723 ms | Valid PNG, seed 42 |
| Photography, 1216×1664 | 138 ms | 46,991 ms | Valid PNG, seed 424242 |
| Img2img, 1024×1024 | 150 ms | 14,914 ms | Valid PNG, seed 43; input was only the new fast image |
| Optional second Destripe LoRA at 0.25, 768×768 | 336,267 ms | 13,050 ms | Valid PNG, seed 44 |
| Empty prompt | 126 ms | 127 ms | Correctly rejected |

The second cold delay followed worker idle shutdown between test collection and the next submission. Queue delay includes cold preparation and scheduling; it is separate from generation execution. These are observations, not timing guarantees. A replacement ephemeral worker may download all 23.51 GB again. Shared-cache concurrency remains untested.

These results establish tested execution and response integrity without claiming universal image-quality superiority. The current [publication report](validation.json) must record only completed 0.1.1 checks. The archived [0.1.0 report](validation-0.1.0.json) applies to its earlier runtime and is not evidence for 0.1.1.
