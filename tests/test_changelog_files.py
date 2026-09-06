# -*- coding: utf-8 -*-
"""What a build's output contributes to changelogs/, and what it must not.

A leg produces four metadata files. Three belong in `changelogs/`; the fourth,
`hashes_<winpyver>.md`, describes one build's binaries rather than the release
and has never been kept there. Getting that wrong is quiet: the wrong file is
committed and nothing complains, so the selection is pinned here.

The `_History.md` companions are written from the checkout rather than shipped
by the build, because a history compares against the *previous* release, which
only the repository has.
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".github/scripts/changelog_files.py"

needs_script = pytest.mark.skipif(not SCRIPT.is_file(), reason="changelog_files.py is gone")


@pytest.fixture(scope="module")
def changelog_files():
    if not SCRIPT.is_file():
        pytest.skip("changelog_files.py is gone")
    spec = importlib.util.spec_from_file_location("changelog_files", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# what one leg of 2026-04 b1 actually uploaded, names verbatim
LEG_OUTPUT = [
    "WinPythonslim-64bit-3.15.0.5b1.md",
    "pylock.64-3_15_0_5slimb1.toml",
    "requir.64-3_15_0_5slimb1.txt",
    "hashes_3.15.0.5slimb1.md",
]


@needs_script
class TestParseChangelogName:
    @pytest.mark.parametrize("name,expected", [
        ("WinPythonslim-64bit-3.15.0.5b1.md", ("slim", 64, "3.15.0.5b1")),
        ("WinPythondotf-64bit-3.14.7.1b1.md", ("dotf", 64, "3.14.7.1b1")),
        ("WinPythondot-64bit-3.13.15.0.md", ("dot", 64, "3.13.15.0")),
        ("WinPython-64bit-3.9.8.0.md", ("", 64, "3.9.8.0")),  # the unflavored ones
        ("WinPythondot-32bit-3.9.0.0b1.md", ("dot", 32, "3.9.0.0b1")),
    ])
    def test_reads_flavor_architecture_and_version(self, changelog_files, name, expected):
        assert changelog_files.parse_changelog_name(name) == expected

    @pytest.mark.parametrize("name", [
        "WinPythonslim-64bit-3.15.0.5b1_History.md",  # the companion, not an index
        "hashes_3.15.0.5slimb1.md",
        "pylock.64-3_15_0_5slimb1.toml",
        "README.md",
        "WinPythonslim-64bit-.md",
    ])
    def test_rejects_everything_that_is_not_a_package_index(self, changelog_files, name):
        assert changelog_files.parse_changelog_name(name) is None


@needs_script
class TestSelection:
    def test_hashes_are_left_behind(self, changelog_files, tmp_path):
        """They describe one build's binaries; changelogs/ has never held them."""
        for name in LEG_OUTPUT:
            (tmp_path / name).write_text("", encoding="utf-8")
        chosen = sorted(p.name for p in changelog_files.files_to_file(tmp_path))
        assert chosen == [
            "WinPythonslim-64bit-3.15.0.5b1.md",
            "pylock.64-3_15_0_5slimb1.toml",
            "requir.64-3_15_0_5slimb1.txt",
        ]

    def test_directories_are_skipped(self, changelog_files, tmp_path):
        (tmp_path / "WinPythonslim-64bit-3.15.0.5b1.md").write_text("", encoding="utf-8")
        (tmp_path / "pylock.64-nested").mkdir()
        assert [p.name for p in changelog_files.files_to_file(tmp_path)] == [
            "WinPythonslim-64bit-3.15.0.5b1.md"
        ]


@needs_script
class TestEndToEnd:
    """Run the script the way the workflow runs it."""

    @pytest.fixture
    def cycle(self, tmp_path):
        """A metadata directory and a changelogs/ holding one earlier release."""
        source = tmp_path / "release_metadata"
        source.mkdir()
        changelogs = tmp_path / "changelogs"
        changelogs.mkdir()

        # a real package index makes a real diff; reuse two the repo already has
        previous = REPO / "changelogs" / "WinPythonslim-64bit-3.15.0.4.md"
        current = REPO / "changelogs" / "WinPythonslim-64bit-3.14.7.0.md"
        if not (previous.is_file() and current.is_file()):
            pytest.skip("the changelogs this test reads from are gone")
        shutil.copyfile(previous, changelogs / previous.name)
        shutil.copyfile(current, source / "WinPythonslim-64bit-3.15.0.5b1.md")
        (source / "pylock.64-3_15_0_5slimb1.toml").write_text("x", encoding="utf-8")
        (source / "requir.64-3_15_0_5slimb1.txt").write_text("x", encoding="utf-8")
        (source / "hashes_3.15.0.5slimb1.md").write_text("x", encoding="utf-8")
        return source, changelogs

    def test_files_the_three_and_writes_the_history(self, cycle):
        source, changelogs = cycle
        proc = subprocess.run(
            [sys.executable, ".github/scripts/changelog_files.py", str(source), str(changelogs)],
            cwd=REPO, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        landed = sorted(p.name for p in changelogs.iterdir())
        assert landed == [
            "WinPythonslim-64bit-3.15.0.4.md",           # was already there
            "WinPythonslim-64bit-3.15.0.5b1.md",         # filed
            "WinPythonslim-64bit-3.15.0.5b1_History.md",  # written
            "pylock.64-3_15_0_5slimb1.toml",
            "requir.64-3_15_0_5slimb1.txt",
        ]

    def test_the_history_names_the_release_it_compares_against(self, cycle):
        source, changelogs = cycle
        subprocess.run(
            [sys.executable, ".github/scripts/changelog_files.py", str(source), str(changelogs)],
            cwd=REPO, capture_output=True, text=True, check=True,
        )
        history = (changelogs / "WinPythonslim-64bit-3.15.0.5b1_History.md").read_text(
            encoding="utf-8"
        )
        assert "since version 3.15.0.4slim" in history
        assert "3.15.0.5b1slim" in history

    def test_an_empty_metadata_directory_is_an_error(self, tmp_path):
        """Silence here would commit nothing and call it a success."""
        source, changelogs = tmp_path / "src", tmp_path / "changelogs"
        source.mkdir()
        changelogs.mkdir()
        proc = subprocess.run(
            [sys.executable, ".github/scripts/changelog_files.py", str(source), str(changelogs)],
            cwd=REPO, capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "held no changelog" in proc.stdout + proc.stderr

    def test_a_missing_directory_is_an_error(self, tmp_path):
        proc = subprocess.run(
            [sys.executable, ".github/scripts/changelog_files.py",
             str(tmp_path / "nope"), str(tmp_path)],
            cwd=REPO, capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "no such directory" in proc.stdout + proc.stderr
