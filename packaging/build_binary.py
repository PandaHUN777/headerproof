from __future__ import annotations

import platform
import shutil
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist-bin"


def artifact_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    machine = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(machine, machine)
    suffix = ".exe" if system == "windows" else ""
    return f"headerproof-{system}-{machine}{suffix}"


def main() -> int:
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir(parents=True, exist_ok=True)
    args = [
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name",
        artifact_name(),
        "--distpath",
        str(DIST),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build" / "pyinstaller"),
        "--paths",
        str(ROOT / "src"),
        "--collect-data",
        "headerproof",
        str(ROOT / "header_active_scan.py"),
    ]
    PyInstaller.__main__.run(args)
    binary = DIST / artifact_name()
    if not binary.exists():
        raise SystemExit(f"missing binary: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
