# Discovery and contribution

HeaderProof keeps discovery metadata factual and keeps starter work small enough to review.

## Repository discovery

The GitHub repository uses focused security topics including `appsec`, `recon`, `red-team`, `web-security`, `security-scanner`, `vulnerability-scanner`, `dast`, `devsecops`, `sarif`, `security-testing`, `http-security`, `cors`, `csrf`, `header-injection`, and `cache-poisoning`.

The repository description states what HeaderProof scans and does not use speed, accuracy, or false-positive-rate adjectives without a named measurement corpus.

## Starter backlog

The project maintains 8–10 open `good first issue` tickets as the onboarding window. Starter tickets must:
- have one bounded outcome;
- include acceptance criteria or a concrete expected artifact;
- avoid requiring access to private targets or secrets;
- preserve the evidence-gate and false-positive-first design;
- remain open until a contributor actually completes the work.

The current starter backlog covers configuration validation, template documentation, SARIF validation, OOB documentation, cache regression coverage, evidence-schema consumption, release-binary smoke testing, and deterministic demo generation.

## Releases

Release notes describe shipped behavior and measured boundaries rather than roadmap promises. v1.4.0 and v1.4.1 are published GitHub releases, with matching repository release notes under `docs/releases/`.

## External lists

External distribution is tracked separately from scanner correctness:
- `infoslack/awesome-web-hacking`: HeaderProof entry merged in PR #146; PR #148 refreshes the old developer-alpha description to the current released feature set.
- `vavkamil/awesome-bugbounty-tools`: PR #134 proposes HeaderProof under Header Injection.
- `enaqx/awesome-pentest`: PR #719 proposes HeaderProof under Web Vulnerability Scanners.
- `qazbnm456/awesome-web-security`: PR #249 proposes HeaderProof through the repository's YAML-first Scanning data model; schema, generation, anchor, and automated format/reachability checks pass.

These submissions are intentionally small, category-specific, and factual. Lists that only aggregate other awesome repositories, stale forks, or weakly related catalogs are not targeted merely to increase PR count.
