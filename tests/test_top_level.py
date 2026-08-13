# -*- coding: utf-8 -*-
"""--top-level: keep only the entries no other entry already pulls in.

Same synthetic site-packages trick as test_piptree.py -- the point is the
graph, not the packages.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from wppm import piptree, utils, wppm as wppm_module

from conftest import write_dist, windows_only

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def graph(tmp_path):
    """app -> lib -> helper, app[fancy] -> fancylib, and a standalone orphan."""
    root = tmp_path / "dist"
    site = root / "Lib" / "site-packages"
    site.mkdir(parents=True)
    (root / "python.exe").write_bytes(b"MZ")
    write_dist(site, "app", "1.0", requires=["lib>=1.0", 'fancylib; extra == "fancy"'],
               extras=["fancy"])
    write_dist(site, "lib", "1.5", requires=["helper"])
    write_dist(site, "helper", "0.3")
    write_dist(site, "fancylib", "2.0")
    write_dist(site, "orphan", "9.9")
    return root


@pytest.fixture
def pip(graph):
    return piptree.PipData(str(graph))


class TestSplitRequirement:
    @pytest.mark.parametrize("text, expected", [
        ("numpy", ("numpy", [])),
        ("numpy==2.0", ("numpy", [])),
        ("numpy >= 2.0", ("numpy", [])),
        ("Pillow", ("pillow", [])),
        ("mypy[mypyc]", ("mypy", ["mypyc"])),
        ("dask[array,dataframe]>=2.0", ("dask", ["array", "dataframe"])),
        ("scipy; python_version > '3.10'", ("scipy", [])),
    ])
    def test_parses(self, text, expected):
        assert piptree.PipData.split_requirement(text) == expected


class TestClosure:
    def test_follows_the_chain(self, pip):
        assert pip.dependency_closure("app") == {"lib", "helper"}

    def test_ignores_an_extra_nobody_asked_for(self, pip):
        assert "fancylib" not in pip.dependency_closure("app")

    def test_follows_an_extra_that_is_asked_for(self, pip):
        assert "fancylib" in pip.dependency_closure("app", "fancy")

    def test_leaf_reaches_nothing(self, pip):
        assert pip.dependency_closure("helper") == set()


class TestTopLevel:
    def test_installed_set_keeps_only_what_nothing_requires(self, pip):
        assert pip.top_level()["kept"] == ["app", "fancylib", "orphan"]

    def test_drops_an_entry_another_entry_pulls_in(self, pip):
        result = pip.top_level(["app", "lib", "orphan"])
        assert result["kept"] == ["app", "orphan"]
        assert result["dropped"] == {"lib": ["app"]}

    def test_names_every_puller_of_a_dropped_entry(self, pip):
        assert pip.top_level(["app", "lib", "helper"])["dropped"]["helper"] == ["app", "lib"]

    def test_keeps_an_entry_whose_puller_is_not_listed(self, pip):
        """Nothing listed pulls helper in, so it stays."""
        assert pip.top_level(["helper", "orphan"])["kept"] == ["helper", "orphan"]

    def test_an_extra_only_dependency_stays_unless_the_extra_is_asked_for(self, pip):
        assert "fancylib" in pip.top_level(["app", "fancylib"])["kept"]
        assert "fancylib" in pip.top_level(["app[fancy]", "fancylib"])["dropped"]

    def test_keeps_the_entry_as_written(self, pip):
        assert pip.top_level(["app[fancy]", "lib"])["kept"] == ["app[fancy]"]

    def test_reports_a_repeated_entry_once(self, pip):
        result = pip.top_level(["orphan", "orphan"])
        assert result["kept"] == ["orphan"]
        assert result["duplicates"] == ["orphan"]

    def test_a_repeat_keeps_the_fuller_spelling(self, pip):
        assert pip.top_level(["app", "app[fancy]"])["kept"] == ["app[fancy]"]

    def test_an_entry_the_target_lacks_is_kept_and_reported(self, pip):
        result = pip.top_level(["orphan", "nosuchpackage"])
        assert result["unknown"] == ["nosuchpackage"]
        assert "nosuchpackage" in result["kept"]

    def test_sorting_is_case_insensitive(self, pip):
        assert pip.top_level(["orphan", "App", "fancylib"])["kept"] == ["App", "fancylib", "orphan"]

    def test_empty_input_gives_empty_output(self, pip):
        assert pip.top_level([]) == {"kept": [], "dropped": {}, "duplicates": [], "unknown": []}


class TestMutualDependency:
    @pytest.fixture
    def cycle(self, tmp_path):
        root = tmp_path / "cyc"
        site = root / "Lib" / "site-packages"
        site.mkdir(parents=True)
        (root / "python.exe").write_bytes(b"MZ")
        write_dist(site, "aaa", "1.0", requires=["bbb"])
        write_dist(site, "bbb", "1.0", requires=["aaa"])
        write_dist(site, "ccc", "1.0", requires=["aaa"])
        return piptree.PipData(str(root))

    def test_a_mutual_pair_keeps_both(self, cycle):
        """Dropping either would take the other with it."""
        assert cycle.top_level(["aaa", "bbb"])["kept"] == ["aaa", "bbb"]

    def test_something_outside_the_cycle_still_drops_it(self, cycle):
        result = cycle.top_level(["aaa", "bbb", "ccc"])
        assert result["kept"] == ["ccc"]
        assert set(result["dropped"]) == {"aaa", "bbb"}


class TestRendering:
    def test_plain_output_is_the_list_and_nothing_else(self, pip):
        """Redirect it and what lands in the file is the file."""
        assert wppm_module.top_level_as_requirements(pip.top_level(["app", "lib"])) == ["app"]

    def test_verbose_comments_out_what_went_and_why(self, pip):
        lines = wppm_module.top_level_as_requirements(pip.top_level(["app", "lib"]), verbose=True)
        assert "app" in lines
        assert "#lib  # <- app" in lines

    def test_verbose_heads_the_list_with_source_and_time(self, pip):
        lines = wppm_module.top_level_as_requirements(
            pip.top_level(["app", "lib"]), source="req.txt", verbose=True)
        assert re.fullmatch(r"# req\.txt, sorted, \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", lines[0])

    def test_verbose_heads_the_list_with_the_same_counts_stderr_gives(self, pip):
        result = pip.top_level(["app", "lib", "orphan"])
        lines = wppm_module.top_level_as_requirements(result, verbose=True)
        assert lines[1:2] == wppm_module.top_level_summary(result)[:1]
        assert lines[1] == "# 3 entries -> 2 kept, 1 already pulled in"

    def test_source_notes_are_kept_even_plainly(self, pip):
        """They are the author's own lines, not our commentary."""
        lines = wppm_module.top_level_as_requirements(pip.top_level(["app"]), comments=["# a note"])
        assert "# a note" in lines


