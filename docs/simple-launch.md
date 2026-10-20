# Simplified launch — 0.1.1 candidate

The intended user flow is **Deploy → Connect → choose a workflow**. Runpod's Connect link supplies its platform-issued access token. Users do not create or copy a separate MOSS password. The preparation page shows startup phases, downloaded GB and percentage until the workflows are ready.

The public template still runs validated `0.1.0`. This branch is a private candidate; it is not a published replacement or a completed GPU validation report.

## Startup and connection

The startup script is [`scripts/entrypoint.sh`](../scripts/entrypoint.sh), baked into the image as `/opt/moss/scripts/entrypoint.sh`. Both the image's `CMD` and the candidate template's explicit start command select it. The image retains `/usr/bin/tini --` as its entry point so signals and child processes are handled correctly. No external startup-script download is required.

The script initializes Runpod SSH, starts the gateway before downloading models, prepares the six pinned model files, and supervises ComfyUI. The candidate uses port **8888**, labeled **MOSS ComfyUI**. [Console metadata](../deploy/pod-console.json) enables the native token-bearing connection link; the [template](../deploy/pod-template.json) does not contain a shared token or password.

Runpod provides its token through the native Jupyter setting. The image prevents a separate Jupyter server from competing for port 8888 and serves MOSS there. A valid connection token becomes a secure, HTTP-only browser session and is removed from the URL. Existing explicit-password deployments and the Serverless API remain supported.

## Storage

A 60 GB container disk provides room for the models without requiring a storage edit before first use. The template also requests a 60 GB volume at `/workspace`, but the current Runpod workload-first launch screen chooses persistent storage separately and can launch without that attachment.

Users who want models and images retained after stopping or replacing a Pod must select persistent storage in Runpod Storage. A template volume field alone does not establish that retention. Attached data keeps models, edited workflows and images outside the baked application under `/opt`.

## Candidate validation

| Check | Status |
|---|---|
| CPU/source checks | 79 passed after the image-build repair |
| Headless Chrome token/session test | Passed with two TLS origins; authenticated HTTP/WebSocket, clean URL and foreign-origin checks passed |
| Final image build and in-image CPU checks | Pending |
| Fresh task-owned GPU Pod and platform-issued Connect token | Pending |
| New generation and restart preservation | Pending |
| Candidate report and immutable image promotion | Pending |
| Public template update and 0.1.1 release | Pending |

The browser test verifies the application protocol; it does not establish that a deployed Runpod Connect button supplies the expected token. Verify that separately on a fresh task-owned Pod. Observe only its new test jobs and outputs, never user logs or history. Leave the user's stopped Pod untouched.

[`validation.json`](validation.json) remains the historical `0.1.0` report. It must not be reused as proof for this candidate. Publication requires evidence for the exact new source and immutable image digest.

## Host availability

The runtime retains its pinned CUDA 13.0 user libraries. Deployment filters also allow CUDA 13.2-capable hosts, which Runpod currently reports in stock. NVIDIA documents driver backward compatibility for applications built against older CUDA versions. The actual candidate driver and generation checks still have to pass. See [NVIDIA compatibility](https://docs.nvidia.com/cuda/archive/13.0.1/cuda-toolkit-release-notes/index.html) and [Runpod CUDA filters](https://docs.runpod.io/sdks/graphql/manage-pods#filter-by-cuda-version).
