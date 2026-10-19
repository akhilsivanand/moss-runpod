# syntax=docker/dockerfile:1
# runpod/base:1.4.1-cuda1300-ubuntu2404; includes SSH, no duplicate Torch install.
FROM runpod/base@sha256:b635f96e8e24b75a4a3ff2132b8043dd4c4651f75775a4f1a670d8e4b19b55fc
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG COMFY_COMMIT=63be2f9b82ad0dac88a7ceaa28a9cf3154125a18
ARG VERSION=0.1.0
LABEL org.opencontainers.image.title="MOSS Image Studio" \
      org.opencontainers.image.description="Curated MOSS-Image workflows for ComfyUI and the Runpod Hub" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update && apt-get install -y --no-install-recommends tini curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/* \
    && python3.11 -c 'import sys; assert sys.version_info[:2] == (3,11)'
COPY requirements/runtime.lock /opt/moss/requirements/runtime.lock
RUN python3.11 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir 'pip==25.2' \
    && /opt/venv/bin/python -m pip install --no-cache-dir --no-compile --only-binary=:all: \
        --require-hashes -r /opt/moss/requirements/runtime.lock
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

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/opt/moss/src \
    PYTHONUNBUFFERED=1 \
    MOSS_ROOT=/opt/moss \
    COMFY_ROOT=/opt/comfyui \
    MOSS_DATA_DIR=/workspace/moss \
    MOSS_MODE=pod \
    COMFY_URL=http://127.0.0.1:8189
WORKDIR /opt/moss
EXPOSE 8188 22
HEALTHCHECK --interval=30s --timeout=5s --start-period=15m --retries=3 \
    CMD ["/opt/venv/bin/python", "/opt/moss/scripts/healthcheck.py"]
ENTRYPOINT ["/opt/nvidia/nvidia_entrypoint.sh", "/usr/bin/tini", "--"]
CMD ["/opt/moss/scripts/entrypoint.sh"]
