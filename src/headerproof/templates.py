from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib import request

TEMPLATE_SCHEMA_VERSION = 1
BUNDLED_TEMPLATE_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_BASE_URL = (
    "https://raw.githubusercontent.com/TayfurYldz/headerproof-templates/main/templates"
)


class TemplateError(ValueError):
    pass


def user_template_dir() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return base / "headerproof" / "templates"


def _read_template_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateError(f"invalid template file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TemplateError(f"template file must contain an object: {path}")
    return payload


def validate_template(payload: dict[str, Any], source: str = "") -> dict[str, Any]:
    required = {"id", "check", "request", "matchers", "extractors", "assessment", "verification"}
    missing = sorted(required - payload.keys())
    if missing:
        raise TemplateError(f"{source or payload.get('id', 'template')}: missing {', '.join(missing)}")
    if not isinstance(payload["id"], str) or not payload["id"].strip():
        raise TemplateError(f"{source}: template id must be a non-empty string")
    if not isinstance(payload["request"], dict):
        raise TemplateError(f"{source}: request must be an object")
    if not isinstance(payload["matchers"], list):
        raise TemplateError(f"{source}: matchers must be a list")
    if not isinstance(payload["extractors"], list):
        raise TemplateError(f"{source}: extractors must be a list")
    assessment = payload["assessment"]
    if not isinstance(assessment, dict):
        raise TemplateError(f"{source}: assessment must be an object")
    for key in ("default_state", "gate", "missing_proof"):
        if key not in assessment:
            raise TemplateError(f"{source}: assessment.{key} is required")
    if not isinstance(assessment["gate"], list):
        raise TemplateError(f"{source}: assessment.gate must be a list")
    verification = payload["verification"]
    if not isinstance(verification, dict) or "report_gate" not in verification:
        raise TemplateError(f"{source}: verification.report_gate is required")
    return payload


def _iter_template_paths() -> list[Path]:
    paths = sorted(BUNDLED_TEMPLATE_DIR.glob("*.yaml"))
    override_dir = user_template_dir()
    if override_dir.is_dir():
        overrides = {path.name: path for path in override_dir.glob("*.yaml")}
        paths = [overrides.get(path.name, path) for path in paths]
        known = {path.name for path in paths}
        paths.extend(path for name, path in sorted(overrides.items()) if name not in known)
    return paths


@lru_cache(maxsize=1)
def load_templates() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for path in _iter_template_paths():
        payload = _read_template_file(path)
        entries = payload.get("templates", [payload])
        if not isinstance(entries, list):
            raise TemplateError(f"{path}: templates must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise TemplateError(f"{path}: template entry must be an object")
            template = validate_template(entry, str(path))
            template_id = template["id"]
            if template_id in loaded:
                raise TemplateError(f"duplicate template id: {template_id}")
            loaded[template_id] = template
    return loaded


def reload_templates() -> dict[str, dict[str, Any]]:
    load_templates.cache_clear()
    return load_templates()


def get_template(signal_type: str) -> dict[str, Any] | None:
    return load_templates().get(signal_type)


def _path_value(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def evaluate_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    op = str(condition.get("op", "truthy"))
    path = str(condition.get("path", ""))
    value = _path_value(context, path) if path else None
    if op == "truthy":
        return bool(value)
    if op == "falsey":
        return not bool(value)
    if op == "equals":
        return value == condition.get("value")
    if op == "not_equals":
        return value != condition.get("value")
    if op == "all_true":
        return isinstance(value, dict) and bool(value) and all(bool(item) for item in value.values())
    if op == "status_recorded":
        return isinstance(context.get("status"), int)
    if op == "always":
        return bool(condition.get("value", True))
    raise TemplateError(f"unknown condition operator: {op}")


def evaluate_gate(template: dict[str, Any], context: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    assessment = template["assessment"]
    named_checks = assessment.get("gate_checks", {})
    checks = {
        name: evaluate_condition(condition, context)
        for name, condition in named_checks.items()
        if isinstance(condition, dict)
    }
    gate_conditions = assessment.get("gate", [])
    passed = bool(gate_conditions) and all(
        evaluate_condition(condition, context)
        for condition in gate_conditions
        if isinstance(condition, dict)
    )
    return passed, checks


def update_templates(base_url: str | None = None) -> tuple[int, Path]:
    base = (base_url or os.environ.get("HEADERPROOF_TEMPLATE_BASE_URL") or DEFAULT_TEMPLATE_BASE_URL).rstrip("/")
    manifest_url = f"{base}/manifest.json"
    try:
        with request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise TemplateError(f"template update failed: {exc}") from exc

    files = manifest.get("files", []) if isinstance(manifest, dict) else []
    if not isinstance(files, list) or not files:
        raise TemplateError("template manifest contains no files")

    destination = user_template_dir()
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for name in files:
        if not isinstance(name, str) or "/" in name or not name.endswith(".yaml"):
            raise TemplateError(f"invalid template manifest entry: {name!r}")
        try:
            with request.urlopen(f"{base}/{name}", timeout=10) as response:
                raw = response.read()
        except Exception as exc:
            raise TemplateError(f"failed to download {name}: {exc}") from exc
        payload = json.loads(raw.decode("utf-8"))
        validate_template(payload, name)
        (destination / name).write_bytes(raw)
        downloaded += 1
    reload_templates()
    return downloaded, destination
