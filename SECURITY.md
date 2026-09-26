# Security Policy

HeaderProof is intended for authorized security testing only.

## Supported versions

Security fixes target `main` and the latest published release line. Older release lines may receive a backport when the fix is low-risk, but they are not guaranteed ongoing security maintenance.

## Vulnerabilities in HeaderProof

If you find a vulnerability in HeaderProof itself, use GitHub's private vulnerability reporting for this repository. Do not open a public issue before coordinated disclosure.

Include the affected version or commit, impact, minimal reproduction, and any proposed mitigation. Remove third-party secrets and target data.

Reports are handled on a best-effort basis without a promised response SLA. After validation, the maintainer will coordinate remediation and disclosure before public details are posted. Security reporters can be credited in the advisory and release notes if they want attribution; reporting a vulnerability alone does not imply code-contributor credit in `CONTRIBUTORS.md`.

## Scanner bugs

For non-security defects in HeaderProof, use the public Bug report form with a deterministic, sanitized reproduction.

## Third-party findings

Do not use HeaderProof issues, pull requests, or Discussions to disclose vulnerabilities in third-party systems. Report those findings through the target's authorized disclosure process.

## Testing boundaries

Only scan assets where you have explicit permission. HeaderProof uses bounded, low-impact requests by design, but operators remain responsible for scope, rate, and program policy.
