from __future__ import annotations

import json
from pathlib import Path

from headerproof.output import export_findings, sarif_payload


def finding() -> dict[str, object]:
    return {
        "url": "https://example.com/demo",
        "type": "response_splitting_crlf_candidate",
        "check": "header-injection",
        "title": "CRLF query probe influenced response headers",
        "severity": "high",
        "confidence": "high",
        "assessment": {"state": "reproduced"},
    }


def test_sarif_payload_contains_rule_and_location() -> None:
    payload = sarif_payload([finding()])

    run = payload["runs"][0]
    assert payload["version"] == "2.1.0"
    assert run["tool"]["driver"]["name"] == "HeaderProof"
    assert run["results"][0]["ruleId"] == "response_splitting_crlf_candidate"
    assert run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == (
        "https://example.com/demo"
    )


def test_export_sarif_uses_signal_records(tmp_path: Path) -> None:
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    (out_dir / "signals.jsonl").write_text(json.dumps(finding()) + "\n")
    output = tmp_path / "findings.sarif"

    export_findings(out_dir, output)

    payload = json.loads(output.read_text())
    assert payload["runs"][0]["results"][0]["level"] == "error"
    assert payload["runs"][0]["tool"]["driver"]["rules"][0]["id"] == "response_splitting_crlf_candidate"
