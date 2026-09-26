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
Completed and release-verified:
- PyInstaller single-file build path.
- Linux amd64/arm64, macOS amd64/arm64, and Windows amd64 release matrix; all five v1.4.1 binaries passed native `--version` and `--help` smoke tests in GitHub Actions.
- Published v1.4.1 GitHub Release with all five binaries, wheel, sdist, SHA-256 checksums, and a Sigstore/Cosign checksum signature bundle.
- Binary-first `install.sh`; a clean latest-release Linux install passed checksum verification, `--version`, and `--help`.
- Public multi-architecture linux/amd64 + linux/arm64 GHCR image. Anonymous registry-token and OCI-index retrieval verified both architectures for v1.4.1; the release workflow also keyless-signed the published image digest.
- PyPI remains an optional secondary channel. Its Trusted Publishing job is implemented and safely disabled until a PyPI pending/trusted publisher is configured; the primary binary and official container distribution paths do not depend on it.

Phase 4 is complete. The release binary is the primary installation path; PyPI is intentionally non-blocking.

### Phase 5 — CI consumption

#### Phase 5A — CLI/CI contract — complete
- Findings/machine output stay on stdout; operational logs stay on stderr.
- SARIF 2.1.0 export is available on stdout and as `.sarif` output.
- Stable exit codes: no finding 0, finding 1, scan error 2; operator interrupt 130.
- Contract regression tests cover SARIF stream separation and exit-code precedence.
- `docs/CI.md` documents shell/CI consumption without coupling policy to the scanner.

#### Phase 5B — Action and evidence compatibility — complete
- Published evidence schemas are hash-locked in `schemas/manifest.json`; tests bind the runtime `SCHEMA_VERSION` to the manifest and reject in-place edits or untracked schema files.
- Evidence schema v1.2 is unchanged across HeaderProof v1.4.0 and v1.4.1, proving scanner releases can advance independently from the evidence contract.
- HeaderProof Action v1.0.0 is independently versioned with the stable `v1` major tag.
- Action E2E CI installs the published HeaderProof v1.4.1 binary and verifies controlled no-finding (`0`) and reproduced-finding (`1`) SARIF paths.
- The action preserves scan error (`2`) and other non-zero process exits instead of silently converting them to success.

### Phase 6 — Project proof and contributor path
Implemented:
- Short asciinema v2 terminal recording backed by a controlled localhost fixture and a regression test for the compact output contract.
- Factual, non-ranking role comparison with Nuclei, Corsy, and ffuf.
- Concrete template contribution guide plus documentation-evidence rules separating fixtures, known-vulnerable labs, and real findings.
- `docs/PROJECT_PROOF.md` records the reproducible demo boundary and the minimum evidence/publication checklist for a future real-world case study.
- Documentation contract tests keep the README at 40 lines or fewer and prevent the controlled demo from being mislabeled as a real finding.

Remaining external evidence:
- Add one redacted real finding from an explicitly permitted program once disclosure/publication is allowed. No example will be fabricated, promoted from a fixture, or taken from an unverified target.

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
