from __future__ import annotations

import json
import os
import re
import time
from urllib import parse, request

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url

BASE = os.environ.get("HEADERPROOF_DVWA_FIXTURE", "http://127.0.0.1:18080").rstrip("/")


def fetch(path: str, *, data: bytes | None = None) -> str:
    req = request.Request(f"{BASE}{path}", data=data, headers={"User-Agent": "headerproof-phase3-dvwa/1"})
    with request.urlopen(req, timeout=5) as response:
        return response.read().decode("utf-8", errors="replace")


def wait_for_dvwa() -> None:
    last_error = ""
    for _ in range(45):
        try:
            fetch("/setup.php")
            return
        except OSError as exc:
            last_error = str(exc)
            time.sleep(1)
    raise RuntimeError(f"DVWA did not become ready: {last_error}")


def initialize_database() -> None:
    payload = parse.urlencode({"create_db": "Create / Reset Database", "user_token": ""}).encode()
    fetch("/setup.php", data=payload)


def csrf_ground_truth() -> dict[str, object]:
    body = fetch("/vulnerabilities/csrf/")
    match = re.search(r'<form action="#" method="GET">(.*?)</form>', body, flags=re.I | re.S)
    if not match:
        raise RuntimeError("DVWA low-CSRF form was not found")
    form = match.group(1)
    password_fields = all(name in form for name in ('name="password_new"', 'name="password_conf"'))
    token_absent = 'name="user_token"' not in form
    if not password_fields or not token_absent:
        raise RuntimeError("DVWA fixture does not match the expected low-CSRF ground truth")
    return {
        "state_change_method": "GET",
        "password_change_fields": password_fields,
        "anti_csrf_token_absent": token_absent,
    }


def record_types(records: list[dict[str, object]]) -> list[str]:
    return sorted({str(item.get("type")) for item in records if item.get("type")})


def main() -> int:
    wait_for_dvwa()
    initialize_database()
    ground_truth = csrf_ground_truth()
    url = f"{BASE}/vulnerabilities/csrf/"
    args = parse_cli_args([url])
    args.enabled_checks = {"csrf"}
    args.no_live_alerts = True
    result = scan_url(url, args)
    observations = record_types(result.get("observations", []))
    findings = record_types(result.get("signals", []))

    # Cookie-hardening observations do not count as detection of the known
    # state-changing form's missing anti-CSRF token. Credit only a detector
    # that explicitly represents that primitive.
    accepted_types = {"csrf_form_without_token", "csrf_state_change_without_token"}
    detected = bool(accepted_types & set(observations + findings))
    report = {
        "target": "DVWA low CSRF",
        "ground_truth": ground_truth,
        "expected_vulnerability": "state-changing password form without anti-CSRF token",
        "accepted_detector_types": sorted(accepted_types),
        "observed_types": observations,
        "finding_types": findings,
        "false_negatives": 0 if detected else 1,
        "detection_recall": 1.0 if detected else 0.0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
