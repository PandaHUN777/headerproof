# Roadmap

HeaderProof follows three rules: reduce false positives, keep normal usage memorable, and keep output pipe-friendly.

## Completed foundation

- Sade single-line verified finding output.
- Positional target, `-l`, and stdin input.
- Stable concurrency, per-host rate limit, severity filtering, JSONL, verbose notes, and extension-based exports.
- stdout/stderr separation and CI-oriented `0/1/2` exit codes.
- XDG user-state evidence storage.

## Next dependency order

1. Declarative detector templates and template updates.
2. Single-binary release pipeline in parallel with templates.
3. OOB callback verification and real cache-server fixtures.
4. SARIF and CI/action integration.
5. Precision/recall publication and contributor template guide.
6. Release automation, topics, and good-first-issue backlog.

A feature is accepted only when it improves proof quality, reduces false positives, or makes verified evidence easier to consume.
