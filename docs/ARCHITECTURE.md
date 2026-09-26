# Architecture

HeaderProof separates input, orchestration, transport, detection, evidence gating, and output.

- `cli.py` owns the stable command surface and process exit contract.
- `input.py` normalizes target, list, and stdin streams.
- `engine.py` schedules bounded detector work per URL.
- `transport.py` performs HTTP exchanges and enforces request pacing.
- `detectors.py` derives bounded probe context; template matchers/extractors decide which candidate signals exist.
- `templates.py` validates declarative request primitives, matchers, extractors, and evidence-gate definitions.
- `evidence.py` applies the template evidence gate before a candidate can become a finding.
- `output.py` persists append-only evidence and exports findings.

The primary invariant is that a console finding is never emitted before its detector-specific technical gate passes. Lower-confidence observations stay in the evidence bundle rather than being promoted to findings.

## Data flow

`input -> baseline/probes -> detector candidate -> evidence gate -> finding -> stdout/export`

Every attempted probe is recorded independently of whether a finding is produced. This keeps false-positive suppression auditable and makes missing proof distinguishable from a clean result.

## Published integrations

- Detector updates: `TayfurYldz/headerproof-templates`; `headerproof -update-templates` downloads its validated manifest without replacing the binary.
- CI wrapper: `TayfurYldz/headerproof-action`; the action preserves HeaderProof's `0/1/2` exit semantics and can export SARIF.
