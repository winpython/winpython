# -*- coding: utf-8 -*-
"""End-to-end: run the wppm CLI against a real venv.

These are the commands that returned "OSError: Invalid Python distribution"
for any venv before the target-resolution fix.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import windows_only

REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = windows_only


def wppm(*args, expect_ok=True):
    """Run `python -m wppm ...` from the repo, not from an installed copy."""
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "wppm", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
        encoding="utf-8", errors="replace",
    )
    if expect_ok:
        assert proc.returncode == 0, f"exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    return proc


class TestListing:
    def test_lists_packages_of_a_venv(self, real_venv):
        out = wppm("-t", str(real_venv), "-ls").stdout
        assert "pip" in out

    def test_scripts_target_gives_the_same_listing(self, real_venv):
        """-t <venv>\\Scripts used to print nothing at all."""
        root = wppm("-t", str(real_venv), "-ls").stdout
        scripts = wppm("-t", str(real_venv / "Scripts"), "-ls").stdout
        assert scripts.strip() == root.strip()
        assert "pip" in scripts

    def test_json_listing_is_valid_json(self, real_venv):
        out = wppm("-t", str(real_venv), "-ls", "pip", "-j").stdout
        assert any(row["package"] == "pip" for row in json.loads(out))

    def test_filters_by_expression(self, real_venv):
        out = wppm("-t", str(real_venv), "-ls", "^pip$", "-j").stdout
        assert [r["package"] for r in json.loads(out)] == ["pip"]

    def test_does_not_list_the_running_interpreters_packages(self, real_venv):
        """A -t listing must describe the target, not whatever runs wppm."""
        names = {r["package"] for r in json.loads(
            wppm("-t", str(real_venv), "-ls", "-j").stdout)}
        assert "pytest" not in names


class TestTrees:
    def test_downward_tree(self, real_venv):
        assert "pip==" in wppm("-t", str(real_venv), "-p", "pip", "-l1").stdout

    def test_upward_tree(self, real_venv):
        assert "pip==" in wppm("-t", str(real_venv), "-r", "pip", "-l1").stdout

    def test_tree_json_parses(self, real_venv):
        out = wppm("-t", str(real_venv), "-p", "pip", "-l1", "-j").stdout
        assert json.loads(out)


class TestMarkdown:
    def test_generates_a_package_index(self, real_venv):
        out = wppm("-t", str(real_venv), "-md").stdout
        assert "### Python packages" in out
        assert "pip" in out

    def test_reports_plain_python_not_winpython(self, real_venv):
        """WINPYVER2 is unset here, so it must not claim to be WinPython."""
        assert "## Python" in wppm("-t", str(real_venv), "-md").stdout

    def test_tools_section_reports_the_target_python_version(self, real_venv):
        """Sanity check only: this venv comes from the running interpreter, so it
        cannot tell target from runner -- test_distribution.py does that.
        """
        data = json.loads(wppm("-t", str(real_venv), "-md", "-j").stdout)
        tools = {t["name"]: t["version"] for t in data["tools"]}
        expected = subprocess.run(
            [str(real_venv / "Scripts" / "python.exe"), "-c",
             "import platform;print(platform.python_version())"],
            capture_output=True, text=True,
        ).stdout.strip()
        assert tools["Python"].startswith(expected)

    def test_json_manifest_has_the_expected_shape(self, real_venv):
        data = json.loads(wppm("-t", str(real_venv), "-md", "-j").stdout)
        assert set(data) >= {"distribution", "tools", "packages", "wheelhouse"}
        assert set(data["distribution"]) >= {"name", "version", "python_version"}


class TestBadTarget:
    def test_rejects_a_directory_that_is_not_a_python(self, tmp_path):
        proc = wppm("-t", str(tmp_path), "-md", expect_ok=False)
        assert proc.returncode != 0
        assert "Invalid Python distribution" in proc.stdout + proc.stderr


class TestHelp:
    def test_help_mentions_the_version(self):
        from wppm import __version__
        assert __version__ in wppm("-h").stdout
