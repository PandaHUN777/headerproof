from __future__ import annotations

import json
import os
import uuid

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url

FIXTURES = {
    "varnish": os.environ.get("HEADERPROOF_VARNISH_FIXTURE", ""),
    "nginx": os.environ.get("HEADERPROOF_NGINX_FIXTURE", ""),
    "cloudflare": os.environ.get("HEADERPROOF_CLOUDFLARE_FIXTURE", ""),
    "fastly": os.environ.get("HEADERPROOF_FASTLY_FIXTURE", ""),
}
CASES = (("/vulnerable", True), ("/safe", False), ("/clean", False))


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
    for name, base in FIXTURES.items():
        if not base:
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
        }
    report["aggregate"] = {
        **total,
        "precision": ratio(total["tp"], total["tp"] + total["fp"]),
        "recall": ratio(total["tp"], total["tp"] + total["fn"]),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["implementations"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
