from __future__ import annotations

import os
import uuid

import pytest

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url

BASE = os.environ.get("HEADERPROOF_CACHE_FIXTURE", "")
pytestmark = pytest.mark.skipif(not BASE, reason="real cache fixture is not running")


def scan(path: str) -> dict[str, object]:
    args = parse_cli_args([f"{BASE.rstrip('/')}{path}?case={uuid.uuid4().hex}"])
    args.enabled_checks = {"header-injection", "cache-poisoning"}
    args.header_probe_limit = 1
    args.per_url_concurrency = 1
    args.concurrency = 1
    args.url_timeout = 9.0
    return scan_url(args.target, args)


def finding_types(result: dict[str, object]) -> set[str]:
    signals = result["signals"]
    assert isinstance(signals, list)
    return {str(item["type"]) for item in signals if isinstance(item, dict)}


def test_varnish_unkeyed_header_fixture_is_confirmed() -> None:
    result = scan("/vulnerable")
    assert "cache_poisoning_shared_cache_confirmed" in finding_types(result)


def test_varnish_keyed_header_fixture_is_suppressed() -> None:
    result = scan("/safe")
    assert "cache_poisoning_shared_cache_confirmed" not in finding_types(result)


def test_no_store_fixture_has_no_cache_confirmation() -> None:
    result = scan("/clean")
    assert "cache_poisoning_shared_cache_confirmed" not in finding_types(result)
