# Evidence schema compatibility

Evidence schemas are versioned independently from the HeaderProof application version.

- The current schema version is defined by `SCHEMA_VERSION` in `src/headerproof/constants.py`.
- Published schema files are immutable. A breaking record change requires a new `evidence-vX.Y.schema.json` file instead of editing an older schema.
- Readers should select a schema from each record's `schema_version` field.
- New optional fields may be introduced only when they remain valid under the published schema; otherwise the schema version is incremented.
- Release CI validates emitted JSONL records against the current published schema.

`evidence-v1.2.schema.json` is the first schema covered by this compatibility policy.
