# -*- coding: utf-8 -*-
"""Distribution and the -md package index.

The CLI tests cannot catch "-md described the wrong interpreter", because a
venv made from the running Python reports the same version either way. These
check which path the code actually asks about.
"""
from pathlib import Path

import pytest

from wppm import utils, wppm

from conftest import write_dist


@pytest.fixture
def target(tmp_path, monkeypatch):
    """A synthetic distribution, with the spawning probes stubbed out."""
    root = tmp_path / "WPy64-1234" / "python"
    site = root / "Lib" / "site-packages"
    site.mkdir(parents=True)
    (root / "python.exe").write_bytes(b"MZ")
    write_dist(site, "somepkg", "1.2.3", summary="A package")
    monkeypatch.setattr(utils, "get_python_infos", lambda path: ("9.9", 64))
    return root


@pytest.fixture
def tools_probe(monkeypatch):
    """Record the path -md asks get_installed_tools about."""
    seen = []

    def fake(path=None):
        seen.append(path)
        return [("Python", "http://www.python.org/", "9.9.9", "stub")]

    monkeypatch.setattr(utils, "get_installed_tools", fake)
    return seen


class TestPackageIndexTarget:
    def test_tools_are_read_from_the_target_not_the_running_interpreter(
        self, target, tools_probe
    ):
        """Regression: -md used to describe whatever interpreter ran wppm."""
        wppm.Distribution(str(target)).get_package_index_data()
        assert len(tools_probe) == 1
        asked = Path(tools_probe[0])
        assert target in asked.parents or asked == target / "python.exe"

    def test_explicit_directory_argument_still_wins(self, target, tools_probe, tmp_path):
        other = tmp_path / "other"
        other.mkdir()
        (other / "python.exe").write_bytes(b"MZ")
        wppm.Distribution(str(target)).get_package_index_data(
            python_executable_directory=str(other)
        )
        assert Path(tools_probe[0]) == other / "python.exe"

    def test_packages_come_from_the_target(self, target, tools_probe):
        data = wppm.Distribution(str(target)).get_package_index_data()
        assert [p["name"] for p in data["packages"]] == ["somepkg"]

    def test_identity_is_plain_python_without_winpyver2(
        self, target, tools_probe, monkeypatch
    ):
        monkeypatch.delenv("WINPYVER2", raising=False)
        data = wppm.Distribution(str(target)).get_package_index_data()
        assert data["distribution"]["name"] == "Python"

    def test_identity_is_winpython_when_told_so(self, target, tools_probe):
        data = wppm.Distribution(str(target)).get_package_index_data(
            winpyver2="3.14.7.0", flavor="slim", release_level="b3"
        )
        assert data["distribution"]["name"] == "WinPython"
        assert data["distribution"]["version"] == "3.14.7.0slim"

    def test_explicit_arguments_beat_the_environment(
        self, target, tools_probe, monkeypatch
    ):
        """The build passes these as env vars today; arguments must take priority."""
        monkeypatch.setenv("WINPYVER2", "0.0.0.0")
        monkeypatch.setenv("WINPYFLAVOR", "wrong")
        data = wppm.Distribution(str(target)).get_package_index_data(
            winpyver2="3.14.7.0", flavor="slim"
        )
        assert data["distribution"]["version"] == "3.14.7.0slim"


class TestVersionProbesDoNotCrash:
    """Every version probe used to end in an unguarded splitlines()[0]."""

    def test_first_line_falls_back_when_output_is_empty(self):
        assert utils.first_line("") == "?"
        assert utils.first_line("\n  \n") == "?"

    def test_first_line_skips_blank_leading_lines(self):
        assert utils.first_line("\n\n3.14.2\nrest") == "3.14.2"

    def test_installed_tools_survives_a_silent_probe(self, tmp_path, monkeypatch):
        """A tool that prints nothing must not take the whole -md down."""
        root = tmp_path / "python"
        root.mkdir()
        (root / "python.exe").write_bytes(b"MZ")
        monkeypatch.setattr(utils, "exec_shell_cmd", lambda *a, **k: "")
        tools = utils.get_installed_tools(str(root))
        assert [t[0] for t in tools] == ["Python"]
        assert tools[0][2] == "?"
