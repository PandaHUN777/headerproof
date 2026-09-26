# Evidence schema compatibility

Evidence schemas are versioned independently from the HeaderProof application version.

- The current schema version is defined by `SCHEMA_VERSION` in `src/headerproof/constants.py`.
- Published schema files are immutable. A breaking record change requires a new `evidence-vX.Y.schema.json` file instead of editing an older schema.
- `manifest.json` records the current evidence version and SHA-256 of every published schema; regression tests fail if a published schema is edited in place or omitted from the manifest.
- Readers should select a schema from each record's `schema_version` field.
- New optional fields may be introduced only when they remain valid under the published schema; otherwise the schema version is incremented.
- Release CI validates emitted JSONL records against the current published schema.

`evidence-v1.2.schema.json` is the first schema covered by this compatibility policy. Its locked digest matches the schema published with both HeaderProof v1.4.0 and v1.4.1.
