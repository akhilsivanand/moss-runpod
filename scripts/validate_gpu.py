#!/usr/bin/env python3
"""Generate three new preset smoke jobs on a fresh deployment.

Without --run this only validates the package catalog and prints the plan.
It does not query a GPU, contact ComfyUI, inspect history, or read saved images.
The resulting record is execution evidence, not a complete release certificate
or an assessment of image quality.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import binascii
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, UnidentifiedImageError

# Also support running this file directly from an unpacked source checkout.
SOURCE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_ROOT / "src"))
from moss_runtime import __version__
from moss_runtime.jobs import (ComfyJobRunner, GenerationRequest, MAX_OUTPUT_BYTES,
                               load_catalog, validate_request)


FAST_PROMPT = (
    "A documentary photograph of a small green plant in a clay pot on a wooden "
    "cafe table, soft window daylight, natural colors, fine leaf detail."
)
PHOTOGRAPHY_PROMPT = (
    "A candid photograph of a woman in her thirties seated beside a cafe window, "
    "holding a ceramic coffee cup with both hands. Olive cotton shirt, soft "
    "overcast daylight, natural skin texture, relaxed expression, softly blurred "
    "cafe background. Eye-level 50 mm photograph."
)
IMG2IMG_PROMPT = (
    "A watercolor illustration of a small green plant in a clay pot on a wooden "
    "cafe table, loose ink outlines, soft green washes, visible paper texture."
)
FORMATS = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gpu_details() -> dict:
    """Inspect hardware only after the operator explicitly supplies --run."""
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("A CUDA GPU must be available before running validation")
    properties = torch.cuda.get_device_properties(0)
    if properties.total_memory < 23 * 1024**3:
        raise RuntimeError("Validation requires at least 23 GiB of available device VRAM")
    response = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,driver_version,name,memory.total",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    devices = []
    for row in csv.reader(response.stdout.splitlines()):
        if len(row) != 4:
            raise RuntimeError("nvidia-smi returned unexpected hardware metadata")
        index, driver, name, memory = (value.strip() for value in row)
        devices.append({"index": int(index), "driver_version": driver,
                        "name": name, "memory_total_mib": int(memory)})
    if not devices:
        raise RuntimeError("nvidia-smi did not return driver metadata")
    return {
        "name": properties.name,
        "vram_bytes": properties.total_memory,
        "vram_gib": round(properties.total_memory / 1024**3, 3),
        "compute_capability": [properties.major, properties.minor],
        "torch_version": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_device_count": torch.cuda.device_count(),
        "nvidia_smi_devices": devices,
    }


def package_details(root: Path) -> dict:
    details = {
        "version": __version__,
        "workflow_catalog_sha256": hashlib.sha256((root / "config/workflows.json").read_bytes()).hexdigest(),
    }
    commit_file = root / "comfy-commit.txt"
    if commit_file.is_file():
        details["baked_comfy_commit"] = commit_file.read_text().strip()
    provided = {key: os.environ[key] for key in (
        "MOSS_SOURCE_REVISION", "MOSS_IMAGE_DIGEST", "MOSS_IMAGE_REFERENCE",
    ) if os.environ.get(key)}
    if provided:
        # Environment declarations are useful provenance but do not independently
        # prove the running OCI image's identity.
        details["operator_provided_environment"] = provided
    return details


def save_result(result: dict, request: GenerationRequest, destination: Path,
                elapsed_seconds: float) -> dict:
    """Verify and save only the image returned by this newly submitted job."""
    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        raise ValueError("Elapsed time must be finite and nonnegative")
    if not isinstance(result, dict) or result.get("preset") != request.preset or result.get("seed") != request.seed:
        raise RuntimeError("The worker returned an unexpected preset or seed")
    images = result.get("images")
    if not isinstance(images, list) or len(images) != 1 or not isinstance(images[0], dict):
        raise RuntimeError("The worker must return exactly one image")
    item = images[0]
    encoded = item.get("data")
    if item.get("type") != "base64" or not isinstance(encoded, str):
        raise RuntimeError("The worker did not return a base64 image")
    if len(encoded) > 4 * ((MAX_OUTPUT_BYTES + 2) // 3):
        raise RuntimeError("Returned image exceeds the output-size limit")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise RuntimeError("The worker returned invalid image encoding") from error
    if not content or len(content) > MAX_OUTPUT_BYTES:
        raise RuntimeError("Returned image is empty or too large")
    try:
        with Image.open(io.BytesIO(content)) as image:
            dimensions, image_format = image.size, image.format
            if image_format not in FORMATS or dimensions != (request.width, request.height):
                raise RuntimeError("The worker returned an unexpected image format or dimensions")
            image.verify()
    except (UnidentifiedImageError, OSError) as error:
        raise RuntimeError("The worker returned an invalid image") from error
    output = destination.with_suffix(FORMATS[image_format])
    with output.open("xb") as target:
        target.write(content)
    output.chmod(0o600)
    return {
        "preset": request.preset,
        "completed": True,
        "seed": request.seed,
        "width": dimensions[0],
        "height": dimensions[1],
        "steps": request.steps,
        "cfg": request.cfg,
        "client_elapsed_seconds": round(elapsed_seconds, 3),
        "image_sha256": hashlib.sha256(content).hexdigest(),
        "image_bytes": len(content),
        "image_format": image_format,
        "file": output.name,
    }


def _write_record(path: Path, record: dict) -> None:
    temporary = path.with_name("." + path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as target:
        json.dump(record, target, indent=2)
        target.write("\n")
    temporary.chmod(0o600)
    temporary.replace(path)


async def validate(output_dir: Path, root: Path, data_dir: Path) -> dict:
    catalog = load_catalog(root)
    hardware = gpu_details()
    # Refuse an existing path rather than inspecting or overwriting its contents.
    output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    record_path = output_dir / "record.json"
    record = {
        "schema_version": 1,
        "evidence_kind": "new_preset_job_smoke",
        "status": "running",
        "started_at": _utc_now(),
        "package": package_details(root),
        "gpu": hardware,
        "jobs": [],
        "limits": [
            "Checks execution and returned image structure, not aesthetic quality.",
            "Does not verify Pod freshness, restart persistence, authentication, SDK transport, or Hub acceptance.",
            "Elapsed times are client wall time, not isolated GPU or server execution time.",
        ],
    }
    _write_record(record_path, record)
    runner = ComfyJobRunner(root=root, data_dir=data_dir)
    lora_dir = data_dir / "models/loras"
    fast_payload = {"preset": "fast", "prompt": FAST_PROMPT, "width": 768,
                    "height": 768, "steps": 25, "seed": 42}
    photography_payload = {"preset": "photography", "prompt": PHOTOGRAPHY_PROMPT,
                           "steps": 25, "seed": 424242}
    try:
        fast_result = None
        for ordinal, payload in enumerate((fast_payload, photography_payload), 1):
            request = validate_request(payload, catalog, lora_dir)
            started = time.perf_counter()
            result = await runner.run(payload)
            elapsed = time.perf_counter() - started
            record["jobs"].append(save_result(result, request, output_dir / f"{ordinal:02d}-{request.preset}", elapsed))
            _write_record(record_path, record)
            if request.preset == "fast":
                fast_result = result
        img2img_payload = {
            "preset": "img2img", "prompt": IMG2IMG_PROMPT,
            "width": 1024, "height": 1024, "steps": 25, "seed": 43,
            "image_base64": fast_result["images"][0]["data"],
        }
        request = validate_request(img2img_payload, catalog, lora_dir)
        started = time.perf_counter()
        result = await runner.run(img2img_payload)
        elapsed = time.perf_counter() - started
        record["jobs"].append(save_result(result, request, output_dir / "03-img2img", elapsed))
        record.update(status="passed", finished_at=_utc_now())
        _write_record(record_path, record)
        return record
    except BaseException as error:
        record.update(status="failed", finished_at=_utc_now(), error_type=type(error).__name__)
        _write_record(record_path, record)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="New directory for only these three new images and record.json")
    parser.add_argument("--run", action="store_true",
                        help="Explicitly authorize submitting the three GPU jobs")
    args = parser.parse_args()
    root = Path(os.environ.get("MOSS_ROOT", SOURCE_ROOT)).resolve()
    data_dir = Path(os.environ.get("MOSS_DATA_DIR", "/workspace/moss")).resolve()
    load_catalog(root)
    if not args.run:
        print(json.dumps({
            "status": "dry_run", "gpu_jobs_submitted": 0,
            "plan": [
                {"preset": "fast", "width": 768, "height": 768, "steps": 25, "seed": 42},
                {"preset": "photography", "resolution": "catalog defaults", "steps": 25, "seed": 424242},
                {"preset": "img2img", "width": 1024, "height": 1024, "steps": 25, "seed": 43,
                 "input": "only the new fast job's returned image"},
            ],
            "requires": "--run and a new --output-dir to execute",
        }, indent=2))
        return
    record = asyncio.run(validate(args.output_dir.expanduser().absolute(), root, data_dir))
    print(json.dumps({"status": record["status"], "completed_new_jobs": len(record["jobs"]),
                      "record": str(args.output_dir / "record.json")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print("New-job GPU validation failed: " + str(error), file=sys.stderr)
        sys.exit(1)
