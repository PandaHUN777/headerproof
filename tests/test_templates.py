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
    assert crlf["matchers"] == ["parsed-injected-header"]


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
