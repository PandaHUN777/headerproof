from __future__ import annotations

import os
import uuid

import pytest

from headerproof.cli import parse_cli_args
from headerproof.engine import scan_url

FIXTURES = [
    ("varnish", os.environ.get("HEADERPROOF_VARNISH_FIXTURE", "")),
    ("nginx", os.environ.get("HEADERPROOF_NGINX_FIXTURE", "")),
    ("cloudflare", os.environ.get("HEADERPROOF_CLOUDFLARE_FIXTURE", "")),
    ("fastly", os.environ.get("HEADERPROOF_FASTLY_FIXTURE", "")),
]
AVAILABLE = [(name, base) for name, base in FIXTURES if base]


def scan(base: str, path: str) -> dict[str, object]:
    args = parse_cli_args([f"{base.rstrip('/')}{path}?case={uuid.uuid4().hex}"])
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


@pytest.mark.skipif(not AVAILABLE, reason="real cache fixtures are not configured")
@pytest.mark.parametrize(("implementation", "base"), AVAILABLE)
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/vulnerable", True),
        ("/safe", False),
        ("/clean", False),
    ],
)
def test_real_cache_fixture_matrix(implementation: str, base: str, path: str, expected: bool) -> None:
    result = scan(base, path)
    confirmed = "cache_poisoning_shared_cache_confirmed" in finding_types(result)
    assert confirmed is expected, f"{implementation} {path}: expected confirmed={expected}"
