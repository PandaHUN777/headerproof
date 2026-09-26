<p align="center">
  <img src="assets/headerproof-banner.png" alt="HeaderProof" width="100%">
</p>

<p align="center">
  <strong>Evidence-first active web security scanning.</strong><br>
  Reproduce the technical primitive before promoting a signal to a finding.
</p>

<p align="center">
  <a href="https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml"><img src="https://github.com/TayfurYldz/headerproof/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/TayfurYldz/headerproof/releases/latest"><img src="https://img.shields.io/github/v/release/TayfurYldz/headerproof?display_name=tag&sort=semver" alt="Latest release"></a>
  <a href="https://pypi.org/project/headerproof/"><img src="https://img.shields.io/pypi/v/headerproof" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/TayfurYldz/headerproof" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#why-headerproof">Why HeaderProof</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#checks">Checks</a> ·
  <a href="#evidence-model">Evidence</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#documentation">Docs</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

**HeaderProof** is an evidence-gated active scanner for header-driven web security issues. It targets **CORS, CSRF, header injection / response splitting, cache poisoning, and content spoofing** while treating false positives as a primary failure mode.

Most scanners are good at producing signals. HeaderProof is built around the harder question: **what technical evidence is strong enough to promote a signal into a finding?**

A detector can observe suspicious behavior without reporting it as a vulnerability. HeaderProof records the probe and observation, applies a detector-specific evidence gate, filters weak or incomplete proof, and only then emits a finding.

> [!IMPORTANT]
> HeaderProof proves technical behavior, not real-world victim impact. Every reported result still requires appropriate manual validation before disclosure.

## Why HeaderProof

| Principle | What it means |
| --- | --- |
| **Evidence before alerts** | A console finding is never emitted before its detector-specific technical gate passes. |
| **Lower false-positive noise** | Weak or incomplete signals remain auditable observations instead of becoming findings. |
| **Reproducible proof states** | Evidence progresses through explicit states such as `observed`, `reproduced`, and `cross_request_confirmed`. |
| **Cross-request verification** | Cache poisoning uses separated clean, poison, victim, and control request roles. |
| **Auditable runs** | Findings, observations, probes, coverage, and operational errors are persisted independently. |
| **Automation ready** | Stable exit codes plus JSONL, JSON, Markdown, and SARIF exports fit CI and recon pipelines. |
| **Extensible** | Declarative HTTP templates can add bounded same-target detectors without new Python detector code. |
| **Minimal runtime** | The Python package has no third-party runtime dependencies. |

## Quick start

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/TayfurYldz/headerproof/main/install.sh | sh
```

Verify the installation:

```bash
headerproof --version
```

You can also run the published container:

```bash
docker run --rm ghcr.io/tayfuryldz/headerproof:latest --version
```

### Scan a target

```bash
headerproof example.com
```

### Feed a recon pipeline

```bash
subfinder -silent | httpx -silent | headerproof -silent
```

### Filter and export

```bash
headerproof example.com -severity high,medium -o findings.jsonl
```

HeaderProof accepts a single target, target lists, and stdin streams, making it suitable for both focused verification and larger authorized workflows.

## Checks

HeaderProof currently focuses on five security areas:

| Check | Verification focus |
| --- | --- |
| **CORS** | Arbitrary and `null` origins, origin reflection, credential combinations, preflight behavior, and cache-relevant CORS signals. |
| **CSRF** | Authentication-cookie and unsafe-method indicators while deliberately avoiding claims that cookie hardening alone proves CSRF. |
| **Header injection** | Forwarding-header influence, response-header reflection, CRLF / response-splitting candidates, and optional OOB-capable probes. |
| **Cache poisoning** | Persistence across isolated poison/victim/control requests, cache-key separation, and cache-hit evidence. |
| **Content spoofing** | Controlled canary reflection in security-relevant response content and headers. |

The scanner intentionally favors **bounded probes and evidence quality** over broad, destructive request behavior.

## Evidence model

```text
                         ┌───────────────┐
