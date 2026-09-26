# Evidence and testing

HeaderProof treats false positives as the primary failure mode. A detector may record an observation without promoting it to a finding.

## Evidence states

- `observed`: a relevant response property was seen once.
- `reproduced`: a detector-specific replay reproduced the technical primitive.
- `cross_request_confirmed`: independent request roles confirmed the primitive.

Impact remains a separate manual-validation concern.

## Local quality gates

```bash
python -m pytest -q
python -m ruff check src tests
python -m mypy src/headerproof
```

The integration suite includes origin/cache fixtures, timeout behavior, concurrency bounds, schema validation, and evidence serialization. Real Varnish/nginx/edge-cache fixtures and published precision/recall measurements remain tracked in the roadmap until the fixture matrix is reproducible in CI.
