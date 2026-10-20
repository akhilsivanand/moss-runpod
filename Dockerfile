# syntax=docker/dockerfile:1
# Retain the tested Runpod SSH initialization without shipping its CUDA toolkit.
FROM runpod/base@sha256:b635f96e8e24b75a4a3ff2132b8043dd4c4651f75775a4f1a670d8e4b19b55fc AS runpod_init
# Official python:3.11-slim-bookworm, linux/amd64, Python 3.11.17.
# CUDA user libraries come from the unchanged, hash-locked binary wheels.
FROM python@sha256:8a00ecb83ed9d0864dfd102a1bdb2067fda907ceb30bb86d09da9ee558b19590
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG COMFY_COMMIT=63be2f9b82ad0dac88a7ceaa28a9cf3154125a18
ARG VERSION=0.1.2
LABEL org.opencontainers.image.title="MOSS Image Studio" \
      org.opencontainers.image.description="Curated MOSS-Image workflows for ComfyUI and the Runpod Hub" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.licenses="MIT"

# Include the small RDMA/MPI runtimes linked by the pinned NVIDIA wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx openssh-server tini curl ca-certificates git \
        gcc libc6-dev libstdc++6 libgomp1 \
        libibverbs1 ibverbs-providers librdmacm1 libopenmpi3 libpmix2 libfabric1 libucx0 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/ssh/ssh_host_* \
    && mkdir -p /run/sshd \
    && python3.11 -c 'import sys; assert sys.version_info[:2] == (3,11)'
COPY --from=runpod_init /start.sh /start.sh
# License for the copied Runpod containers startup script:
# https://github.com/runpod/containers/blob/main/LICENSE
RUN <<'LICENSE'
set -eu
printf '%s  /start.sh\n' '2a745b3f8456da49adf23fecf72ef8dc92920d59b8c55c6d50d4788d49c24a5a' | sha256sum -c -
mkdir -p /usr/share/licenses/runpod-containers
cat > /usr/share/licenses/runpod-containers/LICENSE <<'MIT'
MIT License

Copyright (c) 2022 RunPod, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
MIT
LICENSE
COPY requirements/runtime.lock /opt/moss/requirements/runtime.lock
RUN python3.11 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir 'pip==25.2' \
    && /opt/venv/bin/python -m pip install --no-cache-dir --no-compile --only-binary=:all: \
        --require-hashes -r /opt/moss/requirements/runtime.lock
COPY scripts/check_native_dependencies.py /opt/moss/scripts/check_native_dependencies.py
RUN /opt/venv/bin/python /opt/moss/scripts/check_native_dependencies.py --root /opt/venv --cuda-only \
    && /opt/venv/bin/python -c 'from pathlib import Path; import sysconfig; from triton import knobs; assert (Path(sysconfig.get_paths()["include"]) / "Python.h").is_file(); print("Triton ptxas:", knobs.nvidia.ptxas.path)'
RUN git init --quiet /opt/comfyui \
    && git -C /opt/comfyui remote add origin https://github.com/Comfy-Org/ComfyUI.git \
    && git -C /opt/comfyui fetch --depth 1 origin "$COMFY_COMMIT" \
    && git -C /opt/comfyui checkout --detach "$COMFY_COMMIT" \
    && test "$(git -C /opt/comfyui rev-parse HEAD)" = "$COMFY_COMMIT" \
    && printf '%s\n' "$COMFY_COMMIT" >/opt/moss/comfy-commit.txt \
    && rm -rf /opt/comfyui/.git

COPY src/ /opt/moss/src/
COPY config/ /opt/moss/config/
COPY workflows/ /opt/moss/workflows/
COPY scripts/ /opt/moss/scripts/
COPY handler.py README.md LICENSE THIRD_PARTY_NOTICES.txt /opt/moss/
COPY custom_nodes/moss/ /opt/comfyui/custom_nodes/moss/
COPY scripts/base-ready.sh /post_start.sh
RUN ln -s /opt/moss/workflows/ui /opt/comfyui/custom_nodes/moss/example_workflows \
    && chmod 0755 /post_start.sh /opt/moss/scripts/entrypoint.sh \
    && test -x /start.sh

ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/opt/moss/src \
    PYTHONUNBUFFERED=1 \
    MOSS_ROOT=/opt/moss \
    COMFY_ROOT=/opt/comfyui \
    MOSS_DATA_DIR=/workspace/ComfyUI \
    MOSS_MODE=pod \
    COMFY_URL=http://127.0.0.1:8189
WORKDIR /opt/moss
EXPOSE 8888 8188 22
HEALTHCHECK --interval=30s --timeout=5s --start-period=15m --retries=3 \
    CMD ["/opt/venv/bin/python", "/opt/moss/scripts/healthcheck.py"]
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/moss/scripts/entrypoint.sh"]
