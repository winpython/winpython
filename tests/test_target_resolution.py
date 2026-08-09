# -*- coding: utf-8 -*-
"""How wppm decides what a -t target is, and where its site-packages live.

This is where the venv bug lived: a venv keeps python.exe in Scripts\\ while
Lib\\site-packages stays at the root, so every layout question has two right
answers depending on the flavour of installation.
"""
from pathlib import Path

import pytest

from wppm import utils


class TestInstallRoot:
    def test_root_directory_is_its_own_root(self, winpython_layout):
        assert utils.get_install_root(str(winpython_layout)) == winpython_layout

    def test_executable_resolves_to_its_directory(self, winpython_layout):
        exe = winpython_layout / "python.exe"
        assert utils.get_install_root(str(exe)) == winpython_layout

    def test_scripts_directory_resolves_one_level_up(self, venv_layout):
        assert utils.get_install_root(str(venv_layout / "Scripts")) == venv_layout

    def test_scripts_match_is_case_insensitive(self, tmp_path):
        (tmp_path / "SCRIPTS").mkdir()
        assert utils.get_install_root(str(tmp_path / "SCRIPTS")) == tmp_path


class TestPythonExecutable:
    def test_finds_interpreter_at_root(self, winpython_layout):
        found = Path(utils.get_python_executable(str(winpython_layout)))
        assert found == winpython_layout / "python.exe"

    def test_finds_interpreter_under_scripts(self, venv_layout):
        found = Path(utils.get_python_executable(str(venv_layout)))
        assert found == venv_layout / "Scripts" / "python.exe"

    def test_scripts_target_finds_the_same_interpreter(self, venv_layout):
        """-t <venv>\\Scripts and -t <venv> must agree."""
        assert (utils.get_python_executable(str(venv_layout / "Scripts"))
                == utils.get_python_executable(str(venv_layout)))

    def test_root_interpreter_wins_over_one_in_scripts(self, winpython_layout):
        """A Scripts\\python.exe must never shadow the real interpreter."""
        (winpython_layout / "Scripts" / "python.exe").write_bytes(b"MZ")
        found = Path(utils.get_python_executable(str(winpython_layout)))
        assert found == winpython_layout / "python.exe"

    def test_returns_a_nonexistent_root_path_when_nothing_found(self, tmp_path):
        """Callers test the result with is_file(), so the fallback must be honest."""
        found = Path(utils.get_python_executable(str(tmp_path)))
        assert found == tmp_path / "python.exe"
        assert not found.is_file()


class TestSitePackages:
    def test_resolves_from_root_for_winpython(self, winpython_layout):
        found = Path(utils.get_site_packages_path(str(winpython_layout)))
        assert found == winpython_layout / "Lib" / "site-packages"

    def test_resolves_from_root_for_venv(self, venv_layout):
        found = Path(utils.get_site_packages_path(str(venv_layout)))
        assert found == venv_layout / "Lib" / "site-packages"

    def test_venv_scripts_does_not_look_inside_scripts(self, venv_layout):
        """The old code produced <venv>\\Scripts\\lib\\site-packages here."""
        found = Path(utils.get_site_packages_path(str(venv_layout / "Scripts")))
        assert found == venv_layout / "Lib" / "site-packages"
        assert found.is_dir()

    def test_resolves_from_an_executable_path(self, venv_layout):
        exe = venv_layout / "Scripts" / "python.exe"
        found = Path(utils.get_site_packages_path(str(exe)))
        assert found == venv_layout / "Lib" / "site-packages"


class TestIsPythonDistribution:
    def test_accepts_winpython_layout(self, winpython_layout):
        assert utils.is_python_distribution(str(winpython_layout))

    def test_accepts_venv_layout(self, venv_layout):
        assert utils.is_python_distribution(str(venv_layout))

    def test_accepts_venv_via_scripts_directory(self, venv_layout):
        assert utils.is_python_distribution(str(venv_layout / "Scripts"))

    def test_accepts_venv_without_site_packages_via_pyvenv_cfg(self, venv_layout):
        """pyvenv.cfg is the canonical marker even if Lib is missing."""
        import shutil
        shutil.rmtree(venv_layout / "Lib")
        assert utils.is_python_distribution(str(venv_layout))

    def test_rejects_empty_directory(self, tmp_path):
        assert not utils.is_python_distribution(str(tmp_path))

    def test_rejects_directory_with_no_interpreter(self, tmp_path):
        (tmp_path / "Lib" / "site-packages").mkdir(parents=True)
        assert not utils.is_python_distribution(str(tmp_path))

    def test_rejects_winpython_scripts_sibling(self, winpython_layout):
        """<WP>\\scripts holds env.bat, not an interpreter -- it is not a venv.

        It resolves to the distribution root, which has no python.exe, so it
        must still be refused rather than mistaken for a venv Scripts dir.
        """
        env_bat_dir = winpython_layout.parent / "scripts"
        assert (env_bat_dir / "env.bat").is_file()
        assert not utils.is_python_distribution(str(env_bat_dir))


class TestPythonQuery:
    def test_reports_a_readable_error_when_interpreter_produces_nothing(
        self, tmp_path, monkeypatch
    ):
        """Used to raise IndexError: list index out of range."""
        monkeypatch.setattr(utils, "exec_shell_cmd", lambda *a, **k: "")
        with pytest.raises(RuntimeError, match="not a usable Python interpreter"):
            utils.python_query("print(1)", str(tmp_path))

    def test_returns_first_line_of_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr(utils, "exec_shell_cmd", lambda *a, **k: "3.14\nnoise\n")
        assert utils.python_query("print(1)", str(tmp_path)) == "3.14"
