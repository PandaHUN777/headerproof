# Roadmap

HeaderProof follows three rules: reduce false positives, keep normal usage memorable, and keep output pipe-friendly.

## Phase status

### Phase 0 — Presentation and evidence language
Completed in the current implementation:
- README is kept under 40 lines and avoids banners/marketing copy.
- Verified findings use one grep-friendly line.
- Evidence states use factual terms such as observed, reproduced, and cross_request_confirmed.
- Verbose output adds compact evidence notes instead of conversational blocks.

### Phase 1 — One default CLI
Completed:
- Positional target, -l/--list, and stdin input.
- Bounded concurrency, per-host -rl/--rate-limit, -severity, -silent, -json, and -v/--verbose.
- One default scan behavior; profile selection is not part of the public CLI.
- Optional advanced settings live in headerproof.yaml.

### Phase 2 — Declarative detectors
Completed:
- CORS, CSRF, CRLF/header injection, cache poisoning, and content spoofing definitions declare request primitive, matcher, extractor, assessment, and verification metadata in templates.
- Specialized multi-request proof workflows remain bounded engine primitives; a generic same-target `http` request kind lets new safe GET/HEAD/OPTIONS detector classes define query/header probes, matchers, extractors, finding metadata, and evidence gates without Python detector changes.
- Template validation rejects unsupported request fields, unsafe state-changing generic methods, invalid finding metadata, and unsupported manifest schema versions before installation.
- The separately versioned `headerproof-templates` repository is published and its current `core.yaml` matches the bundled template payload.
- `-update-templates` was verified against the published manifest and validates downloaded templates before atomically replacing local files.
- Regression coverage includes a template-only detector with a new check name that performs a canary probe and reaches `reproduced` without adding Python detector code.

### Phase 3 — OOB and reproducible validation
Implemented:
- Self-hosted DNS/HTTP OOB callbacks and proof-gated OOB findings, including an end-to-end scanner -> target -> callback -> finding regression test.
- Real Varnish and nginx cache fixtures.
- Reproducible controlled cache measurements with provider-specific cache-hit semantics.
- Cloudflare/Fastly fixture inputs with provider-fingerprint validation so an arbitrary endpoint cannot be mislabeled as a CDN measurement.
- Reproducible real-provider fixtures: Cloudflare Workers temporary deployments and Fastly Fiddle ephemeral VCL services.
- Authorized known-vulnerable-lab recall harness plus an isolated official DVWA low-CSRF measurement in CI.

Measured controlled cache corpus on 2026-09-26: TP=2, TN=4, FP=0, FN=0, precision=1.0, recall=1.0.
Measured DVWA low-CSRF case on 2026-09-26: expected=1, detected=0, FN=1, detection recall=0.0. The existing SameSite observation is not credited as proof of the missing form token.
Measured Cloudflare Workers temporary fixture on 2026-09-26: TP=0, TN=2, FP=0, FN=1, precision=0.0, recall=0.0.
Measured Fastly Fiddle real-edge fixture on 2026-09-26: TP=0, TN=2, FP=0, FN=1, precision=0.0, recall=0.0.

Phase 3 is complete as a validation phase: all requested provider/lab measurements now have reproducible harnesses and published results. The two external-CDN false negatives are retained as measured limitations rather than converted into unsupported confirmations.

### Phase 4 — Distribution
Implemented:
- PyInstaller single-file build path.
- Linux amd64/arm64, macOS amd64/arm64, and Windows amd64 release matrix.
- Release checksums and Sigstore/Cosign signature bundle.
- Binary-first install.sh, Python distributions, and multi-architecture container workflow.

Remaining:
- Publish and verify the v1.4.0 release after the implementation branch is accepted into the release branch.

### Phase 5 — CI consumption
Implemented:
- stdout findings / stderr operational logs.
- SARIF 2.1.0 export.
- Exit codes: no finding 0, finding 1, scan error 2.
- Independently versioned evidence schema compatibility policy.

Remaining:
- Publish the separately versioned headerproof-action repository. This is outside work scoped only to this repository.

### Phase 6 — Project proof and contributor path
Implemented:
- Short asciinema terminal recording.
- Factual role comparison with Nuclei, Corsy, and ffuf.
- Concrete template contribution guide.

Remaining:
- Add one redacted real finding from an explicitly permitted program. No example will be fabricated or taken from an unverified target.

### Phase 7 — Discovery and contribution backlog
Implemented:
- GitHub topics include appsec, recon, and red-team.
- Eight scoped good first issue tickets exist in this repository.
- v1.4.0 release notes are prepared.

Remaining:
- External awesome-list pull requests require permission to modify repositories outside HeaderProof and are not performed under the current repository-only scope.
- Publish final v1.4.0 release notes with the release.

## Acceptance rule

A feature is accepted only when it improves proof quality, reduces false positives, or makes verified evidence easier to consume. Measurements must name their corpus; controlled-fixture results are never presented as internet-wide accuracy claims.
