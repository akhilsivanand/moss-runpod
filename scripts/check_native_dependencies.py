#!/usr/bin/env python3
"""Check installed ELF shared libraries without requiring a GPU at image build."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


# These libraries belong to the host NVIDIA driver, injected at GPU startup.
# CUDA runtime, cuBLAS, cuDNN, and every other userspace dependency must resolve.
HOST_DRIVER_LIBRARY = re.compile(r"(?:libcuda|libnvidia[-_A-Za-z0-9]*)\.so(?:\.\d+)*\Z")
MISSING_LIBRARY = re.compile(r"^\s*(\S+)\s+=>\s+not found\s*$", re.MULTILINE)


def shared_libraries(roots):
    seen = set()
    for root in roots:
        for path in sorted(root.rglob("*.so*")):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            with resolved.open("rb") as stream:
                if stream.read(4) == b"\x7fELF":
                    yield resolved


def library_environment(roots):
    """Mirror the pip CUDA/Torch library locations their loaders use."""
    directories = set()
    for root in roots:
        for marker in root.rglob("libtorch_global_deps.so"):
            directories.add(str(marker.parent))
        for namespace in root.rglob("nvidia"):
            if namespace.is_dir():
                directories.update(str(path) for path in namespace.rglob("lib") if path.is_dir())
    environment = os.environ.copy()
    existing = environment.get("LD_LIBRARY_PATH", "")
    environment["LD_LIBRARY_PATH"] = ":".join(sorted(directories) + ([existing] if existing else []))
    environment["LC_ALL"] = "C"
    return environment


def check(roots, require_driver=False):
    environment = library_environment(roots)
    failures = []
    deferred = set()
    count = 0
    for path in shared_libraries(roots):
        count += 1
        try:
            result = subprocess.run(["ldd", str(path)], env=environment, capture_output=True,
                                    text=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append({"file": str(path), "error": str(error)})
            continue
        missing = set(MISSING_LIBRARY.findall(result.stdout + result.stderr))
        host_only = {name for name in missing if HOST_DRIVER_LIBRARY.fullmatch(name)}
        deferred.update(host_only)
        unresolved = missing if require_driver else missing - host_only
        if unresolved or result.returncode:
            failure = {"file": str(path), "missing": sorted(unresolved)}
            if result.returncode:
                failure.update(returncode=result.returncode,
                               error=(result.stdout + result.stderr).strip())
            failures.append(failure)
    if not count:
        failures.append({"error": "No ELF shared libraries found under the requested roots."})
    return {"status": "failed" if failures else "passed", "checked_native_files": count,
            "host_driver_libraries": sorted(deferred), "require_driver": require_driver,
            "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", required=True, type=Path,
                        help="Installed runtime directory to scan; may be repeated")
    parser.add_argument("--require-driver", action="store_true",
                        help="Also require host driver libraries, for a GPU runtime check")
    arguments = parser.parse_args()
    roots = [path.resolve() for path in arguments.root]
    for root in roots:
        if not root.is_dir():
            parser.error(f"Runtime directory does not exist: {root}")
    report = check(roots, arguments.require_driver)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
