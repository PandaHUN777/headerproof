from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tests" / "integration" / "measure_precision.py"
spec = importlib.util.spec_from_file_location("measure_precision", MODULE)
assert spec and spec.loader
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


def test_external_provider_fingerprints_are_strict() -> None:
    assert measure.provider_verified("cloudflare", {"cf-ray": "abc", "cf-cache-status": "HIT"})
    assert not measure.provider_verified("cloudflare", {"server": "cloudflare"})
    assert measure.provider_verified("fastly", {"x-served-by": "cache-1", "x-cache": "HIT, MISS"})
    assert not measure.provider_verified("fastly", {"x-cache": "HIT"})
    assert measure.provider_verified("varnish", {})
