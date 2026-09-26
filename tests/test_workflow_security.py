from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def test_external_actions_are_pinned_to_full_commit_shas() -> None:
    seen = 0
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line.startswith("uses: "):
                continue
            ref = line.removeprefix("uses: ").split(" #", 1)[0].strip()
            if ref.startswith("./"):
                continue
            seen += 1
            assert "@" in ref, f"{path}: action has no ref: {ref}"
            revision = ref.rsplit("@", 1)[1]
            assert FULL_SHA.fullmatch(revision), f"{path}: action is not pinned to a full SHA: {ref}"
    assert seen > 0


def test_ci_package_job_does_not_need_repository_write_access() -> None:
    text = (WORKFLOWS / "ci.yml").read_text()
    package = text.split("\n  package:\n", 1)[1]
    assert "contents: read" in package
    assert "contents: write" not in package


def test_dependency_review_blocks_moderate_or_higher_new_vulnerabilities() -> None:
    text = (WORKFLOWS / "dependency-review.yml").read_text()
    assert "pull_request:" in text
    assert "contents: read" in text
    assert "fail-on-severity: moderate" in text


def test_dependabot_tracks_actions_and_python_dependencies() -> None:
    text = (ROOT / ".github" / "dependabot.yml").read_text()
    assert "package-ecosystem: github-actions" in text
    assert "package-ecosystem: pip" in text



def test_ci_release_tags_exercise_container_build_without_publishing() -> None:
    text = (WORKFLOWS / "release.yml").read_text()
    assert "startsWith(github.ref, 'refs/tags/ci-')" in text
    assert "push: $" + "{{ startsWith(github.ref, 'refs/tags/v') }}" in text
    assert "name: Verify cosign" in text
    assert "linux/amd64,linux/arm64" in text
    assert "|| 'linux/amd64'" in text