Target ──► Baseline ──► Probes ──► Detector candidate
                                      │
                                      ▼
                               Evidence gate
                                ╱          ╲
                               ╱            ╲
                         gate passes      weak / failed
                             │                │
                             ▼                ▼
                    False-positive       Observation
                       filter             retained
                             │
                             ▼
                          Finding
```

### Evidence states

- **`observed`** — a relevant response property was seen.
- **`reproduced`** — detector-specific replay reproduced the technical primitive.
- **`cross_request_confirmed`** — independent request roles confirmed the primitive.

Technical reproduction and impact are intentionally separate. HeaderProof does not automatically convert a reproduced primitive into a claim about exploitable victim impact.

### Cache poisoning proof

Cache poisoning receives a stricter multi-request workflow. HeaderProof separates the request roles and verifies that the candidate behavior survives into the expected victim request while remaining absent from a fresh control path. Cache-hit semantics are interpreted independently for supported cache/CDN evidence.

This design is intended to distinguish a reflected request header from actual shared-cache persistence.

## Output

The default output is intentionally compact and grep-friendly:

```text
[response_splitting_crlf_candidate] [high] [reproduced] https://example.com/path
```

Use:

- `-json` for JSONL output.
- `-sarif` for SARIF.
- `-v` for compact proof notes.
- `-o` to write findings to a file.

Findings use **stdout**; operational messages use **stderr**, so pipelines can consume results without mixing them with scanner status messages.

### Run evidence

Evidence is stored under:

```text
${XDG_STATE_HOME:-~/.local/state}/headerproof/runs/
└── <run>/
    ├── results.jsonl
    ├── signals.jsonl
    ├── observations.jsonl
    ├── probes.jsonl
    ├── coverage.jsonl
    └── errors.jsonl
```

The separation matters: a probe can be attempted, produce an observation, fail a proof gate, and remain available for later review without polluting the verified finding stream.

### Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | No verified finding |
| `1` | One or more verified findings |
| `2` | Scan error |
| `130` | Interrupted |

## Configuration

Repeated probe inputs and request context can be stored in `headerproof.yaml`:

```yaml
origins:
  - https://origin.example
headers:
  - X-Custom-Cache-Key
request_headers:
  X-Test-Context: authorized-lab
rate_limit: 5
timeout: 2.5
severity: high,medium
```

Supported configuration includes origins, custom probe headers, runtime request headers, concurrency, rate limiting, timeouts, severity filtering, and OOB settings. CLI values override matching configuration values.

Request-header values are used at runtime but are not copied into run metadata. See [Configuration](docs/CONFIGURATION.md) for the full behavior.

## Detector templates

HeaderProof separates the scanner engine from its distributable detector definitions.

Existing bounded primitives cover specialized workflows such as baseline, preflight, origin probes, query/header probes, cache state machines, CRLF probes, and OOB header probes. For simpler same-target checks, declarative HTTP templates can use safe `GET`, `HEAD`, or `OPTIONS` requests with matchers, extractors, finding metadata, and an independent evidence gate.

Template variables include:

```text
{{canary}}    {{hostname}}    {{url}}
```

Update the validated detector set with:

```bash
headerproof -update-templates
```

Detector updates are distributed separately through the [headerproof-templates](https://github.com/TayfurYldz/headerproof-templates) repository.

## Architecture

```text
Input
  │
  ▼
Orchestration ──► Transport ──► Detection
                                  │
                                  ▼
                           Evidence gating
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
               Findings                    Observations
                    │                           │
                    └──────────► Output ◄───────┘
