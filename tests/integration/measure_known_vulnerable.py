from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url


def scan_case(url: str) -> dict[str, Any]:
    args = parse_cli_args([url])
    args.no_live_alerts = True
    return scan_url(args.target, args)


def types(records: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("type")) for item in records if item.get("type")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    ns = parser.parse_args()
    payload = json.loads(ns.manifest.read_text())
    cases = payload.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise SystemExit("manifest contains no cases")

    rows: list[dict[str, Any]] = []
    expected_total = detected_total = promoted_total = 0
    for case in cases:
        result = scan_case(str(case["url"]))
        observed = types(result.get("observations", []))
        findings = types(result.get("signals", []))
        expected = {str(item) for item in case.get("expected_types", [])}
        detected = expected & observed
        promoted = expected & findings
        expected_total += len(expected)
        detected_total += len(detected)
        promoted_total += len(promoted)
        rows.append(
            {
                "name": case.get("name", case["url"]),
                "expected": sorted(expected),
                "observed": sorted(observed),
                "findings": sorted(findings),
                "false_negatives": sorted(expected - observed),
            }
        )

    report = {
        "cases": rows,
        "expected": expected_total,
        "detected": detected_total,
        "promoted_to_findings": promoted_total,
        "false_negatives": expected_total - detected_total,
        "detection_recall": round(detected_total / expected_total, 4) if expected_total else 0.0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
