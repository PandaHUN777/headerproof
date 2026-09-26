# Releasing HeaderProof

HeaderProof uses Semantic Versioning for the scanner package. Evidence-schema
versions are independent compatibility contracts and do not automatically track
the package version.

## Before tagging

- Release changes must already be on `main`.
- Required CI checks on the release commit must be green.
- `CHANGELOG.md` must describe the user-visible change.
- `docs/releases/vX.Y.Z.md` must exist and follow `docs/releases/TEMPLATE.md`.
- Package and runtime versions must match the intended tag.
- Accepted external contributions shipping for the first time must be credited.
- No controlled-fixture result may be rewritten as an internet-wide accuracy claim.

Run locally:

```bash
python -m compileall -q header_active_scan.py src/headerproof
python -m ruff check header_active_scan.py src/headerproof tests
python -m mypy
python -m pytest -q
python -m build
```

## Tag and publish

Create the annotated release tag only from the verified `main` commit. The
release workflow builds native binaries and Python distributions from that tag,
creates checksums, signs the checksum manifest with Sigstore/Cosign, creates
GitHub provenance attestations, publishes the GitHub Release, and publishes and
signs the multi-architecture GHCR image.

PyPI publishing is a separate Trusted Publishing workflow and remains gated by
the PyPI publisher configuration documented in `docs/PYPI.md`.

## After publishing

- Download the public release artifacts and verify checksums.
- Verify the Cosign checksum bundle against the release workflow identity.
- Verify GitHub provenance with `gh attestation verify`.
- Run `--version` and `--help` from the downloaded native binary.
- Confirm the GHCR image signature and provenance.
- Confirm release notes credit every accepted external contribution included.
- Keep the release immutable; issue a patch release instead of replacing assets.

See `docs/VERIFYING_RELEASES.md` for consumer verification commands.
