#!/usr/bin/env bash
set -euo pipefail
if [[ -n ${MOSS_START_SIGNAL:-} ]]; then
  printf 'ready\n' > "$MOSS_START_SIGNAL"
fi
