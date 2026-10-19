#!/usr/bin/env python3
"""Readiness probe; contains no secrets and never reads logs."""
import sys
from urllib.request import urlopen

try:
    with urlopen('http://127.0.0.1:8188/readyz', timeout=4) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception:
    sys.exit(1)
