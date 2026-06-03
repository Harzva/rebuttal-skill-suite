#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-7864}"

cd "$ROOT_DIR/webview"
echo "Serving anonymized rebuttal dashboard at http://${HOST}:${PORT}/"
python3 -m http.server "$PORT" --bind "$HOST"
