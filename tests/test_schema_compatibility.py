from __future__ import annotations

import hashlib
import json
from pathlib import Path

from headerproof.constants import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def _manifest() -> dict[str, object]:
    return json.loads((SCHEMA_DIR / "manifest.json").read_text())


def test_schema_manifest_tracks_current_runtime_version() -> None:
    manifest = _manifest()
    assert manifest["current"] == SCHEMA_VERSION
    schemas = manifest["schemas"]
    assert isinstance(schemas, dict)
    assert SCHEMA_VERSION in schemas


def test_published_schema_files_are_hash_locked() -> None:
    manifest = _manifest()
    schemas = manifest["schemas"]
    assert isinstance(schemas, dict)
    tracked_files: set[str] = set()
    for version, entry in schemas.items():
        assert isinstance(entry, dict)
        filename = entry["file"]
        expected_sha256 = entry["sha256"]
        assert isinstance(filename, str)
        assert isinstance(expected_sha256, str)

        path = SCHEMA_DIR / filename
        tracked_files.add(filename)
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256

        schema = json.loads(path.read_text())
        assert schema["$id"].endswith(f"/schemas/{filename}")
        assert f"v{version}" in schema["title"]

    published_files = {path.name for path in SCHEMA_DIR.glob("evidence-v*.schema.json")}
    assert published_files == tracked_files
