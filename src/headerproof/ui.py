from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections import Counter
from typing import Any

from .constants import CONFIDENCE_ORDER

ALERT_LOCK = threading.Lock()


def alert_allowed(signal: dict[str, Any], min_confidence: str) -> bool:
    assessment = signal.get("assessment", {})
    if assessment.get("technical_gate") != "passed":
        return False
    return CONFIDENCE_ORDER.get(signal.get("confidence", "low"), 0) >= CONFIDENCE_ORDER[min_confidence]


def terminal_color(enabled: bool, severity: str) -> str:
    if not enabled:
        return ""
    return {
        "critical": "\033[95m",
        "high": "\033[91m",
        "medium": "\033[93m",
        "low": "\033[96m",
        "info": "\033[90m",
    }.get(severity, "")


def reset_color(enabled: bool) -> str:
    return "\033[0m" if enabled else ""


def shorten(value: Any, limit: int = 180) -> str:
    text = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{sec:02d}s"
    if minutes:
        return f"{minutes}m{sec:02d}s"
    return f"{sec}s"


def emit_scan_start(input_label: Any, url_count: int | str, args: argparse.Namespace, out_dir: Any) -> None:
    if args.silent or args.json:
        return
    print(
        f"headerproof: input={input_label} urls={url_count} concurrency={args.concurrency} evidence={out_dir}",
        file=sys.stderr,
        flush=True,
    )


def emit_progress(
    completed: int,
    total: int,
    started_at: float,
    statuses: Counter[str],
    total_signals: int,
    filtered: int,
) -> None:
    elapsed = time.monotonic() - started_at
    rate = completed / elapsed if elapsed > 0 else 0.0
    errors = statuses["error"] + statuses["partial_error"]
    print(
        f"headerproof: completed={completed}/{total} rate={rate:.1f}/s "
        f"findings={total_signals} suppressed={filtered} errors={errors}",
        file=sys.stderr,
        flush=True,
    )


def _state(signal: dict[str, Any]) -> str:
    return str(signal.get("assessment", {}).get("state", "unverified"))


def emit_live_alert(url: str, signal: dict[str, Any], args: argparse.Namespace) -> None:
    if args.no_live_alerts or not alert_allowed(signal, args.min_alert_confidence):
        return

    payload = {"url": url, **signal}
    with ALERT_LOCK:
        if args.json:
            print(json.dumps(payload, sort_keys=True), flush=True)
            return

        severity = str(signal.get("severity", "info"))
        finding_type = str(signal.get("type", signal.get("check", "finding")))
        state = _state(signal)
        color_enabled = sys.stdout.isatty() and not args.no_color
        color = terminal_color(color_enabled, severity)
        reset = reset_color(color_enabled)
        print(f"{color}[{finding_type}] [{severity}] [{state}] {url}{reset}", flush=True)

        if args.verbose:
            assessment = signal.get("assessment", {})
            reasons = assessment.get("reasons", [])
            missing = assessment.get("missing_proof", [])
            details: list[str] = []
            if reasons:
                details.append("evidence=" + "; ".join(shorten(item, 120) for item in reasons[:2]))
            if missing:
                details.append("missing=" + "; ".join(shorten(item, 120) for item in missing[:2]))
            if details:
                print("  " + " | ".join(details), flush=True)


def ui_kv(label: str, value: Any) -> str:
    return f"{label}: {value}"


def ui_box(title: str, lines: list[str], color: str = "", stream: Any | None = None) -> None:
    """Compatibility helper retained for callers outside the primary CLI."""
    stream = sys.stderr if stream is None else stream
    reset = reset_color(bool(color))
    with ALERT_LOCK:
        print(color + title + reset, file=stream)
        for line in lines:
            print(str(line), file=stream)
