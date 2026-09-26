# PyPI publishing

PyPI is a secondary distribution channel. HeaderProof publishes with GitHub OIDC Trusted Publishing; no long-lived PyPI API token belongs in repository secrets.

## One-time PyPI account setup

The `headerproof` project does not exist on PyPI yet. Create a **pending GitHub publisher** in the PyPI account Publishing settings with exactly:

- PyPI project name: `headerproof`
- GitHub owner: `TayfurYldz`
- Repository: `headerproof`
- Workflow: `publish-pypi.yml`
- Environment: `pypi`

The pending publisher creates the project on the first successful upload.

## Publishing

Future GitHub Releases automatically trigger `Publish PyPI`. To publish an existing release after the one-time publisher setup, manually run the workflow and supply its existing tag, for example `v1.5.0`.

The workflow checks out that exact tag, builds wheel/sdist in a job without OIDC permission, verifies wheel metadata matches the tag version, transfers only the built distributions as an artifact, and grants `id-token: write` only to the final publish job.

Do not add a PyPI password or API token as a GitHub secret.
