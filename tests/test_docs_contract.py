from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DEMO = ROOT / "docs" / "headerproof-demo.cast"
PROOF = ROOT / "docs" / "PROJECT_PROOF.md"
DISCOVERY = ROOT / "docs" / "DISCOVERY.md"


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
    assert "8–10 open `good first issue`" in text
    assert "avoid requiring access to private targets or secrets" in text
    assert "Release notes describe shipped behavior" in text
    assert "require explicit authorization for those external repositories" in text
