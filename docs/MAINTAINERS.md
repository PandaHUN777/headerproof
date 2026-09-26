# Maintainer policy

HeaderProof optimizes for trustworthy evidence and low false-positive cost, not detector count.

## Intake

- Bugs need a minimal sanitized reproduction before they are considered actionable.
- New ideas start in Discussions unless an existing issue already defines the scope.
- A Discussion becomes an issue only when the expected behavior, acceptance criteria, safety boundary, and maintenance owner are clear.
- Security vulnerabilities in HeaderProof itself use private vulnerability reporting.

## Contributor work

- `good first issue` means the task is bounded, has clear acceptance criteria, and should not require an architecture decision.
- `help wanted` means the task is accepted and useful but may require deeper project context.
- Contributors should comment before starting an issue. A maintainer confirms the scope before substantial work begins.
- An assignment is coordination, not ownership forever. If progress stops, maintainers may reopen the task for others after checking in.
- Unsolicited large rewrites or new active scanning primitives may be declined even when technically correct; discuss them first.

## Review bar

A merge should leave the project easier to trust than before.

1. Behavior matches the issue or accepted Discussion scope.
2. New detection behavior has deterministic tests and preserves conservative proof gates.
3. Active requests remain bounded and safe by default.
4. User-facing behavior is documented when it changes.
5. CI is green and no unrelated cleanup is bundled into the change.
6. Security-sensitive evidence contains no live third-party secrets or exploit material.

Maintainers may ask for a PR to be split when independent changes can be reviewed and reverted separately.

## Integration

For an accepted external pull request, prefer a linear fast-forward integration of the exact reviewed contributor commits:

1. The contributor rebases or updates the pull-request branch onto the current `main`.
2. Required CI checks and maintainer review pass on that exact head.
3. Verify locally that `main` is an ancestor of the reviewed pull-request head.
4. Fast-forward that exact head to `main`; do not recreate the change as a maintainer-authored commit.
5. Confirm GitHub records the pull request as merged and the contributor commit is reachable from the default branch.

If the accepted change needs maintainer-only follow-up, keep that follow-up in a separate commit. Do not use branch-protection bypass as a substitute for review or green required checks.

## Labels

- `good first issue`: newcomer-sized and ready to implement.
- `help wanted`: accepted work where outside contribution is explicitly welcome.
- `bug`: reproducible defect in HeaderProof.
- `documentation`: documentation-only or documentation-led work.
- `tests`: test coverage, fixtures, or validation-only work.
- `community`: an external community contribution; it does not imply acceptance or merge readiness.
- `enhancement`: accepted improvement; it does not by itself mean the task is ready for implementation.
- `needs triage`: maintainer has not yet confirmed scope or priority.
- `dependencies`, `ci`, and `release`: dependency, workflow, and distribution maintenance.

Labels describe project state; they are not a promise that every proposed change will be merged.

## Attribution

External contributions keep their original commit author when integrated. Do not rewrite an accepted contributor's work as a maintainer-authored commit merely to simplify history.

- Add a person to `CONTRIBUTORS.md` after their first accepted contribution reaches `main`, not when a pull request is merely opened.
- Credit accepted external work in the first release that ships it using the contributor's GitHub handle and pull request number.
- Do not list Dependabot, GitHub Actions, or other automation as community contributors.
- Use `Co-authored-by` only for actual co-authorship; it is not a substitute for preserving the original author.
- When a contribution needs maintainer fixes before integration, keep the contributor's commit where practical and put maintainer follow-up in a separate commit so attribution and review history stay clear.

## Releases

Changes reach a release only after they are present on `main`, pass the project CI contract, and have release notes appropriate to their user impact. Release tags are not used as a substitute for merging maintained source into `main`.

Use `docs/releases/TEMPLATE.md` as the release-note contract. When external work ships, include a `Contributors` section with `@handle`, pull request number, and a short factual description. Omit the section when there are no external contributors rather than manufacturing credit. Automated release-note configuration lives in `.github/release.yml` as a drafting aid; curated release notes remain authoritative.
