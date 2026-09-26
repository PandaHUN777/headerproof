# Contributing

HeaderProof accepts changes that reduce false positives, improve evidence quality, or make verified output easier to consume.

## Before you start

- Pick an open `good first issue` or `help wanted` task when possible and comment before starting. A maintainer will confirm that the scope is still current.
- Use Discussions → Ideas for new features or detector behavior. Use Discussions → General for a larger contribution plan that is not already scoped.
- Keep pull requests focused. Do not bundle unrelated cleanup, refactors, and feature work.
- New specialized active-scanning primitives require design agreement before implementation.
- Read [the maintainer policy](docs/MAINTAINERS.md) for intake, review, labels, and release expectations.

## Pull requests

Link the accepted issue or Discussion when one exists. Explain the behavior change, the proof/safety boundary when detection changes, and the validation you ran. Maintainers may ask for a large change to be split into independently reviewable commits or pull requests.

A green CI run is necessary but not sufficient for merge: the change must preserve conservative evidence gates, remain maintainable, and match the accepted scope.

## Add or change a detector template

Detector definitions belong in the separately distributed `headerproof-templates` set. HeaderProof supports two template paths:

1. Use an existing bounded primitive (`baseline`, `preflight`, `origin-probe`, `query-probe`, `header-probe`, `cache-state-machine`, `crlf-query-probe`, or `header-oob-probe`) when the detector needs HeaderProof's specialized multi-request evidence logic.
2. Use `request.kind: http` for a new same-target detector that can be expressed as a safe `GET`, `HEAD`, or `OPTIONS` request. `headers` and `query` accept `{{canary}}`, `{{hostname}}`, and `{{url}}` variables, so adding this class of detector does not require Python changes.

A generic HTTP template defines condition-object `matchers`, path-based `extractors`, finding metadata, and an independent `assessment.gate`. The matcher decides whether an observation exists; the gate decides whether it can become a finding.

```json
{
  "id": "example_header_reflection",
  "check": "example",
  "request": {
    "kind": "http",
    "method": "GET",
    "query": {"probe": "{{canary}}"}
  },
  "matchers": [
    {"op": "contains", "path": "response.headers.x-example", "value": "{{canary}}"}
  ],
  "extractors": [
    {"name": "reflected_value", "path": "response.headers.x-example"}
  ],
  "finding": {
    "severity": "high",
    "confidence": "high",
    "title": "Configured canary was reproduced"
  },
  "assessment": {
    "default_state": "observed",
    "passed_state": "reproduced",
    "gate": [{"op": "truthy", "path": "evidence.reflected_value"}],
    "missing_proof": ["configured response evidence was not reproduced"],
    "passed_missing_proof": []
  },
  "verification": {
    "report_gate": "Require independent impact validation before reporting."
  }
}
```

Keep `missing_proof` explicit. Technical reproduction must not be described as victim impact. State-changing methods are intentionally rejected by the generic executor; specialized active workflows stay in bounded engine primitives.

Add a focused test in `tests/test_templates.py`. A new generic HTTP detector must prove that it works without adding Python detector code.

## Documentation evidence

Keep controlled fixtures, known-vulnerable labs, and real-world findings clearly separated. A real finding example requires an explicitly permitted program and enough redacted request/response evidence to support the stated HeaderProof finding type and evidence state. Do not present synthetic or unverified targets as real findings. See `docs/PROJECT_PROOF.md` for the publication checklist.

## Local checks
```bash
python3 -m compileall -q header_active_scan.py src/headerproof
python3 -m ruff check header_active_scan.py src/headerproof tests
python3 -m mypy
python3 -m pytest -q
python3 -m pytest -q --cov=headerproof.detectors --cov=headerproof.evidence --cov-branch --cov-fail-under=95
```
