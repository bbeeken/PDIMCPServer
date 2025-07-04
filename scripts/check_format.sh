#!/usr/bin/env bash
# Verify code formatting using black
set -euo pipefail
black --check .
