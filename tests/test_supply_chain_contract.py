from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_container_base_images_are_digest_pinned() -> None:
    text = (ROOT / "Dockerfile").read_text()
    from_lines = [line for line in text.splitlines() if line.startswith("FROM ")]
    assert len(from_lines) == 2
    for line in from_lines:
        image = line.split()[1]
        assert "@sha256:" in image
        digest = image.rsplit("@sha256:", 1)[1]
        assert len(digest) == 64
        int(digest, 16)


def test_container_build_does_not_self_upgrade_pip() -> None:
    text = (ROOT / "Dockerfile").read_text()
    assert "pip install --no-cache-dir --upgrade pip" not in text
    assert '"pyinstaller==6.22.3"' in text
