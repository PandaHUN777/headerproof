# Contributing

HeaderProof accepts changes that reduce false positives, improve evidence quality, or make verified output easier to consume.

## Add or change a detector template

1. Start from the matching entry in `src/headerproof/core.yaml`.
2. Keep the detector on an existing bounded request primitive: `baseline`, `preflight`, `origin-probe`, `query-probe`, `header-probe`, `cache-state-machine`, `crlf-query-probe`, or `header-oob-probe`.
3. Select matcher and extractor primitives implemented by `src/headerproof/templates.py`. Unknown primitives are rejected when templates load.
4. Define the evidence gate separately from the matcher. A matcher may create an observation; the gate decides whether it can become a finding.
5. Keep `missing_proof` explicit. Technical reproduction must not be described as victim impact.
6. Add a focused test in `tests/test_templates.py` and a detector behavior test when the change affects evidence.

A template must contain `id`, `check`, `request`, `matchers`, `extractors`, `assessment`, and `verification`.

## Local checks

```bash
python3 -m compileall -q header_active_scan.py src/headerproof
python3 -m ruff check header_active_scan.py src/headerproof tests
python3 -m mypy
python3 -m pytest -q
python3 -m pytest -q --cov=headerproof.detectors --cov=headerproof.evidence --cov-branch --cov-fail-under=95
```
