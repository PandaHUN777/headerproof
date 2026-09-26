from __future__ import annotations

import json
from urllib import request

API = "https://fiddle.fastly.dev"


def call(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=30) as response:
        return json.load(response)


fiddle = {
    "title": "HeaderProof controlled cache fixture",
    "description": "Ephemeral Fastly Fiddle for HeaderProof Phase 3 cache validation.",
    "type": "vcl",
    "origins": ["https://http-me.fastly.dev"],
    "src": {
        "recv": """
if (req.url.path == "/vulnerable") {
  set req.url = "/cache=120/body=vulnerable";
} elsif (req.url.path == "/safe") {
  set req.url = "/cache=120/body=safe";
} else {
  set req.url = "/cache=120/body=clean";
}
""".strip(),
        "fetch": """
if (bereq.url ~ "body=vulnerable" && bereq.http.X-Forwarded-Host) {
  set beresp.http.X-HeaderProof-Fixture = bereq.http.X-Forwarded-Host;
}
if (bereq.url ~ "body=safe") {
  set beresp.http.Vary = "X-Forwarded-Host";
}
set beresp.ttl = 120s;
""".strip(),
    },
    "requests": [
        {
            "method": "GET", "path": "/clean", "headers": "", "body": "", "data": {},
            "enableCluster": True, "enableShield": False, "useFreshCache": True,
            "connType": "h2", "sourceIP": "client", "followRedirects": False,
            "tests": "clientFetch.status is 200", "delay": 0,
        }
    ],
}
created = call("POST", "/fiddle", fiddle)
fiddle_id = str(created.get("id") or created.get("fiddle", {}).get("id") or "")
if not fiddle_id:
    raise SystemExit(f"Fiddle creation did not return an id: {created}")
def execute(fiddle_id: str, cache_id: int) -> str:
    executed = call("POST", f"/fiddle/{fiddle_id}/execute?cacheID={cache_id}")
    session_id = str(executed.get("sessionID") or "")
    if not session_id:
        return ""
    stream = request.Request(
        f"{API}/results/{session_id}/stream",
        headers={"Accept": "text/event-stream"},
    )
    with request.urlopen(stream, timeout=90) as response:
        event = ""
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line.partition(":")[2].strip()
            elif line.startswith("data:") and event == "updateResult":
                payload = json.loads(line.partition(":")[2].strip())
                exec_host = str(payload.get("execHost") or "")
                if exec_host:
                    return exec_host
    return ""


exec_host = ""
for cache_id in range(3):
    exec_host = execute(fiddle_id, cache_id)
    if exec_host:
        break
if not exec_host:
    raise SystemExit("Fastly Fiddle execution did not expose an execHost after three attempts")
print(json.dumps({"fiddle_id": fiddle_id, "base_url": f"https://{exec_host}"}, indent=2))
