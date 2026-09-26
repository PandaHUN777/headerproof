# Architecture

HeaderProof separates input, orchestration, transport, detection, evidence gating, and output.

- `cli.py` owns the stable command surface and process exit contract.
- `input.py` normalizes target, list, and stdin streams.
- `engine.py` schedules bounded detector work per URL.
- `transport.py` performs HTTP exchanges and enforces request pacing.
- `detectors.py` evaluates technical behavior and emits candidate signals.
- `evidence.py` decides whether a candidate satisfies its proof gate.
- `output.py` persists append-only evidence and exports findings.

The primary invariant is that a console finding is never emitted before its detector-specific technical gate passes. Lower-confidence observations stay in the evidence bundle rather than being promoted to findings.

## Data flow

`input -> baseline/probes -> detector candidate -> evidence gate -> finding -> stdout/export`

Every attempted probe is recorded independently of whether a finding is produced. This keeps false-positive suppression auditable and makes missing proof distinguishable from a clean result.
