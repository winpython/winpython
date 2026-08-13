# -*- coding: utf-8 -*-
"""--top-level: keep only the entries no other entry already pulls in.

Same synthetic site-packages trick as test_piptree.py -- the point is the
graph, not the packages.
"""
import json
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
    def test_dropped_entries_come_back_as_comments(self, pip):
        lines = wppm_module.top_level_as_requirements(pip.top_level(["app", "lib"]))
        assert "app" in lines
        assert "#lib" in lines

    def test_verbose_says_who_pulls_each_one_in(self, pip):
        lines = wppm_module.top_level_as_requirements(pip.top_level(["app", "lib"]), verbose=True)
        assert "#lib  # <- app" in lines

    def test_source_comments_are_preserved(self, pip):
        lines = wppm_module.top_level_as_requirements(pip.top_level(["app"]), comments=["# a note"])
        assert "# a note" in lines

    def test_header_counts_the_entries(self, pip):
        header = "\n".join(wppm_module.top_level_as_requirements(pip.top_level(["app", "lib", "orphan"]))[:2])
        assert "3 entries -> 2" in header


class TestReadRequirements:
    def test_splits_entries_from_comments(self, tmp_path):
        path = tmp_path / "r.txt"
        path.write_text("# a note\n\nnumpy\n  pandas  \n#disabled\n", encoding="utf-8")
        assert utils.read_requirements(path) == (["numpy", "pandas"], ["# a note", "#disabled"])


@windows_only
class TestCli:
    def wppm(self, *args):
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "wppm", *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
            encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0, f"exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}"
        return proc.stdout

    def test_top_level_of_a_target(self, graph):
        out = self.wppm("-t", str(graph), "--top-level")
        assert "app" in out.splitlines()
        assert "#lib" in out.splitlines()

    def test_top_level_of_a_requirements_file(self, graph, tmp_path):
        req = tmp_path / "req.txt"
        req.write_text("# keep me\nlib\napp\n", encoding="utf-8")
        out = self.wppm("-t", str(graph), str(req), "--top-level")
        assert "app" in out.splitlines()
        assert "#lib" in out.splitlines()
        assert "# keep me" in out.splitlines()

    def test_json_output_parses(self, graph):
        data = json.loads(self.wppm("-t", str(graph), "--top-level", "-j"))
        assert set(data) == {"kept", "dropped", "duplicates", "unknown"}
        assert data["kept"] == ["app", "fancylib", "orphan"]
