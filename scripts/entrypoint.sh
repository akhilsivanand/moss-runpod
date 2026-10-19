#!/usr/bin/env bash
set -Eeuo pipefail

case "${MOSS_MODE:-pod}" in
  pod)
    /opt/venv/bin/python - <<'PY'
import sys
from moss_runtime.gateway import auth_from_environment
try:
    auth_from_environment()
except ValueError as error:
    print(str(error), file=sys.stderr)
    sys.exit(2)
PY
    # Let the official Runpod base initialize SSH before the foreground app.
    # The hook acknowledges initialization; it does not background the app.
    MOSS_START_SIGNAL="$(mktemp /tmp/moss-base-ready.XXXXXX)"
    export MOSS_START_SIGNAL
    # Keep the provider's token in this parent for the MOSS gateway, while
    # preventing the base image from starting a second service on port 8888.
    env -u JUPYTER_PASSWORD -u JUPYTER_DISABLE_AUTH -u MOSS_PASSWORD /start.sh &
    base_pid=$!
    for attempt in {1..120}; do
      [[ -s "$MOSS_START_SIGNAL" ]] && break
      kill -0 "$base_pid" 2>/dev/null || { printf 'Runpod base initialization exited.\n' >&2; exit 1; }
      sleep 0.5
    done
    [[ -s "$MOSS_START_SIGNAL" ]] || { printf 'Runpod base initialization timed out.\n' >&2; exit 1; }
    rm -f -- "$MOSS_START_SIGNAL"
    unset MOSS_START_SIGNAL
    ;;
  serverless) ;;
  *) printf '%s\n' 'MOSS_MODE must be pod or serverless.' >&2; exit 2 ;;
esac

# A failed application now fails the container. tini forwards signals/reaps
# children; the runtime supervises ComfyUI and the Hub worker together.
exec /opt/venv/bin/python -m moss_runtime.bootstrap "$@"
