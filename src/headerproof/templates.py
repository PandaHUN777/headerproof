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

REQUEST_KINDS = {
    "baseline",
    "preflight",
    "origin-probe",
    "query-probe",
    "header-probe",
    "cache-state-machine",
    "crlf-query-probe",
    "header-oob-probe",
}
MATCHER_CONTEXT_KEYS = {
    "exact-origin-reflection": "reflected",
    "credentials-true": "credentials",
    "credentials-false": "credentials_missing",
    "acao-wildcard": "wildcard",
    "origin-reflection": "reflected",
    "cacheable": "cacheable",
    "vary-origin-missing": "vary_origin_missing",
    "cookie-samesite-missing": "samesite_missing",
    "auth-cookie-cross-site": "auth_cookie_cross_site",
    "auth-cookie": "auth_cookie",
    "unsafe-methods": "unsafe_methods",
    "samesite-none": "samesite_none",
    "secure-missing": "secure_missing",
    "canary-security-header": "security_header_hits",
    "security-header-missing": "security_header_missing",
    "canary-response-header": "header_hits",
    "canary-text-body": "textual_body_hits",
    "canary-reflection": "locations",
    "cache-indicator": "cacheable",
    "clean-follow-up-canary": "victim_locations",
    "shared-cache-confirmed": "shared_cache_confirmed",
    "shared-cache-unconfirmed": "shared_cache_unconfirmed",
    "parsed-injected-header": "injected_header_seen",
    "oob-callback-observed": "oob_confirmed",
}
EXTRACTOR_CONTEXT_KEYS = {
    "acao": "access_control_allow_origin",
    "acac": "credentials",
    "methods": "unsafe_methods",
    "cache-indicators": "cache_indicators",
    "cookie-name": "cookie_name",
    "likely-auth": "likely_auth_cookie",
    "secure": "secure",
    "samesite": "samesite",
    "unsafe-methods": "unsafe_methods",
    "cookie-names": "cookie_names",
    "locations": "locations",
    "state-machine-checks": "state_machine_checks",
    "shared-cache-hit-markers": "shared_cache_hit_markers",
    "injected-header-values": "injected_header_values",
    "protocols": "protocols",
    "event-count": "event_count",
}


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
    request_kind = payload["request"].get("kind")
    if request_kind not in REQUEST_KINDS:
        raise TemplateError(f"{source}: unsupported request kind: {request_kind}")
    if not isinstance(payload["matchers"], list):
        raise TemplateError(f"{source}: matchers must be a list")
    unknown_matchers = [item for item in payload["matchers"] if item not in MATCHER_CONTEXT_KEYS]
    if unknown_matchers:
        raise TemplateError(f"{source}: unknown matcher(s): {', '.join(map(str, unknown_matchers))}")
    if not isinstance(payload["extractors"], list):
        raise TemplateError(f"{source}: extractors must be a list")
    unknown_extractors = [item for item in payload["extractors"] if item not in EXTRACTOR_CONTEXT_KEYS]
    if unknown_extractors:
        raise TemplateError(f"{source}: unknown extractor(s): {', '.join(map(str, unknown_extractors))}")
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


def validate_template_document(payload: dict[str, Any], source: str = "") -> list[dict[str, Any]]:
    entries = payload.get("templates", [payload])
    if not isinstance(entries, list) or not entries:
        raise TemplateError(f"{source}: templates must be a non-empty list")
    validated: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise TemplateError(f"{source}: template entry must be an object")
        validated.append(validate_template(entry, source))
    return validated


def template_matches(signal_type: str, context: dict[str, Any]) -> bool:
    template = get_template(signal_type)
    if template is None:
        return False
    matchers = template.get("matchers", [])
    return bool(matchers) and all(bool(context.get(MATCHER_CONTEXT_KEYS[str(name)])) for name in matchers)


def extract_template_evidence(signal_type: str, context: dict[str, Any]) -> dict[str, Any]:
    template = get_template(signal_type)
    if template is None:
        return {}
    evidence: dict[str, Any] = {}
    for extractor in template.get("extractors", []):
        key = EXTRACTOR_CONTEXT_KEYS[str(extractor)]
        if key in context:
            evidence[key] = context[key]
    return evidence


def templates_for_request(kind: str, checks: set[str] | None = None) -> list[dict[str, Any]]:
    return [
        template
        for template in load_templates().values()
        if template.get("request", {}).get("kind") == kind
        and (checks is None or template.get("check") in checks)
    ]


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
        for template in validate_template_document(payload, str(path)):
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
        if not isinstance(payload, dict):
            raise TemplateError(f"{name}: template document must be an object")
        validate_template_document(payload, name)
        (destination / name).write_bytes(raw)
        downloaded += 1
    reload_templates()
    return downloaded, destination
