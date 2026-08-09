# -*- coding: utf-8 -*-
"""Shared fixtures.

Most tests build *synthetic* distribution layouts in tmp_path: wppm's target
resolution is pure path logic, so a directory tree with an empty `python.exe`
in it exercises the real code without needing a real interpreter. That keeps
the suite fast, offline and deterministic.

Only the end-to-end CLI tests need a real interpreter, and they use a plain
`python -m venv` (which bundles pip via ensurepip, so still no network).
"""
import subprocess
import sys
from pathlib import Path

import pytest

IS_WINDOWS = sys.platform == "win32"

windows_only = pytest.mark.skipif(
    not IS_WINDOWS, reason="wppm targets the Windows layout (python.exe / Scripts)"
)


def write_dist(site_packages: Path, name: str, version: str, requires=(),
               summary: str = "", extras=()) -> Path:
    """Write a minimal .dist-info so importlib.metadata can discover the package."""
    dist_info = site_packages / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    lines = ["Metadata-Version: 2.1", f"Name: {name}", f"Version: {version}"]
    if summary:
        lines.append(f"Summary: {summary}")
    lines += [f"Provides-Extra: {e}" for e in extras]
    lines += [f"Requires-Dist: {r}" for r in requires]
    (dist_info / "METADATA").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dist_info / "INSTALLER").write_text("pytest\n", encoding="utf-8")
    return dist_info


@pytest.fixture
def winpython_layout(tmp_path: Path) -> Path:
    """WinPython/plain install: python.exe at the root, Lib/site-packages beside it.

    Also creates the distribution-root `scripts/` sibling that holds env.bat --
    that directory is NOT a venv Scripts dir and must not be mistaken for one.
    """
    root = tmp_path / "WPy64-31470b3" / "python"
    (root / "Lib" / "site-packages").mkdir(parents=True)
    (root / "Scripts").mkdir()
    (root / "python.exe").write_bytes(b"MZ")
    distro_root = root.parent
    (distro_root / "scripts").mkdir()
    (distro_root / "scripts" / "env.bat").write_text("@echo off\n", encoding="utf-8")
    (distro_root / "wheelhouse").mkdir()
    return root


@pytest.fixture
def venv_layout(tmp_path: Path) -> Path:
    """venv: python.exe under Scripts/, Lib/site-packages at the root, pyvenv.cfg marker."""
    root = tmp_path / "myvenv"
    (root / "Scripts").mkdir(parents=True)
    (root / "Lib" / "site-packages").mkdir(parents=True)
    (root / "Scripts" / "python.exe").write_bytes(b"MZ")
    (root / "pyvenv.cfg").write_text(
        "home = C:\\Python\nversion = 3.14.6\n", encoding="utf-8"
    )
    return root


@pytest.fixture(scope="session")
def real_venv(tmp_path_factory) -> Path:
    """A genuine venv. ensurepip is bundled, so this needs no network."""
    if not IS_WINDOWS:
        pytest.skip("wppm targets the Windows layout")
    target = tmp_path_factory.mktemp("real") / "venv"
    proc = subprocess.run(
        [sys.executable, "-m", "venv", str(target)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        pytest.skip(f"could not create a venv: {proc.stderr.strip()[:200]}")
    return target
