from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_contributor_credit_waits_for_accepted_work() -> None:
    text = (ROOT / "CONTRIBUTORS.md").read_text()
    assert "after an accepted contribution reaches" in text
    assert "Bots and automated dependency updates are not listed" in text


def test_release_template_has_contributor_and_verification_contract() -> None:
    text = (ROOT / "docs" / "releases" / "TEMPLATE.md").read_text()
    assert "## Contributors" in text
    assert "@handle" in text
    assert "PR #NN" in text
    assert "## Verification" in text


def test_generated_release_notes_exclude_automation_from_credit() -> None:
    text = (ROOT / ".github" / "release.yml").read_text()
    assert "- dependabot[bot]" in text
    assert "- github-actions[bot]" in text
    for title in ("Features", "Fixes", "Documentation", "Maintenance", "Other changes"):
        assert f"- title: {title}" in text


def test_maintainer_policy_preserves_external_authorship() -> None:
    text = (ROOT / "docs" / "MAINTAINERS.md").read_text()
    assert "keep their original commit author" in text
    assert "first accepted contribution reaches `main`" in text
    assert "Use `Co-authored-by` only for actual co-authorship" in text


def test_security_policy_separates_reporter_and_code_credit() -> None:
    text = (ROOT / "SECURITY.md").read_text()
    assert "latest published release line" in text
    assert "without a promised response SLA" in text
    assert "does not imply code-contributor credit" in text
