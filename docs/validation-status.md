# Validation status — 2026-10-20

## 0.1.1 simplified-launch candidate

The candidate has passed 79 CPU/source checks after the image-build repair and a headless Chrome token/session test using two TLS origins. The final image build and in-image checks, actual Runpod Connect deployment, new GPU jobs and restart preservation remain pending. No candidate image has been promoted or substituted into the public template. See [candidate details](simple-launch.md).

The report below and [`validation.json`](validation.json) apply only to published 0.1.0. They are not evidence for 0.1.1.

## 0.1.0 validation — 2026-10-19

The completed [publication report](validation.json) records the tested runtime
and image. The publication check passed for that release. Image `0.1.0`
is public and resolves to the tested digest below. The tested Pod template is
public and the GitHub `v0.1.0` release is published. Hub accepted the submission, but its first build was reported failed on
2026-10-20. No Hub tests ran and the listing is not approved. Replacement release validation and manual approval remain
pending.

| Check | Result |
|---|---|
| Source and package checks | 71 tests passed; source CI, release consistency, syntax/compilation, and Docker build check passed |
| Built image | Linux AMD64 build, dependency check, and CPU ComfyUI/native-template smoke passed |
| Registry | Anonymous digest verification and exact `0.1.0` promotion passed |
| Fresh Pod | L40S 48 GB, CUDA 13.0, fresh 60 GB volume; model preparation completed and baked source hashes matched |
| Pod GPU generation | Photography, fast, and img2img passed |
| Browser security and connection | Unauthenticated HTTP/WebSocket 401; foreign origin 403; authenticated POST 405 and WebSocket 101/status passed |
| Native workflows | Four landing cards, four catalog entries, and all four imports passed, including enhanced nested-subgraph serialization |
| Prompt-enhanced browser generation | TextGenerate executed and returned a 1024×1024 PNG |
| Restart preservation | Eight task-file SHA256 values, six model inode/mtime/size records, and baked app hash preserved |
| Post-restart browser/health | Readiness 200, unauthenticated HTTP/WebSocket 401, authenticated POST 405 and WebSocket 101/status passed |
| Fresh queue worker | Fast 768×768 seed 42, photography 1216×1664 seed 424242, and img2img 1024×1024 seed 43 completed |
| Additional API cases | Second-LoRA variant passed; blank prompt rejected; all four returned PNGs inspected |

The tested runtime revision is `37236a8e329d51adf2591c197a678f437650cebc`.
The public image `ghcr.io/akhilsivanand/moss-comfyui:0.1.0` resolves to:

```text
ghcr.io/akhilsivanand/moss-comfyui@sha256:4247e93d9fee317243f23713b5e55ec44e05f23a0cb41388599183b8789603ec
```

One cold API job reported 420,479 ms (about 7 minutes) of delay before execution
on one worker. That observation is not a startup-time or generation-speed
guarantee. An ephemeral replacement worker may download all 23.51 GB again
without persistent storage. Shared-cache concurrency and worker-replacement
behavior were not exercised in this validation. These results establish the
tested execution paths and persistence, without an image-quality superiority
claim. Hub automated testing and manual approval remain separate release steps;
see [release.md](release.md).
