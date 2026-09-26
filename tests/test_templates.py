from __future__ import annotations

import json
from pathlib import Path

import pytest

from headerproof.templates import (
    TemplateError,
    evaluate_condition,
    get_template,
    reload_templates,
    update_templates,
    user_template_dir,
    validate_template,
)


def test_bundled_templates_cover_proof_gates() -> None:
    cache = get_template("cache_poisoning_shared_cache_confirmed")
    crlf = get_template("response_splitting_crlf_candidate")

    assert cache is not None
    assert crlf is not None
    assert cache["request"]["kind"] == "cache-state-machine"
    assert crlf["matchers"] == ["canary-reflection"]
    assert {item.get("path") for item in crlf["assessment"]["gate"]} >= {"evidence.injected_header_seen"}


def test_condition_dsl_handles_nested_evidence() -> None:
    context = {"status": 200, "evidence": {"confirmed": True, "checks": {"a": True, "b": True}}}

    assert evaluate_condition({"op": "status_recorded"}, context) is True
    assert evaluate_condition({"op": "truthy", "path": "evidence.confirmed"}, context) is True
    assert evaluate_condition({"op": "all_true", "path": "evidence.checks"}, context) is True


def test_invalid_template_is_rejected() -> None:
    with pytest.raises(TemplateError, match="missing"):
        validate_template({"id": "broken"}, "broken.yaml")


def test_update_templates_from_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    bundled = get_template("response_splitting_crlf_candidate")
    assert bundled is not None
    payload = {**bundled, "title": "updated fixture"}

    (source / "manifest.json").write_text(json.dumps({"schema_version": 1, "files": ["core.yaml"]}))
    (source / "core.yaml").write_text(json.dumps(payload))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    count, destination = update_templates(source.as_uri())

    assert count == 1
    assert destination == user_template_dir()
    assert (destination / "core.yaml").exists()
    assert get_template("response_splitting_crlf_candidate")["title"] == "updated fixture"

    (destination / "core.yaml").unlink()
    reload_templates()


def test_template_matchers_and_extractors_are_executable() -> None:
    from headerproof.templates import extract_template_evidence, template_matches

    context = {
        "reflected": True,
        "credentials": True,
        "access_control_allow_origin": "https://probe.invalid",
        "unsafe_methods": ["POST"],
    }
    assert template_matches("cors_arbitrary_origin_with_credentials", context) is True
    assert extract_template_evidence("cors_arbitrary_origin_with_credentials", context) == {
        "access_control_allow_origin": "https://probe.invalid",
        "credentials": True,
        "unsafe_methods": ["POST"],
    }


def test_template_document_accepts_bundled_multi_template_file() -> None:
    from headerproof.templates import validate_template_document

    payload = json.loads((Path(__file__).parents[1] / "src" / "headerproof" / "core.yaml").read_text())
    validated = validate_template_document(payload, "core.yaml")
    assert len(validated) >= 15


def test_http_template_adds_new_detector_without_python_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlsplit

    from headerproof.cli import parse_cli_args
    from headerproof.engine import scan_url

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            value = parse_qs(urlsplit(self.path).query).get("phase2_probe", [""])[0]
            self.send_response(200)
            self.send_header("X-Phase2-Echo", value)
            self.end_headers()

        def log_message(self, _format: str, *args: object) -> None:
            return

    template = {
        "id": "phase2_template_only_detector",
        "check": "template-only-check",
        "request": {
            "kind": "http",
            "method": "GET",
            "query": {"phase2_probe": "{{canary}}"},
            "headers": {"X-Phase2-Probe": "{{canary}}"},
        },
        "matchers": [
            {"op": "contains", "path": "response.headers.x-phase2-echo", "value": "{{canary}}"}
        ],
        "extractors": [
            {"name": "reflected_value", "path": "response.headers.x-phase2-echo"}
        ],
        "finding": {
            "severity": "high",
            "confidence": "high",
            "title": "Template-only detector reproduced its canary",
            "next_step": "Validate the behavior independently before reporting.",
        },
        "assessment": {
            "default_state": "observed",
            "passed_state": "reproduced",
            "gate": [{"op": "truthy", "path": "evidence.reflected_value"}],
            "gate_checks": {
                "reflection_recorded": {"op": "truthy", "path": "evidence.reflected_value"}
            },
            "reasons": ["template matcher observed the configured response value"],
            "passed_reasons": ["template evidence gate reproduced the configured response value"],
            "missing_proof": ["template evidence gate did not reproduce"],
            "passed_missing_proof": [],
        },
        "verification": {
            "objective": "Validate the template-only detector independently.",
            "automated_checks": ["Record the configured request and response."],
            "manual_confirmation": ["Repeat with a fresh canary."],
            "report_gate": "Require independent impact validation before reporting.",
        },
    }

    data_home = tmp_path / "data"
    template_dir = data_home / "headerproof" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "phase2.yaml").write_text(json.dumps(template), encoding="utf-8")
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    reload_templates()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    try:
        args = parse_cli_args([url, "-silent"])
        assert "template-only-check" not in args.enabled_checks
        result = scan_url(url, args)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        reload_templates()

    signals = [item for item in result["signals"] if item["type"] == "phase2_template_only_detector"]
    assert len(signals) == 1
    assert signals[0]["check"] == "template-only-check"
    assert signals[0]["assessment"]["technical_gate"] == "passed"
    assert signals[0]["assessment"]["state"] == "reproduced"
    assert signals[0]["evidence"]["reflected_value"].startswith("pa-scan-")


def test_http_template_rejects_state_changing_methods() -> None:
    template = {
        "id": "unsafe-template",
        "check": "custom",
        "request": {"kind": "http", "method": "POST"},
        "matchers": [{"op": "status_recorded"}],
        "extractors": [],
        "finding": {"severity": "high", "confidence": "high", "title": "unsafe"},
        "assessment": {"default_state": "observed", "gate": [], "missing_proof": []},
        "verification": {"report_gate": "manual"},
    }
    with pytest.raises(TemplateError, match="method must be one of"):
        validate_template(template, "unsafe.yaml")


def test_update_templates_rejects_unknown_manifest_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source-bad-schema"
    source.mkdir()
    (source / "manifest.json").write_text(json.dumps({"schema_version": 999, "files": ["core.yaml"]}))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data-bad-schema"))

    with pytest.raises(TemplateError, match="unsupported template manifest schema"):
        update_templates(source.as_uri())