```

The core modules deliberately keep responsibilities separate:

| Component | Responsibility |
| --- | --- |
| `cli.py` | Stable CLI surface and process exit contract |
| `input.py` | Target, file, and stdin normalization |
| `engine.py` | Bounded detector scheduling per URL |
| `transport.py` | HTTP exchanges and request pacing |
| `detectors.py` | Probe context and candidate signal generation |
| `templates.py` | Declarative request/matcher/extractor/gate validation |
| `evidence.py` | Technical evidence gating |
| `output.py` | Append-only evidence persistence and exports |

See [Architecture](docs/ARCHITECTURE.md) for the project-level design.

## Verification and testing

HeaderProof's test strategy treats false positives as a first-class failure mode.

The repository includes:

- Unit and integration tests.
- Ruff and mypy quality gates.
- Branch coverage gates for detector/evidence code.
- Real Varnish and nginx cache fixtures.
- Optional provider-backed Cloudflare and Fastly fixtures.
- A known-vulnerable DVWA measurement that explicitly documents a current CSRF false-negative boundary.
- Package build/install smoke tests in CI.

Controlled fixture measurements are published with their limitations rather than presented as internet-wide accuracy claims. See [Testing](docs/TESTING.md) and [Project Proof](docs/PROJECT_PROOF.md).

## CI and integrations

HeaderProof is designed to fit into existing security workflows:

- **GitHub Actions:** [headerproof-action](https://github.com/TayfurYldz/headerproof-action) preserves the scanner's exit semantics and supports SARIF export.
- **Detector updates:** [headerproof-templates](https://github.com/TayfurYldz/headerproof-templates) distributes validated detector definitions independently of the scanner binary.
- **Containers:** release automation publishes a GHCR image.
- **Release artifacts:** platform binaries, Python distributions, checksums, signatures, and provenance/attestation material are produced by the release workflow.

## Project scope

HeaderProof is not intended to replace a general-purpose vulnerability scanner or content fuzzer. It focuses on **header/cache security primitives where reproducible evidence and request relationships matter**.

| Tool | Primary role |
| --- | --- |
| **HeaderProof** | Evidence-gated verification of header/cache security behavior |
| **Nuclei** | Broad template-driven vulnerability scanning |
| **Corsy** | Focused CORS testing |
| **ffuf** | Web fuzzing and content discovery |

These tools can complement each other in an authorized testing workflow.

## Documentation

| Resource | Description |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | Components, data flow, and architectural invariants |
| [Configuration](docs/CONFIGURATION.md) | YAML configuration and precedence |
| [Testing](docs/TESTING.md) | Evidence states, fixtures, metrics, and known limitations |
| [Project Proof](docs/PROJECT_PROOF.md) | Evidence/publication rules and project proof |
| [Discovery](docs/DISCOVERY.md) | Discovery workflow documentation |
| [PyPI](docs/PYPI.md) | Package publishing/install information |
| [CI](docs/CI.md) | Continuous-integration details |
| [Roadmap](docs/ROADMAP.md) | Current project direction |
| [Changelog](CHANGELOG.md) | Release history |
| [Security](SECURITY.md) | Vulnerability reporting and authorized-testing policy |

A controlled terminal walkthrough is available in [`docs/headerproof-demo.cast`](docs/headerproof-demo.cast).

## Contributing

Contributions that **reduce false positives, improve evidence quality, strengthen detector behavior, improve tests, or make verified output easier to consume** are welcome.

Before opening a pull request:

1. Read [CONTRIBUTING.md](CONTRIBUTING.md).
2. Prefer an existing `good first issue` or `help wanted` issue, or discuss larger detector behavior first.
3. Keep changes focused and include tests for behavioral changes.
4. Keep controlled fixtures, known-vulnerable labs, and real-world findings clearly separated.
5. Never describe technical reproduction as victim impact without independent validation.

Local quality checks:

```bash
python3 -m compileall -q header_active_scan.py src/headerproof
python3 -m ruff check header_active_scan.py src/headerproof tests
python3 -m mypy
python3 -m pytest -q
python3 -m pytest -q --cov=headerproof.detectors --cov=headerproof.evidence --cov-branch --cov-fail-under=95
```

See [open issues](https://github.com/TayfurYldz/headerproof/issues) and [Discussions](https://github.com/TayfurYldz/headerproof/discussions) to get involved.

## Security and responsible use

HeaderProof performs active HTTP probes. Use it **only on systems you own or are explicitly authorized to test**.

Vulnerabilities in HeaderProof itself should be reported according to [SECURITY.md](SECURITY.md). Third-party vulnerabilities should **not** be disclosed in HeaderProof issues, pull requests, or Discussions.

## License

HeaderProof is released under the [MIT License](LICENSE).

---

<p align="center">
  <strong>HeaderProof</strong><br>
  Evidence first. Findings second.
</p>
