#!/usr/bin/env python3
"""Serve the dashboard with optional local management APIs.

Default mode is intentionally conservative: static files plus read-only registry
refresh. Mutating or long-running actions require --enable-actions.
"""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
WEBVIEW = ROOT / "webview"

READ_ONLY_COMMANDS = {
    "/api/refresh-skill-registry": [sys.executable, str(ROOT / "scripts" / "build_skill_registry_data.py")],
    "/api/check-skills": ["bash", str(ROOT / "scripts" / "install_skills.sh"), "--check"],
    "/api/validate-extensions": [sys.executable, str(ROOT / "scripts" / "validate_extensions.py")],
}
ACTION_COMMANDS = {
    "/api/install-skills": ["bash", str(ROOT / "scripts" / "install_skills.sh")],
    "/api/validate-suite": ["bash", str(ROOT / "scripts" / "validate_suite.sh")],
}


def run_command(command: list[str], timeout: int = 120) -> dict[str, object]:
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return {"ok": result.returncode == 0, "returncode": result.returncode, "output": result.stdout[-12000:]}


class Handler(SimpleHTTPRequestHandler):
    enable_actions = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBVIEW), **kwargs)

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/skill-registry":
            payload = run_command(READ_ONLY_COMMANDS["/api/refresh-skill-registry"], timeout=30)
            registry = WEBVIEW / "skill_registry.local.json"
            if registry.exists():
                payload["registry"] = json.loads(registry.read_text(encoding="utf-8"))
            self.send_json(200 if payload["ok"] else 500, payload)
            return
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path in READ_ONLY_COMMANDS:
            self.send_json(200, run_command(READ_ONLY_COMMANDS[path], timeout=120))
            return
        if path in ACTION_COMMANDS:
            if not self.enable_actions:
                self.send_json(403, {"ok": False, "error": "Actions are disabled. Restart with --enable-actions to allow this endpoint."})
                return
            timeout = 600 if path == "/api/validate-suite" else 120
            self.send_json(200, run_command(ACTION_COMMANDS[path], timeout=timeout))
            return
        self.send_json(404, {"ok": False, "error": f"Unknown endpoint: {path}"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7864)
    parser.add_argument("--enable-actions", action="store_true")
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost"}:
        print("Refusing to bind non-localhost host for dashboard management server.", file=sys.stderr)
        return 2

    Handler.enable_actions = args.enable_actions
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving dashboard at http://{args.host}:{args.port}/")
    print("Read-only APIs: /api/skill-registry, /api/refresh-skill-registry, /api/check-skills, /api/validate-extensions")
    if args.enable_actions:
        print("Actions enabled: /api/install-skills, /api/validate-suite")
    else:
        print("Actions disabled. Restart with --enable-actions to allow install/validate-suite endpoints.")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
