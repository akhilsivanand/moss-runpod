# Simplified launch candidate

This branch prepares a simpler ComfyUI launch. It is not the published `0.1.0` image or a completed GPU validation report.

The intended user flow is **Deploy → Connect → choose a workflow**. Runpod's Connect button supplies its platform-issued access token; users do not create or copy a separate MOSS password. The service shows preparation phases, downloaded GB, and percentage until the workflows are ready.

## Connection

The candidate uses the native token-bearing Connect link on port 8888, labeled **MOSS ComfyUI**. The template enables Runpod's Jupyter token setting, while the image suppresses the actual Jupyter server and serves MOSS instead. Valid launch tokens become secure, HTTP-only browser sessions and are removed from the URL. The existing explicit-password and Serverless interfaces remain supported.

This requires verification of the actual platform-issued token during an isolated deployment. The public template must remain on the validated release until that check passes. No shared password or public setup token belongs in the template.

## Storage

A 60 GB container disk provides room for the model files without requiring a storage edit before first use. Templates can also request a 60 GB persistent volume at `/workspace`, but the current Runpod workload-first launch screen selects storage independently and can launch with no attached volume.

Persistent storage is an optional Runpod setting for users who want models and images retained after stopping. Documentation must distinguish that choice from starting the UI; it must not promise retention for a launch with no persistent attachment. Existing files and edited workflows remain protected when a volume is attached.

## Validation before publication

- Validate native token exchange, clean URLs, browser session security, authenticated HTTP and WebSocket traffic, foreign-origin rejection, and native readiness polling.
- Build the candidate and pass the in-image dependency and actual ComfyUI CPU checks.
- Verify the platform-generated token and Connect button through a fresh task-owned deployment; observe only new validation jobs, never user logs or history.
- Keep the user's stopped Pod untouched. Retire any task-owned validation resources after the checks.
- Record the candidate's own source and image identities before replacing the public template or publishing a new release.
