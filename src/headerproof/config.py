from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_NAME = "headerproof.yaml"
LIST_KEYS = {"origins", "headers"}
MAPPING_KEYS = {"request_headers"}
SCALAR_KEYS = {"concurrency", "rate_limit", "severity", "timeout", "oob_api", "oob_domain"}
ALLOWED_KEYS = LIST_KEYS | MAPPING_KEYS | SCALAR_KEYS


class ConfigError(ValueError):
    pass


def _scalar(value: str) -> str | int | float:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    active_list: str | None = None
    active_map: str | None = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if active_list is None:
                raise ConfigError(f"line {line_number}: list item without a key")
            result.setdefault(active_list, []).append(str(_scalar(stripped[2:])))
            continue
        if raw[:1].isspace() and active_map is not None and ":" in stripped:
            subkey, subvalue = (part.strip() for part in stripped.split(":", 1))
            if not subkey or not subvalue:
                raise ConfigError(f"line {line_number}: request header requires name and value")
            result.setdefault(active_map, {})[subkey] = str(_scalar(subvalue))
            continue
        if ":" not in stripped:
            raise ConfigError(f"line {line_number}: expected key: value")
        key, value = (part.strip() for part in stripped.split(":", 1))
        if key not in ALLOWED_KEYS:
            raise ConfigError(f"line {line_number}: unknown config key: {key}")
        if not value:
            if key in LIST_KEYS:
                result[key] = []
                active_list = key
                active_map = None
                continue
            if key in MAPPING_KEYS:
                result[key] = {}
                active_map = key
                active_list = None
                continue
            raise ConfigError(f"line {line_number}: {key} requires a value")
        active_list = None
        active_map = None
        if key in LIST_KEYS:
            result[key] = [item.strip() for item in value.split(",") if item.strip()]
        else:
            result[key] = _scalar(value)
    return result


def load_config(path: Path | None = None) -> tuple[dict[str, Any], Path | None]:
    config_path = path or Path.cwd() / DEFAULT_CONFIG_NAME
    if not config_path.is_file():
        return {}, None
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {config_path}: {exc}") from exc

    try:
        payload = json.loads(text) if text.lstrip().startswith("{") else _parse_simple_yaml(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON-compatible config {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError(f"{config_path}: config must be an object")

    unknown = set(payload) - ALLOWED_KEYS
    if unknown:
        raise ConfigError(f"{config_path}: unknown config key(s): {', '.join(sorted(unknown))}")
    for key in LIST_KEYS:
        if key in payload and (
            not isinstance(payload[key], list) or not all(isinstance(item, str) for item in payload[key])
        ):
            raise ConfigError(f"{config_path}: {key} must be a list of strings")
    for key in MAPPING_KEYS:
        if key in payload and (
            not isinstance(payload[key], dict)
            or not all(isinstance(name, str) and isinstance(value, str) for name, value in payload[key].items())
        ):
            raise ConfigError(f"{config_path}: {key} must be a string mapping")
    return payload, config_path
