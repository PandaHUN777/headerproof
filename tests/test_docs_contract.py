from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DEMO = ROOT / "docs" / "headerproof-demo.cast"
PROOF = ROOT / "docs" / "PROJECT_PROOF.md"
DISCOVERY = ROOT / "docs" / "DISCOVERY.md"
MAINTAINERS = ROOT / "docs" / "MAINTAINERS.md"
SUPPORT = ROOT / "SUPPORT.md"
SECURITY = ROOT / "SECURITY.md"
CODE_OF_CONDUCT = ROOT / "CODE_OF_CONDUCT.md"
VERIFYING_RELEASES = ROOT / "docs" / "VERIFYING_RELEASES.md"
RELEASING = ROOT / "docs" / "RELEASING.md"
DOC_INDEX = ROOT / "docs" / "README.md"


def test_readme_stays_short_and_keeps_factual_tool_roles() -> None:
    text = README.read_text()
    assert len(text.splitlines()) <= 40
    for row in (
        "| HeaderProof | Header/cache proof-gated verification |",
        "| Nuclei | General template-driven scanning |",
        "| Corsy | CORS-focused testing |",
        "| ffuf | Web fuzzing and content discovery |",
    ):
        assert row in text


def test_terminal_demo_is_valid_local_asciinema_contract() -> None:
    lines = DEMO.read_text().splitlines()
    assert len(lines) >= 3

    header = json.loads(lines[0])
    assert header["version"] == 2
    events = [json.loads(line) for line in lines[1:]]
    assert all(len(event) == 3 and event[1] in {"i", "o"} for event in events)

    transcript = "".join(event[2] for event in events if event[1] == "o")
    assert "headerproof http://127.0.0.1:" in transcript
    assert "example.com" not in transcript
    finding_lines = [
        line
        for line in transcript.splitlines()
        if re.match(r"^\[[^]]+\] \[(?:info|low|medium|high|critical)\] \[[^]]+\] https?://", line)
    ]
    assert finding_lines
    assert "[response_splitting_crlf_candidate] [high] [reproduced]" in finding_lines[0]


def test_project_proof_does_not_mislabel_controlled_demo_as_real_finding() -> None:
    text = PROOF.read_text()
    assert "controlled localhost fixture" in text
    assert "not presented as a real bug-bounty finding" in text
    assert "explicitly permitted program" in text
    assert "Do not convert a controlled fixture" in text


def test_discovery_contract_keeps_contribution_and_external_scope_explicit() -> None:
    text = DISCOVERY.read_text()
    assert "small curated contributor queue rather than a numeric issue quota" in text
    assert "`good first issue`" in text
    assert "`help wanted`" in text
    assert "avoid requiring access to private targets or secrets" in text
    assert "Release notes describe shipped behavior" in text
    assert "vavkamil/awesome-bugbounty-tools" in text
    assert "enaqx/awesome-pentest" in text
    assert "qazbnm456/awesome-web-security" in text
    assert "not targeted merely to increase PR count" in text


def test_community_contract_routes_work_and_security_to_the_right_channels() -> None:
    maintainers = MAINTAINERS.read_text()
    support = SUPPORT.read_text()
    security = SECURITY.read_text()
    conduct = CODE_OF_CONDUCT.read_text()

    assert "`good first issue` means the task is bounded" in maintainers
    assert "`help wanted` means the task is accepted" in maintainers
    assert "A Discussion becomes an issue only when" in maintainers
    assert "Issues are for reproducible defects and accepted, scoped work" in support
    assert "private vulnerability reporting" in security
    assert "third-party systems" in security
    assert "Critique code, evidence, and design decisions rather than people" in conduct


def test_release_verification_and_maintainer_release_contract_are_documented() -> None:
    verifying = VERIFYING_RELEASES.read_text()
    releasing = RELEASING.read_text()
    readme = README.read_text()

    assert "gh attestation verify" in verifying
    assert "cosign verify-blob" in verifying
    assert "--signer-workflow tayfuryldz/headerproof/.github/workflows/release.yml" in verifying
    assert "--signer-workflow TayfurYldz/" not in verifying
    assert "gh release verify vX.Y.Z" in verifying
    assert "Current release workflows also create build provenance attestations" in verifying
    assert "Required CI checks on the release commit must be green" in releasing
    assert "GitHub marks the release immutable" in releasing
    assert "issue a patch release for corrections" in releasing
    assert "[Documentation index](docs/README.md)" in readme

    index = DOC_INDEX.read_text()
    for expected in (
        "Configuration",
        "CI integration",
        "Verifying releases",
        "Contributing",
        "Maintainer policy",
        "Release process",
        "Security policy",
    ):
        assert expected in index