class TestSummary:
    def test_counts_what_happened(self, pip):
        notes = wppm_module.top_level_summary(pip.top_level(["app", "lib", "orphan"]))
        assert notes[0] == "# 3 entries -> 2 kept, 1 already pulled in"

    def test_every_note_is_a_comment(self, pip):
        """stdout and stderr may well end up in the same file."""
        notes = wppm_module.top_level_summary(pip.top_level(["orphan", "orphan", "nosuchpackage"]))
        assert len(notes) == 3
        assert all(note.startswith("# ") for note in notes)

    def test_reports_repeats(self, pip):
        notes = wppm_module.top_level_summary(pip.top_level(["orphan", "orphan"]))
        assert any("repeated" in note for note in notes)

    def test_reports_what_the_target_lacks(self, pip):
        notes = wppm_module.top_level_summary(pip.top_level(["orphan", "nosuchpackage"]))
        assert any("nosuchpackage" in note for note in notes)


class TestReadRequirements:
    def test_splits_entries_from_comments(self, tmp_path):
        path = tmp_path / "r.txt"
        path.write_text("# a note\n\nnumpy\n  pandas  \n#disabled\n", encoding="utf-8")
        assert utils.read_requirements(path) == (["numpy", "pandas"], ["# a note", "#disabled"])


@windows_only
class TestCli:
    def run(self, *args):
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "wppm", *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
            encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0, f"exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}"
        return proc

    def wppm(self, *args):
        return self.run(*args).stdout

    def test_top_level_of_a_target(self, graph):
        assert self.wppm("-t", str(graph), "--top-level").splitlines() == ["app", "fancylib", "orphan"]

    def test_the_short_flag_does_the_same(self, graph):
        assert self.wppm("-t", str(graph), "-tl") == self.wppm("-t", str(graph), "--top-level")

    def test_verbose_adds_the_reasoning(self, graph):
        assert "#lib  # <- app" in self.wppm("-t", str(graph), "--top-level", "-v").splitlines()

    def test_verbose_does_not_say_the_counts_twice(self, graph):
        """Under -v they head the list, so stderr keeps quiet."""
        proc = self.run("-t", str(graph), "--top-level", "-v")
        assert "entries ->" in proc.stdout
        assert "entries ->" not in proc.stderr

    def test_top_level_of_a_requirements_file(self, graph, tmp_path):
        req = tmp_path / "req.txt"
        req.write_text("# keep me\nlib\napp\n", encoding="utf-8")
        out = self.wppm("-t", str(graph), str(req), "--top-level").splitlines()
        assert "app" in out
        assert "#lib" not in out
        assert "# keep me" in out

    def test_the_counts_go_to_stderr_not_into_the_list(self, graph, tmp_path):
        req = tmp_path / "req.txt"
        req.write_text("lib\napp\n", encoding="utf-8")
        proc = self.run("-t", str(graph), str(req), "--top-level")
        assert proc.stdout.splitlines() == ["app"]
        assert "2 entries -> 1 kept" in proc.stderr

    def test_json_output_parses(self, graph):
        data = json.loads(self.wppm("-t", str(graph), "--top-level", "-j"))
        assert set(data) == {"kept", "dropped", "duplicates", "unknown"}
        assert data["kept"] == ["app", "fancylib", "orphan"]
