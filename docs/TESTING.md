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

## Cache fixture measurement

The CI cache corpus runs the same vulnerable, keyed-safe, and `no-store` cases through real Varnish 7.7 and nginx 1.28 proxy caches.

On 2026-09-26 the six-case corpus produced: TP=2, TN=4, FP=0, FN=0, precision=1.0, recall=1.0. These numbers describe only this controlled cache corpus; they are not a claim about arbitrary internet targets.

Cloudflare and Fastly endpoints are supported by the integration harness through `HEADERPROOF_CLOUDFLARE_FIXTURE` and `HEADERPROOF_FASTLY_FIXTURE`, but no measurement is published until real controlled endpoints are configured.

PortSwigger Academy and DVWA false-negative measurements remain separate from this cache corpus and must not be inferred from these numbers. `tests/integration/measure_known_vulnerable.py` accepts an authorized lab manifest and reports expected detector types, observed candidates, promoted findings, false negatives, and detection recall. Authenticated lab sessions can be supplied through `headerproof.yaml` `request_headers` without copying header values into run metadata.
