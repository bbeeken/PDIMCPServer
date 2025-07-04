#!/usr/bin/env bash
# Simple helper to install server dependencies
set -euo pipefail
python -m pip install -r requirements.txt
python -m pip install mcp httpx
