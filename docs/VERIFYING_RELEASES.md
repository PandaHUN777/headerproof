# Verifying releases

HeaderProof publishes multiple independent integrity signals. Verification proves
where an artifact came from; it does not prove that the artifact is vulnerability-free.

## Release files

Download the binary or Python distribution from the GitHub Release together with
`checksums.txt` and `checksums.txt.sigstore.json`.

Verify the downloaded binary against the published digest:

```bash
sha256sum -c checksums.txt --ignore-missing
```

Verify the signed checksum manifest with Cosign:

```bash
cosign verify-blob checksums.txt \
  --bundle checksums.txt.sigstore.json \
  --certificate-identity-regexp '^https://github.com/[Tt]ayfuryldz/headerproof/.github/workflows/release.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

## GitHub provenance

Current release workflows create GitHub artifact attestations for native binaries,
Python distributions, and the published container image.

Verify a downloaded artifact:

```bash
gh attestation verify ./headerproof-linux-amd64 \
  -R TayfurYldz/headerproof \
  --signer-workflow TayfurYldz/headerproof/.github/workflows/release.yml
```

Verify the container:

```bash
gh attestation verify oci://ghcr.io/tayfuryldz/headerproof:vX.Y.Z \
  -R TayfurYldz/headerproof \
  --signer-workflow TayfurYldz/headerproof/.github/workflows/release.yml
```

For older releases that predate GitHub release-artifact attestations, use the
signed checksum bundle. Do not treat a missing historical GitHub attestation as
a successful provenance check.
