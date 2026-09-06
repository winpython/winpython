# -*- coding: utf-8 -*-
"""Which changelog a new one gets compared against.

`write_changelog` asks `find_previous_version` what the previous release was,
and the answer comes from the file names in `changelogs/` alone. That made the
naming of those files load-bearing: the pattern used to be digits and dots, so
a version carrying a release level -- 3.14.7.1b1 -- matched nothing and the
comparison skipped straight past it. PEP 440 orders those versions correctly
already (3.14.7.0 < 3.14.7.1b1 < 3.14.7.1); only the file name pattern did not.

The layouts here are synthetic: the functions care about names, not contents,
so an empty file under the right name exercises the real code.
"""
from pathlib import Path

import pytest

from wppm.diff import changelog_versions, copy_changelogs, find_previous_version


def changelogs(searchdir: Path, *names: str) -> Path:
    """A changelogs directory holding exactly these files."""
    searchdir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (searchdir / name).write_text("", encoding="utf-8")
    return searchdir


class TestFindPreviousVersion:
    def test_picks_the_nearest_earlier_version(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.13.15.0.md",
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.1.md",
        )
        assert find_previous_version("3.14.7.1", searchdir, "dot") == "3.14.7.0"

    def test_a_release_level_is_visible_and_ordered(self, tmp_path):
        """The b1 sits between .0 and .1, so it is what .1 compares against.

        This is the case the old digits-and-dots pattern dropped: it would
        have answered 3.14.7.0 and reported a beta's worth of changes twice.
        """
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.1b1.md",
        )
        assert find_previous_version("3.14.7.1", searchdir, "dot") == "3.14.7.1b1"

    def test_a_release_level_compares_against_the_release_before_it(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.1b1.md",
        )
        assert find_previous_version("3.14.7.1b1", searchdir, "dot") == "3.14.7.0"

    @pytest.mark.parametrize("level", ["b1", "b2", "rc1", "a1", "post1"])
    def test_every_level_winpython_has_used_parses(self, tmp_path, level):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            f"WinPythondot-64bit-3.14.7.1{level}.md",
        )
        assert find_previous_version("3.14.8.0", searchdir, "dot") == f"3.14.7.1{level}"

    def test_history_companions_are_never_the_answer(self, tmp_path):
        """`_History.md` sits beside every changelog and is not one."""
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.0_History.md",
        )
        assert find_previous_version("3.14.7.1", searchdir, "dot") == "3.14.7.0"

    def test_unrelated_files_are_ignored(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "pylock.64-3_14_7_0dot.toml",
            "requir.64-3_14_7_0dot.txt",
            "README.md",
        )
        assert find_previous_version("3.14.7.1", searchdir, "dot") == "3.14.7.0"

    def test_the_old_txt_changelogs_still_count(self, tmp_path):
        searchdir = changelogs(tmp_path, "WinPython-64bit-2.7.10.1.txt")
        assert find_previous_version("2.7.10.2", searchdir, "") == "2.7.10.1"

    def test_nothing_earlier_returns_the_target_itself(self, tmp_path):
        """The documented fallback: comparing a version against itself is empty."""
        searchdir = changelogs(tmp_path, "WinPythondot-64bit-3.14.7.1.md")
        assert find_previous_version("3.14.7.1", searchdir, "dot") == "3.14.7.1"

    def test_flavors_do_not_see_each_other(self, tmp_path):
        """dot and slim ship different package sets; a cross-flavor diff is noise."""
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythonslim-64bit-3.14.7.1.md",
        )
        assert find_previous_version("3.14.7.2", searchdir, "dot") == "3.14.7.0"
        assert find_previous_version("3.14.7.2", searchdir, "slim") == "3.14.7.1"

    def test_a_flavor_is_not_a_prefix_of_another(self, tmp_path):
        """dot must not match dotf: the free-threaded build is a separate line."""
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondotf-64bit-3.14.7.1.md",
        )
        assert find_previous_version("3.14.7.2", searchdir, "dot") == "3.14.7.0"
        assert find_previous_version("3.14.7.2", searchdir, "dotf") == "3.14.7.1"

    def test_the_unflavored_name_does_not_match_flavored_files(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPython-64bit-3.9.8.0.md",
            "WinPythondot-64bit-3.14.7.0.md",
        )
        assert find_previous_version("3.15.0.0", searchdir, "") == "3.9.8.0"

    def test_architecture_separates_the_lines(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-32bit-3.9.0.0.md",
            "WinPythondot-64bit-3.8.0.0.md",
        )
        assert find_previous_version("3.14.0.0", searchdir, "dot", 64) == "3.8.0.0"
        assert find_previous_version("3.14.0.0", searchdir, "dot", 32) == "3.9.0.0"


class TestChangelogVersions:
    def test_reports_the_file_each_version_came_from(self, tmp_path):
        searchdir = changelogs(
            tmp_path,
            "WinPythondot-64bit-3.14.7.1b1.md",
            "WinPythondot-64bit-3.14.7.0_History.md",
        )
        found = changelog_versions(searchdir, "dot")
        assert [(raw, name) for _, raw, name in found] == [
            ("3.14.7.1b1", "WinPythondot-64bit-3.14.7.1b1.md")
        ]


class TestCopyChangelogs:
    @pytest.fixture
    def dest(self, tmp_path):
        target = tmp_path / "dest"
        target.mkdir()
        return target

    def test_takes_the_whole_major_minor_including_levels(self, tmp_path, dest):
        src = changelogs(
            tmp_path / "src",
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.1b1.md",
            "WinPythondot-64bit-3.13.15.0.md",
        )
        copy_changelogs("3.14.7.1", src, "dot", 64, dest)
        assert sorted(p.name for p in dest.iterdir()) == [
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.1b1.md",
        ]

    def test_a_minor_is_not_a_string_prefix(self, tmp_path, dest):
        """Selecting on the parsed version stops 3.1 from dragging in 3.15."""
        src = changelogs(
            tmp_path / "src",
            "WinPythondot-64bit-3.1.0.0.md",
            "WinPythondot-64bit-3.15.0.5.md",
        )
        copy_changelogs("3.1.0.0", src, "dot", 64, dest)
        assert [p.name for p in dest.iterdir()] == ["WinPythondot-64bit-3.1.0.0.md"]

    def test_history_companions_are_not_copied(self, tmp_path, dest):
        src = changelogs(
            tmp_path / "src",
            "WinPythondot-64bit-3.14.7.0.md",
            "WinPythondot-64bit-3.14.7.0_History.md",
        )
        copy_changelogs("3.14.7.0", src, "dot", 64, dest)
        assert [p.name for p in dest.iterdir()] == ["WinPythondot-64bit-3.14.7.0.md"]
