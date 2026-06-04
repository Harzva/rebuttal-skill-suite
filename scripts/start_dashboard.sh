#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-7864}"

cd "$ROOT_DIR/webview"
echo "Serving anonymized rebuttal dashboard at http://${HOST}:${PORT}/"
echo "The page loads webview/dashboard_data.local.json first when present, then falls back to sample_dashboard_data.json."
echo "Skill Suite view loads webview/skill_registry.local.json first when present, then falls back to skill_registry.sample.json."
python3 -m http.server "$PORT" --bind "$HOST"
