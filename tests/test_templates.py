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

    (source / "manifest.json").write_text(json.dumps({"files": ["core.yaml"]}))
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
