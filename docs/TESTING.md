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

Cloudflare and Fastly endpoints are supported by the integration harness through `HEADERPROOF_CLOUDFLARE_FIXTURE` and `HEADERPROOF_FASTLY_FIXTURE`, or the matching manual CI inputs. External CDN measurements are rejected unless provider-specific response headers verify that the endpoint is actually traversing the named CDN. No Cloudflare/Fastly precision number is published until controlled endpoints are configured.

Provider cache-hit semantics are interpreted independently. Fastly multi-node `X-Cache` values count any `HIT` component as cache-served evidence; Cloudflare `HIT`, `STALE`, `UPDATING`, and `REVALIDATED` are cache-served/validated states, while `MISS`, `BYPASS`, `DYNAMIC`, and `EXPIRED` are not promoted as hit evidence.

## Known-vulnerable recall

CI runs the official DVWA container at the `low` security level with authentication disabled only inside the isolated runner. The measurement first verifies ground truth from the rendered page: the password-change form uses `GET`, contains the password-change fields, and has no anti-CSRF token. It then scans the same page with HeaderProof.

On 2026-09-26 this case produced: expected=1, detected=0, false negatives=1, detection recall=0.0. HeaderProof observed `csrf_cookie_samesite_missing`, but that cookie-hardening observation is deliberately not credited as detection of the missing form token. This documents a real false-negative boundary instead of inflating CSRF recall.

`tests/integration/measure_known_vulnerable.py` remains available for additional authorized lab manifests, including PortSwigger Academy instances. Authenticated lab sessions can be supplied through `headerproof.yaml` `request_headers` without copying header values into run metadata.
