from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from .constants import PRODUCT_NAME, SEVERITY_ORDER, VERSION
from .evidence import verification_template
from .file_safety import atomic_write_text
from .metadata import current_git_commit
from .ui import shorten

STATE_ORDER = {"observed": 1, "reproduced": 2, "cross_request_confirmed": 3}
JSONL_NAMES = ("results", "signals", "observations", "probes", "coverage", "errors")


def default_output_root() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base / "headerproof" / "runs"


def reserve_output_dir(requested: Path | None = None) -> Path:
    if requested is not None:
        out_dir = requested.expanduser()
        if out_dir.exists() and any(out_dir.iterdir()):
            raise FileExistsError(f"output directory is not empty: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    root = default_output_root()
    root.mkdir(parents=True, exist_ok=True)
    stem = f"headerproof-{datetime.now():%Y%m%d-%H%M%S-%f}"
    out_dir = root / stem
    out_dir.mkdir()
    return out_dir


class EvidenceWriter:
    """Incremental, crash-tolerant JSONL writer with bounded summary state."""

    def __init__(self, out_dir: Path, metadata: dict[str, Any]) -> None:
        self.out_dir = out_dir
        self.metadata = metadata
        self.handles: dict[str, TextIO] = {
            name: (out_dir / f"{name}.jsonl").open("a", encoding="utf-8", buffering=1)
            for name in JSONL_NAMES
        }
        self.statuses: Counter[str] = Counter()
        self.by_severity: Counter[str] = Counter()
        self.by_state: Counter[str] = Counter()
        self.by_type: Counter[str] = Counter()
        self.urls = 0
        self.verified_signals = 0
        self.observations = 0
        self.probes = 0
        self.coverage = 0
        self.error_events = 0
        self.filtered_signals = 0
        self.duplicate_signals = 0
        self.top_signals: list[dict[str, Any]] = []
        atomic_write_text(out_dir / "metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    def _write(self, name: str, item: dict[str, Any]) -> None:
        self.handles[name].write(json.dumps(item, sort_keys=True) + "\n")

    def append_result(self, item: dict[str, Any]) -> None:
        self._write("results", item)
        self.urls += 1
        self.statuses[item.get("status", "unknown")] += 1
        self.filtered_signals += int(item.get("filtered_signals", 0))
        self.duplicate_signals += int(item.get("duplicate_signals", 0))

        for signal in item.get("signals", []):
            flat = {"url": item["url"], **signal}
            self._write("signals", flat)
            self.verified_signals += 1
            self.by_severity[signal.get("severity", "unknown")] += 1
            self.by_type[signal.get("type", "unknown")] += 1
            self.by_state[signal.get("assessment", {}).get("state", "unknown")] += 1
            self.top_signals.append(flat)
            self.top_signals.sort(
                key=lambda value: (
                    STATE_ORDER.get(value.get("assessment", {}).get("state", "observed"), 0),
                    SEVERITY_ORDER.get(value.get("severity", "info"), 0),
                ),
                reverse=True,
            )
            del self.top_signals[5:]

        for observation in item.get("observations", []):
            self._write("observations", observation)
            self.observations += 1
        for probe in item.get("probes", []):
            self._write("probes", {"url": item["url"], **probe})
            self.probes += 1
        for coverage in item.get("coverage", []):
            self._write("coverage", {"record_type": "coverage", "url": item["url"], **coverage})
            self.coverage += 1
        for error in item.get("errors", []):
            payload = error if isinstance(error, dict) else {"message": str(error)}
            self._write("errors", {"record_type": "error", "url": item["url"], **payload})
            self.error_events += 1

        for handle in self.handles.values():
            handle.flush()
        atomic_write_text(
            self.out_dir / "checkpoint.json",
            json.dumps(
                {
                    "schema_version": self.metadata.get("schema_version", "1.2"),
                    "run_id": self.metadata.get("run_id", ""),
                    "completed_urls": self.urls,
                    "last_completed_url": item.get("url", ""),
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )

    def summary_payload(self) -> dict[str, Any]:
        return {
            "urls": self.urls,
            "scanned": self.statuses["scanned"],
            "partial_error": self.statuses["partial_error"],
            "partial_timeout": self.statuses["partial_timeout"],
            "error": self.statuses["error"],
            "verified_technical_signals": self.verified_signals,
            "filtered_signals": self.filtered_signals,
            "duplicate_signals": self.duplicate_signals,
            "observations": self.observations,
            "probes": self.probes,
            "coverage_records": self.coverage,
            "error_events": self.error_events,
            "by_severity": dict(self.by_severity),
            "by_evidence_state": dict(self.by_state),
            "by_type": dict(self.by_type.most_common()),
            "out_dir": str(self.out_dir),
        }

    def finalize(self) -> dict[str, Any]:
        for handle in self.handles.values():
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
            handle.close()
        self.metadata["url_count"] = self.urls
        self.metadata["completed_at"] = datetime.now().isoformat(timespec="seconds")
        self.metadata["summary"] = self.summary_payload()
        atomic_write_text(
            self.out_dir / "metadata.json",
            json.dumps(self.metadata, indent=2, sort_keys=True) + "\n",
        )
        write_summary(self.out_dir, self.metadata, self.summary_payload(), self.top_signals)
        write_verification_plan(self.out_dir)
        return self.summary_payload()


def write_summary(
    out_dir: Path,
    metadata: dict[str, Any],
    payload: dict[str, Any],
    top_signals: list[dict[str, Any]],
) -> None:
    lines = [
        "# HeaderProof Scan Summary",
        "",
        "## Run Metadata",
        "",
        f"- run_id: {metadata.get('run_id', 'unknown')}",
        f"- generated: {metadata.get('generated_at', 'unknown')}",
        f"- tool: {metadata.get('tool', PRODUCT_NAME)} {metadata.get('version', VERSION)}",
        f"- git_commit: {metadata.get('git_commit') or 'unknown'}",
        f"- command: {' '.join(str(item) for item in metadata.get('command', [])) or 'unknown'}",
        f"- urls: {payload['urls']}",
        f"- scanned: {payload['scanned']}",
        f"- partial_error: {payload['partial_error']}",
        f"- partial_timeout: {payload['partial_timeout']}",
        f"- error: {payload['error']}",
        f"- verified_technical_signals: {payload['verified_technical_signals']}",
        f"- observations: {payload['observations']}",
        f"- probes: {payload['probes']}",
        f"- coverage_records: {payload['coverage_records']}",
        f"- error_events: {payload['error_events']}",
        f"- filtered_signals: {payload['filtered_signals']}",
        f"- duplicate_signals: {payload['duplicate_signals']}",
    ]
    if top_signals:
        lines.extend(["", "## Verified Technical Signals", ""])
        for signal in top_signals:
            assessment = signal.get("assessment", {})
            lines.append(
                f"- **{signal.get('severity', 'unknown').upper()}** `{signal.get('type', 'unknown')}` "
                f"state={assessment.get('state', 'unknown')} {signal.get('url', '')} - "
                f"{signal.get('title', '')}"
            )
            missing = assessment.get("missing_proof", [])
            if missing:
                lines.append(f"  Missing proof: {shorten('; '.join(missing), 260)}")
    atomic_write_text(out_dir / "summary.md", "\n".join(lines) + "\n")


def write_outputs(
    results: list[dict[str, Any]],
    out_dir: Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_metadata = metadata or {
        "schema_version": "1.2",
        "run_id": "compat-write",
        "tool": PRODUCT_NAME,
        "version": VERSION,
        "git_commit": current_git_commit(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config": {},
    }
    writer = EvidenceWriter(out_dir, run_metadata)
    for item in results:
        writer.append_result(item)
    writer.finalize()


def write_verification_plan(out_dir: Path) -> None:
    plans = {
        "CORS": verification_template("cors_arbitrary_origin_with_credentials"),
        "CSRF": verification_template("csrf_cookie_samesite_missing"),
        "Header Injection / Response Splitting": verification_template("response_splitting_crlf_candidate"),
        "Cache Poisoning": verification_template("cache_poisoning_shared_cache_confirmed"),
        "Content Spoofing": verification_template("query_parameter_content_reflection"),
    }
    lines = [
        "# Verification Plan",
        "",
        "A live signal means the detector's technical proof gate passed. Real victim impact still requires manual validation.",
        "",
        "## Evidence States",
        "",
        "- observed: one response contains a relevant exact observation.",
        "- reproduced: explicit detector checks reproduced the technical behavior.",
        "- cross_request_confirmed: independent request roles confirmed the behavior.",
        "- impact remains unverified until a human proves real harm.",
        "",
    ]
    for name, plan in plans.items():
        lines.extend([f"## {name}", "", f"Objective: {plan['objective']}", "", "Automated Checks:"])
        lines.extend(f"- {item}" for item in plan["automated_checks"])
        lines.extend(["", "Manual Confirmation:"])
        lines.extend(f"- {item}" for item in plan["manual_confirmation"])
        lines.extend(["", f"Report Gate: {plan['report_gate']}", ""])
    atomic_write_text(out_dir / "verification-plan.md", "\n".join(lines))


def payload_from_results(results: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    flat = [signal for item in results for signal in item.get("signals", [])]
    return {
        "urls": len(results),
        "scanned": sum(1 for item in results if item.get("status") == "scanned"),
        "partial_error": sum(1 for item in results if item.get("status") == "partial_error"),
        "partial_timeout": sum(1 for item in results if item.get("status") == "partial_timeout"),
        "error": sum(1 for item in results if item.get("status") == "error"),
        "verified_technical_signals": len(flat),
        "filtered_signals": sum(item.get("filtered_signals", 0) for item in results),
        "duplicate_signals": sum(item.get("duplicate_signals", 0) for item in results),
        "observations": sum(len(item.get("observations", [])) for item in results),
        "probes": sum(len(item.get("probes", [])) for item in results),
        "coverage_records": sum(len(item.get("coverage", [])) for item in results),
        "error_events": sum(len(item.get("errors", [])) for item in results),
        "by_severity": dict(Counter(signal.get("severity", "unknown") for signal in flat)),
        "by_evidence_state": dict(
            Counter(signal.get("assessment", {}).get("state", "unknown") for signal in flat)
        ),
        "by_type": dict(Counter(signal.get("type", "unknown") for signal in flat).most_common()),
        "out_dir": str(out_dir),
    }



def sarif_payload(findings: list[dict[str, Any]]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    level_map = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}
    for finding in findings:
        rule_id = str(finding.get("type", "headerproof-finding"))
        rules.setdefault(
            rule_id,
            {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": str(finding.get("title", rule_id))},
                "properties": {
                    "security-severity": str(SEVERITY_ORDER.get(str(finding.get("severity", "info")), 1)),
                    "tags": ["security", str(finding.get("check", "headerproof"))],
                },
            },
        )
        url = str(finding.get("url", ""))
        state = str(finding.get("assessment", {}).get("state", "unverified"))
        results.append(
            {
                "ruleId": rule_id,
                "level": level_map.get(str(finding.get("severity", "info")), "note"),
                "message": {"text": f"{finding.get('title', rule_id)}; evidence_state={state}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": url},
                        }
                    }
                ],
                "properties": {
                    "severity": finding.get("severity", "info"),
                    "confidence": finding.get("confidence", "low"),
                    "evidence_state": state,
                },
            }
        )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": PRODUCT_NAME,
                        "version": VERSION,
                        "informationUri": "https://github.com/TayfurYldz/headerproof",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def read_findings(out_dir: Path) -> list[dict[str, Any]]:
    lines = (out_dir / "signals.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]

def export_findings(out_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    findings = read_findings(out_dir)
    suffix = output_path.suffix.lower()
    if suffix == ".jsonl":
        content = "\n".join(json.dumps(item, sort_keys=True) for item in findings)
        atomic_write_text(output_path, content + ("\n" if content else ""))
        return
    if suffix == ".json":
        atomic_write_text(output_path, json.dumps(findings, indent=2, sort_keys=True) + "\n")
        return
    if suffix == ".sarif":
        atomic_write_text(output_path, json.dumps(sarif_payload(findings), indent=2, sort_keys=True) + "\n")
        return
    if suffix == ".md":
        rows = ["# HeaderProof Findings", "", "| Type | Severity | State | URL |", "|---|---|---|---|"]
        for item in findings:
            state = item.get("assessment", {}).get("state", "unverified")
            rows.append(
                f"| {item.get('type', '')} | {item.get('severity', '')} | {state} | {item.get('url', '')} |"
            )
        atomic_write_text(output_path, "\n".join(rows) + "\n")
        return
    raise ValueError(f"unsupported output format: {suffix}")


def print_console_summary(
    results_or_payload: list[dict[str, Any]] | dict[str, Any],
    out_dir: Path,
    as_json: bool,
) -> None:
    payload = (
        payload_from_results(results_or_payload, out_dir)
        if isinstance(results_or_payload, list)
        else results_or_payload
    )
    if as_json:
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return
    print(
        "headerproof: "
        f"urls={payload['urls']} scanned={payload['scanned']} "
        f"findings={payload['verified_technical_signals']} suppressed={payload['filtered_signals']} "
        f"errors={payload['error']} evidence={out_dir}",
        file=sys.stderr,
    )
