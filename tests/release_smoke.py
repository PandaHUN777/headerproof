from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SmokeHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return

    def do_OPTIONS(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b"headerproof-release-smoke")


def main() -> int:
    bin_cmd = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HEADERPROOF_BIN", "headerproof")

    server = ThreadingHTTPServer(("127.0.0.1", 0), SmokeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="headerproof-release-smoke-") as raw_tmp:
            tmp = Path(raw_tmp)
            input_file = tmp / "urls.txt"
            input_file.write_text(f"http://127.0.0.1:{server.server_port}/smoke\n")
            env = dict(os.environ)
            env["XDG_STATE_HOME"] = str(tmp / "state")
            completed = subprocess.run(
                [
                    bin_cmd,
                    "-l",
                    str(input_file),
                    "-c",
                    "1",
                    "-silent",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
                env=env,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"installed scan failed: {completed.stderr or completed.stdout}")
            run_dirs = sorted((tmp / "state" / "headerproof" / "runs").glob("headerproof-*"))
            if len(run_dirs) != 1:
                raise RuntimeError(f"expected one evidence run, got {len(run_dirs)}")
            out_dir = run_dirs[0]
            result = json.loads((out_dir / "results.jsonl").read_text().splitlines()[0])
            if result["status"] != "scanned" or not result["probes"]:
                raise RuntimeError("installed scan did not produce a completed result with probes")
            for probe in result["probes"]:
                if probe["status"] == "completed" and not isinstance(probe["exchange"], dict):
                    raise RuntimeError("installed scan wrote a null completed exchange")

            # Verify invalid target error handling: documented exit code 2 and stderr message
            invalid_run = subprocess.run(
                [
                    bin_cmd,
                    "http://",
                    "-c",
                    "1",
                    "-silent",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            if invalid_run.returncode != 2:
                raise RuntimeError(
                    f"invalid target expected exit code 2, got {invalid_run.returncode} (stderr={invalid_run.stderr!r})"
                )
            if "headerproof: invalid target: http://" not in invalid_run.stderr:
                raise RuntimeError(
                    f"invalid target expected 'headerproof: invalid target: http://' in stderr, got {invalid_run.stderr!r}"
                )
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
