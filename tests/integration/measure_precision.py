from __future__ import annotations

import json
import os
import uuid
from urllib import request

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url

FIXTURES = {
    "varnish": os.environ.get("HEADERPROOF_VARNISH_FIXTURE", ""),
    "nginx": os.environ.get("HEADERPROOF_NGINX_FIXTURE", ""),
    "cloudflare": os.environ.get("HEADERPROOF_CLOUDFLARE_FIXTURE", ""),
    "fastly": os.environ.get("HEADERPROOF_FASTLY_FIXTURE", ""),
}
CASES = (("/vulnerable", True), ("/safe", False), ("/clean", False))


def provider_evidence(name: str, base: str) -> dict[str, str]:
    url = f"{base.rstrip('/')}/clean?provider_proof={uuid.uuid4().hex}"
    req = request.Request(url, headers={"User-Agent": "headerproof-phase3-measurement/1"})
    with request.urlopen(req, timeout=8) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
    if name == "cloudflare":
        return {key: headers[key] for key in ("cf-ray", "cf-cache-status") if key in headers}
    if name == "fastly":
        return {key: headers[key] for key in ("x-served-by", "x-cache") if key in headers}
    return {key: headers[key] for key in ("server", "x-cache", "age") if key in headers}


def provider_verified(name: str, evidence: dict[str, str]) -> bool:
    if name == "cloudflare":
        return "cf-ray" in evidence and "cf-cache-status" in evidence
    if name == "fastly":
        return "x-served-by" in evidence and "x-cache" in evidence
    return True


def confirmed(base: str, path: str) -> bool:
    target = f"{base.rstrip('/')}{path}?case={uuid.uuid4().hex}"
    args = parse_cli_args([target])
    args.enabled_checks = {"header-injection", "cache-poisoning"}
    args.header_probe_limit = 1
    args.per_url_concurrency = 1
    args.concurrency = 1
    args.url_timeout = 9.0
    args.no_live_alerts = True
    result = scan_url(args.target, args)
    return any(item.get("type") == "cache_poisoning_shared_cache_confirmed" for item in result["signals"])


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def main() -> int:
    report: dict[str, object] = {"implementations": {}}
    total = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    invalid_providers: list[str] = []
    for name, base in FIXTURES.items():
        if not base:
            continue
        evidence = provider_evidence(name, base)
        if not provider_verified(name, evidence):
            invalid_providers.append(name)
            report["implementations"][name] = {
                "error": "provider fingerprint not verified",
                "provider_evidence": evidence,
            }
            continue
        counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        for path, expected in CASES:
            actual = confirmed(base, path)
            key = "tp" if expected and actual else "fn" if expected else "fp" if actual else "tn"
            counts[key] += 1
            total[key] += 1
        report["implementations"][name] = {
            **counts,
            "precision": ratio(counts["tp"], counts["tp"] + counts["fp"]),
            "recall": ratio(counts["tp"], counts["tp"] + counts["fn"]),
            "provider_evidence": evidence,
        }
    report["aggregate"] = {
        **total,
        "precision": ratio(total["tp"], total["tp"] + total["fp"]),
        "recall": ratio(total["tp"], total["tp"] + total["fn"]),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if invalid_providers:
        return 3
    return 0 if report["implementations"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
